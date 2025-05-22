import os
import json
from collections import deque
from itertools import combinations
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

# ----------------------------
# Puzzle Configuration & Helper Functions
# ----------------------------

MOVES = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1)
}

def load_puzzle_config(file_path="puzzle_config.json"):
    """Loads the puzzle configuration from JSON."""
    abs_path = os.path.abspath(file_path)
    print(f"Looking for puzzle config at: {abs_path}")
    if not os.path.exists(abs_path):
        print("Error: Puzzle configuration file not found!")
        return None
    with open(abs_path, "r") as f:
        data = json.load(f)
    if isinstance(data, list):
        print("ERROR: Loaded JSON is a list instead of a dictionary!")
        return None
    return data

def get_piece_dimensions(piece):
    """Returns the height and width based on piece type."""
    if piece["piece_type"] == "1x1":
        return 1, 1
    elif piece["piece_type"] == "1x2":
        return 1, 2
    elif piece["piece_type"] == "2x1":
        return 2, 1
    else:
        raise ValueError(f"Unknown piece type: {piece['piece_type']}")

def create_board_representation(pieces):
    """Creates a board representation with occupied positions."""
    board = {}
    for piece in pieces:
        height, width = get_piece_dimensions(piece)
        piece["height"], piece["width"] = height, width  
        for r in range(height):
            for c in range(width):
                board[(piece["row"] + r, piece["col"] + c)] = piece["label"]
    return board

def is_valid_move(piece, new_row, new_col, board, rows, cols):
    """Checks if a piece can move one step without collisions or leaving the board."""
    height, width = piece["height"], piece["width"]
    if new_row < 0 or new_col < 0 or new_row + height > rows or new_col + width > cols:
        return False
    for r in range(height):
        for c in range(width):
            cell = (new_row + r, new_col + c)
            if cell in board and board[cell] != piece["label"]:
                return False
    return True

def get_all_possible_moves(pieces, rows, cols):
    """Finds all valid moves for each piece in the puzzle."""
    board = create_board_representation(pieces)
    move_dict = {}
    for piece in pieces:
        move_dict[piece["label"]] = []
        for direction, (dr, dc) in MOVES.items():
            new_row, new_col = piece["row"] + dr, piece["col"] + dc
            if is_valid_move(piece, new_row, new_col, board, rows, cols):
                move_dict[piece["label"]].append((direction, new_row, new_col))
    return move_dict

def board_to_tuple(pieces):
    """Converts the board state to a tuple for hashing."""
    return tuple(sorted((p["label"], p["row"], p["col"]) for p in pieces))

# ----------------------------
# Hyper‑node & Super‑node Generation (Converted Format)
# ----------------------------

def count_valid_arrangements(puzzle_data):
    """
    Generates unique valid (non-overlapping) board arrangements (hyper‑nodes)
    from the puzzle configuration. Arrangements are made for pieces of type "1x2" and "2x1",
    while the remaining pieces (e.g. the target or other fixed pieces) are kept at their original positions.
    Each hyper‑node state is a list of dictionaries, in the same format as puzzle_data["pieces"].
    """
    rows, cols = puzzle_data["rows"], puzzle_data["cols"]
    # Separate pieces into those we arrange and those we leave fixed.
    arrangeable_1x2 = [p for p in puzzle_data["pieces"] if p["piece_type"] == "1x2"]
    arrangeable_2x1 = [p for p in puzzle_data["pieces"] if p["piece_type"] == "2x1"]
    fixed_pieces = [p.copy() for p in puzzle_data["pieces"] if p["piece_type"] not in {"1x2", "2x1"}]
    
    num_1x2 = len(arrangeable_1x2)
    num_2x1 = len(arrangeable_2x1)
    
    # Generate possible placements for arranged pieces.
    placements_h = [((r, c), (r, c + 1)) for r in range(rows) for c in range(cols - 1)]
    placements_v = [((r, c), (r + 1, c)) for r in range(rows - 1) for c in range(cols)]
    
    valid_states_set = set()  # for uniqueness
    valid_states = []
    for chosen_h in combinations(placements_h, num_1x2):
        for chosen_v in combinations(placements_v, num_2x1):
            occupied = set()
            valid = True
            for placement in chosen_h + chosen_v:
                if placement[0] in occupied or placement[1] in occupied:
                    valid = False
                    break
                occupied.update(placement)
            if valid:
                state_list = []
                # For arranged 1x2 pieces:
                for p, placement in zip(arrangeable_1x2, chosen_h):
                    new_piece = p.copy()
                    new_piece["row"] = placement[0][0]
                    new_piece["col"] = placement[0][1]
                    h, w = get_piece_dimensions(new_piece)
                    new_piece["height"] = h
                    new_piece["width"] = w
                    state_list.append(new_piece)
                # For arranged 2x1 pieces:
                for p, placement in zip(arrangeable_2x1, chosen_v):
                    new_piece = p.copy()
                    new_piece["row"] = placement[0][0]
                    new_piece["col"] = placement[0][1]
                    h, w = get_piece_dimensions(new_piece)
                    new_piece["height"] = h
                    new_piece["width"] = w
                    state_list.append(new_piece)
                # Add fixed pieces unchanged.
                state_list.extend(fixed_pieces)
                state_tuple = board_to_tuple(state_list)
                if state_tuple not in valid_states_set:
                    valid_states_set.add(state_tuple)
                    valid_states.append(state_list)
    print(f"Total unique valid arrangements (Hyper‑Nodes): {len(valid_states)}")
    return valid_states

