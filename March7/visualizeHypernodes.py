import os
import json
import matplotlib.pyplot as plt
import networkx as nx

'''
This saves all of the hypernodes into the visualization_all folder and also outputs
a JSON file with connection information in the March7 folder.
Working as of 3/9/25
'''

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
    # Always compute pieces from the board using the flood-fill method.
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
    """
    Checks whether piece_to is a one-step translation of piece_from.
    Both piece_from and piece_to are lists of [row, col] coordinates.
    Returns (True, offset) if every cell in piece_from moved by the same offset,
    and that offset is one unit in one of the four cardinal directions.
    Otherwise returns (False, None).
    """
    if len(piece_from) != len(piece_to):
        return False, None
    sorted_from = sorted(piece_from)
    sorted_to = sorted(piece_to)
    offset = (sorted_to[0][0] - sorted_from[0][0],
              sorted_to[0][1] - sorted_from[0][1])
    for (r_from, c_from), (r_to, c_to) in zip(sorted_from, sorted_to):
        if (r_to - r_from, c_to - c_from) != offset:
            return False, None
    valid_offsets = {(1, 0), (-1, 0), (0, 1), (0, -1)}
    if offset in valid_offsets:
        return True, offset
    return False, None

def get_move_info(state_a, state_b):
    """
    Compares two hypernode states (each with a "pieces" key) to see if they differ by exactly one valid move.
    Two states are one move apart if:
      1. They have the same number of pieces.
      2. All pieces are identical (matching token and cells) except one.
      3. The differing piece in state_b is a one-step translation of its counterpart in state_a.
    Returns a dictionary with:
       "token":     the token of the moved piece,
       "moved_from": the cells of the piece in state_a,
       "moved_to":   the cells of the piece in state_b,
       "offset":     the translation offset (row_change, col_change)
    or returns None if conditions aren’t met.
    """
    pieces_a = state_a["pieces"]
    pieces_b = state_b["pieces"]
    if len(pieces_a) != len(pieces_b):
        return None

    unchanged_count = 0
    changed_a = None
    used_indices = set()
    
    # Match each piece in state_a with one in state_b (require same token)
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

    return {"token": changed_a["token"], "moved_from": changed_a["cells"],
            "moved_to": changed_b["cells"], "offset": offset}

def build_hypernode_graph(hypernodes):
    """
    Builds a NetworkX graph where each hypernode is a node.
    Two hypernodes are connected if they differ by exactly one valid move.
    """
    G = nx.Graph()
    for i, node in enumerate(hypernodes):
        G.add_node(i, board=node["board"], pieces=node["pieces"])
    n = len(hypernodes)
    for i in range(n):
        for j in range(i + 1, n):
            move_info = get_move_info(hypernodes[i], hypernodes[j])
            if move_info is not None:
                G.add_edge(i, j, move=move_info)
    return G

def draw_board(ax, board):
    """
    Draws a board configuration on the given Matplotlib axis.
    The board is a 2D list of strings with row 0 at the bottom.
    Grid lines are drawn and non-"empty" cells are annotated.
    """
    rows = len(board)
    cols = len(board[0])
    ax.set_xticks(range(cols+1))
    ax.set_yticks(range(rows+1))
    ax.grid(True)
    for r in range(rows):
        for c in range(cols):
            cell = board[r][c]
            if cell != "empty":
                ax.text(c + 0.5, r + 0.5, cell, fontsize=14,
                        ha="center", va="center")
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.set_xticklabels([])
    ax.set_yticklabels([])

def save_hypernode_connections(hypernode_index, hypernodes, G, out_dir):
    """
    Saves a visualization image showing a hypernode’s board along with its connected neighbors.
    The boards are arranged in a grid and each subplot’s title includes the hypernode index
    and move details (if available).
    """
    original_board = hypernodes[hypernode_index]["board"]
    neighbors = list(G.neighbors(hypernode_index))
    boards_to_show = [(hypernode_index, original_board, None)]
    for nb in neighbors:
        move_info = G.get_edge_data(hypernode_index, nb).get("move")
        nb_board = hypernodes[nb]["board"]
        boards_to_show.append((nb, nb_board, move_info))
    
    total = len(boards_to_show)
    ncols = min(3, total)
    nrows = (total + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 4 * nrows))
    if total == 1:
        axes = [axes]
    else:
        axes = axes.flatten()
    for i, (idx, board, move_info) in enumerate(boards_to_show):
        ax = axes[i]
        draw_board(ax, board)
        title = f"Hypernode {idx}"
        if move_info:
            title += f"\n{move_info['token']} from: {move_info['moved_from']}\nto: {move_info['moved_to']}\noffset: {move_info['offset']}"
        ax.set_title(title)
    for j in range(i + 1, len(axes)):
        axes[j].axis("off")
    plt.tight_layout()
    filename = os.path.join(out_dir, f"hypernode_{hypernode_index}.png")
    plt.savefig(filename)
    plt.close(fig)

def save_connections_json(G, folder="March7", filename="hypernode_connections.json"):
    """
    Saves the connection information of the hypernode graph as a JSON file.
    Each key is a hypernode index and its value is the list of connected neighbor indices.
    """
    connections = {}
    for node in G.nodes():
        connections[node] = list(G.neighbors(node))
    out_path = os.path.join(folder, filename)
    with open(out_path, "w") as f:
        json.dump(connections, f, indent=2)
    print(f"Connections JSON saved to {out_path}")

def main():
    # Load all hypernodes from file.
    hypernodes = load_hypernodes()
    if hypernodes is None:
        return
    # Build the hypernode graph.
    G = build_hypernode_graph(hypernodes)
    print("Graph has", len(G.nodes()), "nodes and", len(G.edges()), "edges.")
    
    # Create an output directory for visualizations.
    out_dir = "visualizations_all"
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    
    # Save visualizations for every hypernode.
    for i in range(len(hypernodes)):
        print(f"Saving visualization for hypernode {i} and its connections")
        save_hypernode_connections(i, hypernodes, G, out_dir)
    
    # Additionally, save the connections information as JSON in the March7 folder.
    save_connections_json(G, folder="March7", filename="hypernode_connections.json")
    
    print("All visualizations and JSON connection data have been saved.")

if __name__ == "__main__":
    main()