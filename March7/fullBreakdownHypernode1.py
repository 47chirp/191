import os
import json
import numpy as np
import networkx as nx
from itertools import combinations

###########################
# Functions for hypernodes
###########################

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
    Uses flood fill to extract contiguous pieces from a board (2D list of strings).
    Returns a list of pieces (each a dict with "token" and "cells").
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
    """
    Compares two hypernode states (using their "pieces") and returns a dictionary
    if they differ by exactly one valid move. (A valid move is when exactly one piece
    is different and that piece in state_b is a one-step translation of its counterpart in state_a.)
    Also computes the overlap of the moved piece's cell sets.
    """
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
    """
    Builds a NetworkX graph where hypernodes are nodes.
    Two hypernodes are connected if get_move_info returns a valid move dictionary.
    """
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
    """
    Merges two boards using a logical OR.
    If either board has a non-"empty" cell at a position, the merged cell is set to 1.
    Returns a 2D numpy array.
    """
    rows = len(board1)
    cols = len(board1[0])
    merged = np.zeros((rows, cols), dtype=int)
    for r in range(rows):
        for c in range(cols):
            if board1[r][c] != "empty" or board2[r][c] != "empty":
                merged[r, c] = 1
    return merged

#########################################
# New function: Enumerate allocations
#########################################

def allocate_1x1s(merged_board, num=4):
    """
    Finds all ways to allocate 'num' 1x1 pieces in the merged board.
    Here, a valid allocation is a selection of 'num' coordinates that are empty (value 0) in the merged board.
    Returns a list of allocations, each allocation is a list of (row, col) tuples.
    """
    rows, cols = merged_board.shape
    empty_cells = []
    for r in range(rows):
        for c in range(cols):
            if merged_board[r, c] == 0:  # cell is empty
                empty_cells.append((r, c))
    # Use combinations to list all ways to pick 'num' empty cells.
    allocs = [list(comb) for comb in combinations(empty_cells, num)]
    return allocs

#########################################
# Main flow for hypernode 0
#########################################

def main():
    # Load hypernodes and build the graph.
    hypernodes = load_hypernodes()
    if hypernodes is None:
        return
    G = build_hypernode_graph(hypernodes)
    print(f"Graph has {len(G.nodes())} nodes and {len(G.edges())} edges.")
    
    # Select hypernode 0 as the highest tier.
    root = 0
    # Get the neighbors (tier 2) of hypernode 0.
    neighbors = list(G.neighbors(root))
    print(f"Hypernode {root} has neighbors: {neighbors}")
    
    # Dictionary to store allocations for each edge from hypernode 0 to a neighbor.
    allocations_dict = {}
    
    # For each neighbor (edge from root to neighbor), compute merged board (tier 3)
    # and then enumerate allocations of 4 1x1 pieces (tier 4).
    for nb in neighbors:
        merged = merge_boards(hypernodes[root]["board"], hypernodes[nb]["board"])
        allocs = allocate_1x1s(merged, num=4)
        edge_key = f"{root}-{nb}"
        allocations_dict[edge_key] = allocs
        print(f"Edge {edge_key} has {len(allocs)} allocation(s) for 4 1x1s.")
    
    # Save the allocation dictionary as JSON in the "March7" folder.
    output_file = os.path.join("March7", "allocation_4_1x1s.json")
    with open(output_file, "w") as f:
        json.dump(allocations_dict, f, indent=2)
    print(f"Saved allocations JSON to {output_file}")

if __name__ == "__main__":
    main()