def count_supernode_arrangements(hyper_state, puzzle_data):
    """
    For a given hyper‑node state (a list of piece dictionaries), returns a list of
    board states (super‑node states) where 4 extra blocks (1x1 pieces) are added into
    empty cells. These extra blocks are assigned labels "Block1", "Block2", etc.
    """
    rows, cols = puzzle_data["rows"], puzzle_data["cols"]
    total_cells = {(r, c) for r in range(rows) for c in range(cols)}
    occupied_cells = set()
    for piece in hyper_state:
        height = piece["height"]
        width = piece["width"]
        for r in range(height):
            for c in range(width):
                occupied_cells.add((piece["row"] + r, piece["col"] + c))
    empty_spaces = list(total_cells - occupied_cells)
    arrangements = []
    if len(empty_spaces) >= 4:
        for combo in combinations(empty_spaces, 4):
            new_state = [p.copy() for p in hyper_state]
            for idx, cell in enumerate(combo):
                block = {
                    "label": f"Block{idx+1}",
                    "row": cell[0],
                    "col": cell[1],
                    "piece_type": "1x1",
                    "height": 1,
                    "width": 1
                }
                new_state.append(block)
            arrangements.append(new_state)
    return arrangements

# ----------------------------
# BFS to Find Shortest Path from a Given State
# ----------------------------
def find_shortest_target_path_from_state(initial_pieces, puzzle_data):
    """
    Uses BFS to find the shortest sequence of moves from a given board state
    (initial_pieces) to a configuration where the target piece is in the bottom‑left.
    Returns a list of moves (each move is a tuple: (piece_label, direction)).
    If the target piece is missing in a state, that state is skipped.
    """
    rows, cols = puzzle_data["rows"], puzzle_data["cols"]
    target_label = puzzle_data["target"]
    queue = deque()
    visited = set()
    queue.append((initial_pieces, []))
    visited.add(board_to_tuple(initial_pieces))
    
    while queue:
        current_pieces, move_history = queue.popleft()
        try:
            target_piece = next(p for p in current_pieces if p["label"] == target_label)
        except StopIteration:
            # Target piece not found in this state; skip to the next.
            continue
        
        if target_piece["row"] == rows - 1 and target_piece["col"] == 0:
            return move_history  # Found solution
        
        possible_moves = get_all_possible_moves(current_pieces, rows, cols)
        for piece in current_pieces:
            for direction, new_row, new_col in possible_moves[piece["label"]]:
                new_pieces = [p.copy() for p in current_pieces]
                for p in new_pieces:
                    if p["label"] == piece["label"]:
                        p["row"], p["col"] = new_row, new_col
                new_state = board_to_tuple(new_pieces)
                if new_state not in visited:
                    visited.add(new_state)
                    queue.append((new_pieces, move_history + [(piece["label"], direction)]))
    return None  # No solution found

