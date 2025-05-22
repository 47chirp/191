import os
import json
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

def load_hypernodes(folder="March7", filename="hyperNode.json"):
    """
    Loads hypernode configurations from the specified JSON file.
    Expects each hypernode to have a "board" key (a 2D list of strings).
    Always computes pieces from the board so that each piece has both "token" and "cells".
    """
    file_path = os.path.join(folder, filename)
    if not os.path.exists(file_path):
        print("Error: Hyper-node file not found!")
        return None
    with open(file_path, "r") as f:
        hypernodes = json.load(f)
    for node in hypernodes:
        node["pieces"] = extract_pieces(node["board"])
    return hypernodes

def extract_pieces(board):
    """
    Extracts contiguous pieces from a board (a 2D list of strings) using flood fill.
    Each non-"empty" contiguous region is considered a separate piece.
    Returns a list of pieces where each piece is a dict with:
      - "token": the string in the cells,
      - "cells": a sorted list of [row, col] coordinates (with row 0 at the bottom).
    """
    rows = len(board)
    cols = len(board[0])
    visited = [[False] * cols for _ in range(rows)]
    pieces = []
    
    def dfs(r, c, token):
        stack = [(r, c)]
        cells = []
        while stack:
            rr, cc = stack.pop()
            if visited[rr][cc]:
                continue
            visited[rr][cc] = True
            cells.append([rr, cc])
            for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
                nr, nc = rr + dr, cc + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    if not visited[nr][nc] and board[nr][nc] == token:
                        stack.append((nr, nc))
        return sorted(cells)
    
    for r in range(rows):
        for c in range(cols):
            if board[r][c] != "empty" and not visited[r][c]:
                token = board[r][c]
                cells = dfs(r, c, token)
                pieces.append({"token": token, "cells": cells})
    return pieces

def is_one_step_translation(piece_from, piece_to):
    if len(piece_from) != len(piece_to):
        return False, None
    sorted_from = sorted(piece_from)
    sorted_to = sorted(piece_to)
    offset = (sorted_to[0][0] - sorted_from[0][0],
              sorted_to[0][1] - sorted_from[0][1])
    for (r_from, c_from), (r_to, c_to) in zip(sorted_from, sorted_to):
        if (r_to - r_from, c_to - c_from) != offset:
            return False, None
    valid_offsets = {(1,0), (-1,0), (0,1), (0,-1)}
    if offset in valid_offsets:
        return True, offset
    return False, None

def get_move_info(state_a, state_b):
    pieces_a = state_a["pieces"]
    pieces_b = state_b["pieces"]
    if len(pieces_a) != len(pieces_b):
        return None
    unchanged_count = 0
    changed_a = None
    used_indices = set()
    for p_a in pieces_a:
        match_found = False
        for j, p_b in enumerate(pieces_b):
            if j in used_indices:
                continue
            if p_a["token"] == p_b["token"] and p_a["cells"] == p_b["cells"]:
                unchanged_count += 1
                used_indices.add(j)
                match_found = True
                break
        if not match_found:
            changed_a = p_a
    changed_b = None
    for j, p_b in enumerate(pieces_b):
        if j not in used_indices:
            changed_b = p_b
            break
    if unchanged_count != len(pieces_a) - 1 or changed_a is None or changed_b is None:
        return None
    valid, offset = is_one_step_translation(changed_a["cells"], changed_b["cells"])
    if not valid:
        return None
    set_a = set(tuple(x) for x in changed_a["cells"])
    set_b = set(tuple(x) for x in changed_b["cells"])
    common = sorted(list(set_a.intersection(set_b)))
    unique = sorted(list(set_a.symmetric_difference(set_b)))
    return {"moved_from": changed_a["cells"],
            "moved_to": changed_b["cells"],
            "offset": offset,
            "overlap": {"AND": common, "OR": unique}}

def build_hypernode_graph(hypernodes):
    G = nx.Graph()
    for i, node in enumerate(hypernodes):
        G.add_node(i, board=node["board"], pieces=node["pieces"])
    n = len(hypernodes)
    for i in range(n):
        for j in range(i+1, n):
            move_info = get_move_info(hypernodes[i], hypernodes[j])
            if move_info is not None:
                G.add_edge(i, j, move=move_info)
    return G