# ----------------------------
# Radial Graph Construction (Tiers 0-3)
# ----------------------------
def build_radial_graph_with_bfs(puzzle_data):
    """
    Builds a radial graph with 4 tiers:
      - Tier 0: Center ("Start")
      - Tier 1: All Hyper‑Nodes (arranged uniformly on a circle, radius 3)
      - Tier 2: All Super‑Nodes (arranged uniformly on a circle, radius 6)
      - Tier 3: For each Super‑Node, attach a branch showing the BFS shortest path
                (the moves to reach a solution) from that super‑node.
    """
    G = nx.DiGraph()
    pos = {}
    
    # Tier 0: Center
    center_node = "Start"
    G.add_node(center_node)
    pos[center_node] = (0, 0)
    
    # Generate hyper‑node states using the actual puzzle configuration.
    hyper_states = count_valid_arrangements(puzzle_data)  # List of board states
    
    hyper_nodes = {}  # Map: hyper node label -> board state
    super_nodes = {}  # Map: super node label -> board state
    
    # ----------------------------
    # Tier 1: Hyper‑Nodes (radius 3)
    # ----------------------------
    hyper_labels = []
    for idx, state in enumerate(hyper_states):
        h_label = f"H{idx}"
        G.add_node(h_label)
        G.add_edge(center_node, h_label)
        hyper_nodes[h_label] = state
        hyper_labels.append(h_label)
    total_hyper = len(hyper_labels)
    for i, node in enumerate(hyper_labels):
        angle = 2 * np.pi * i / total_hyper
        pos[node] = (3 * np.cos(angle), 3 * np.sin(angle))
    
    # ----------------------------
    # Tier 2: Super‑Nodes (radius 6)
    # ----------------------------
    super_labels = []
    for h_label, state in hyper_nodes.items():
        # Generate super‑node states from each hyper‑node state.
        super_arrangements = count_supernode_arrangements(state, puzzle_data)
        for i, super_state in enumerate(super_arrangements):
            s_label = f"{h_label}_S{i}"
            G.add_node(s_label)
            G.add_edge(h_label, s_label)
            super_nodes[s_label] = super_state
            super_labels.append(s_label)
    total_super = len(super_labels)
    for i, node in enumerate(super_labels):
        angle = 2 * np.pi * i / total_super
        pos[node] = (6 * np.cos(angle), 6 * np.sin(angle))
    
    # ----------------------------
    # Tier 3: BFS Branch from Each Super‑Node (Shortest Path)
    # ----------------------------
    base_offset = 1.0    # Base distance between successive moves in the branch.
    curvature = 0.3      # Curvature factor for branch appearance.
    for s_label in super_labels:
        state = super_nodes[s_label]
        bfs_path = find_shortest_target_path_from_state(state, puzzle_data)
        if not bfs_path:
            continue  # Skip if no solution found.
        prev_node = s_label
        branch_angle = np.arctan2(pos[s_label][1], pos[s_label][0])
        for step_idx, move in enumerate(bfs_path, start=1):
            move_label = f"{s_label}_step{step_idx}: {move[0]} {move[1]}"
            G.add_node(move_label)
            G.add_edge(prev_node, move_label)
            displacement = base_offset * step_idx
            perp_offset = curvature * (step_idx ** 1.5)
            x = pos[s_label][0] + displacement * np.cos(branch_angle) - perp_offset * np.sin(branch_angle)
            y = pos[s_label][1] + displacement * np.sin(branch_angle) + perp_offset * np.cos(branch_angle)
            pos[move_label] = (x, y)
            prev_node = move_label
    
    # ----------------------------
    # Graph Drawing
    # ----------------------------
    plt.figure(figsize=(16, 16))
    def get_color(node):
        if node == center_node:
            return "black"
        elif node.startswith("H"):
            return "red"
        elif "_S" in node:
            return "blue"
        else:
            return "green"
    node_colors = [get_color(node) for node in G.nodes]
    def get_size(node):
        if node == center_node:
            return 400
        elif node.startswith("H"):
            return 200
        elif "_S" in node:
            return 150
        else:
            return 100
    node_sizes = [get_size(node) for node in G.nodes]
    
    nx.draw(G, pos,
            node_color=node_colors,
            edge_color="gray",
            alpha=0.9,
            with_labels=True,
            font_color="white",
            node_size=node_sizes)
    plt.title("Radial Graph: Start → Hyper‑Nodes → Super‑Nodes → BFS Shortest Paths", fontsize=18)
    plt.show()

# ----------------------------
# Main Execution
# ----------------------------
def main():
    puzzle_data = load_puzzle_config()
    if not puzzle_data:
        return
    build_radial_graph_with_bfs(puzzle_data)

if __name__ == "__main__":
    main()