def merge_boards(board1, board2):
    rows = len(board1)
    cols = len(board1[0])
    merged = np.zeros((rows, cols), dtype=int)
    for r in range(rows):
        for c in range(cols):
            if board1[r][c] != "empty" or board2[r][c] != "empty":
                merged[r, c] = 1
    return merged

def get_component_breakdown(binary_board, target=0):
    """
    Computes connected component sizes for cells equal to target (default 0 for empty cells)
    using 4-connectivity. Returns a list of component sizes.
    """
    rows, cols = binary_board.shape
    visited = np.zeros_like(binary_board, dtype=bool)
    comp_sizes = []
    
    def dfs(r, c):
        stack = [(r, c)]
        size = 0
        while stack:
            rr, cc = stack.pop()
            if visited[rr, cc]:
                continue
            visited[rr, cc] = True
            if binary_board[rr, cc] == target:
                size += 1
                for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        if not visited[nr, nc] and binary_board[nr, nc] == target:
                            stack.append((nr, nc))
        return size
    
    for r in range(rows):
        for c in range(cols):
            if binary_board[r, c] == target and not visited[r, c]:
                comp_size = dfs(r, c)
                if comp_size > 0:
                    comp_sizes.append(comp_size)
    return comp_sizes

def merge_and_get_empty_components(u, v, hypernodes):
    board_u = hypernodes[u]["board"]
    board_v = hypernodes[v]["board"]
    merged = merge_boards(board_u, board_v)
    empty_components = get_component_breakdown(merged, target=0)
    return empty_components

def save_merged_edge(u, v, hypernodes, output_dir):
    """
    For the edge between hypernode u and v:
      - Merge their boards using a logical OR.
      - Compute the connected component breakdown for the empty spaces.
      - Plot the merged board with grid lines (row 0 at the bottom) and annotate the image with the empty-component breakdown.
      - Save the resulting image as a PNG.
    """
    board_u = hypernodes[u]["board"]
    board_v = hypernodes[v]["board"]
    merged = merge_boards(board_u, board_v)
    empty_cc = get_component_breakdown(merged, target=0)
    
    rows, cols = merged.shape
    figsize = (cols * 0.5, rows * 0.5)
    fig, ax = plt.subplots(figsize=figsize)
    
    # Display the merged board with grid lines.
    ax.imshow(merged, cmap="gray_r", interpolation="nearest", origin="lower")
    ax.set_xticks(np.arange(-0.5, cols, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, rows, 1), minor=True)
    ax.grid(which="minor", color="black", linestyle="-", linewidth=1)
    ax.set_aspect("equal")
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    
    ax.set_title(f"Edge H{u}-{v}\nEmpty CC: {empty_cc}", fontsize=14)
    plt.tight_layout()
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_file = os.path.join(output_dir, f"merged_edge_{u}_{v}.png")
    plt.savefig(output_file, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved merged edge image: {output_file}")

def main():
    hypernodes = load_hypernodes()
    if hypernodes is None:
        return
    G = build_hypernode_graph(hypernodes)
    print(f"Graph has {len(G.nodes())} nodes and {len(G.edges())} edges.")
    
    # Create an output directory for merged edge images.
    image_output_dir = "merged_edges"
    if not os.path.exists(image_output_dir):
        os.makedirs(image_output_dir)
    
    # Create a dictionary to store empty component breakdowns for each edge.
    edge_empty_components = {}
    
    for u, v, data in G.edges(data=True):
        save_merged_edge(u, v, hypernodes, image_output_dir)
        comp_breakdown = merge_and_get_empty_components(u, v, hypernodes)
        edge_key = f"{u}-{v}"
        edge_empty_components[edge_key] = comp_breakdown
    
    # Save the empty component breakdown for each edge as JSON in the March7 folder.
    output_json = os.path.join("March7", "merged_edge_empty_components.json")
    with open(output_json, "w") as f:
        json.dump(edge_empty_components, f, indent=2)
    print(f"Saved edge empty component breakdown in JSON: {output_json}")

if __name__ == "__main__":
    main()