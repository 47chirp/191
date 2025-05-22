import os
import json
from itertools import combinations
from collections import deque
import copy

# Global moves dictionary for four directions.
MOVES = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1)
}

# ----------------------------------
# Utility Functions
# ----------------------------------

def load_puzzle_config(file_path="puzzle_config.json"):
    """Loads the puzzle configuration from JSON."""
    if not os.path.exists(file_path):
        print("Error: Puzzle configuration file not found!")
        return None
    with open(file_path, "r") as f:
        data = json.load(f)
    print(f"Loaded puzzle configuration from: {os.path.abspath(file_path)}")
    return data

def get_piece_dimensions(piece):
    """Returns (height, width) for a given piece based on its type."""
    if piece["piece_type"] == "1x1":
        return 1, 1
    elif piece["piece_type"] == "1x2":
        return 1, 2
    elif piece["piece_type"] == "2x1":
        return 2, 1
    else:
        raise ValueError(f"Unknown piece type: {piece['piece_type']}")

def create_board_representation(pieces):
    """
    Creates a board dictionary for the pieces.
    Keys are (row, col) and values are piece labels.
    """
    board = {}
    for piece in pieces:
        height, width = get_piece_dimensions(piece)
        # Store dimensions in the piece (if not already set)
        piece.setdefault("height", height)
        piece.setdefault("width", width)
        for r in range(piece["height"]):
            for c in range(piece["width"]):
                board[(piece["row"] + r, piece["col"] + c)] = piece["label"]
    return board

def is_valid_move(piece, new_row, new_col, board, rows, cols):
    """
    Checks if moving a piece to (new_row, new_col) is valid:
      - Stays within board boundaries.
      - Does not overlap any occupied cell (including obstacles marked as "X").
    """
    height, width = piece["height"], piece["width"]
    if new_row < 0 or new_col < 0 or new_row + height > rows or new_col + width > cols:
        return False
    new_cells = {(new_row + r, new_col + c) for r in range(height) for c in range(width)}
    for cell in new_cells:
        if cell in board and board[cell] != piece["label"]:
            return False
    return True

def get_all_possible_moves(pieces, extra_blocks, rows, cols):
    """
    Returns a dictionary mapping each piece's label to a list of valid moves.
    Moves are generated from the current positions, and extra blocks are treated as obstacles.
    Each move is represented as (direction, new_row, new_col).
    """
    board = create_board_representation(pieces)
    for cell in extra_blocks:
        board[cell] = "X"
    move_dict = {}
    for piece in pieces:
        move_dict[piece["label"]] = []
        for direction, (dr, dc) in MOVES.items():
            new_row, new_col = piece["row"] + dr, piece["col"] + dc
            if is_valid_move(piece, new_row, new_col, board, rows, cols):
                move_dict[piece["label"]].append((direction, new_row, new_col))
    return move_dict

def board_to_tuple(state):
    """
    Converts a state (with pieces and extra_blocks) into a hashable tuple.
    Pieces are represented by (label, row, col) and extra blocks are sorted.
    """
    pieces_tuple = tuple(sorted((p["label"], p["row"], p["col"]) for p in state["pieces"]))
    extra_tuple = tuple(sorted(state["extra_blocks"]))
    return (pieces_tuple, extra_tuple)

def copy_state(state):
    """Deep-copies the state dictionary."""
    return copy.deepcopy(state)

# ----------------------------------
# Hyper Node & Super Node Generation
# ----------------------------------

def count_valid_arrangements(puzzle_data):
    """
    Generates all valid, non-overlapping arrangements (Hyper-Nodes)
    for the horizontal (1x2) and vertical (2x1) pieces.
    Each arrangement is a frozenset of placements (each placement is a tuple of two cells).
    """
    rows, cols = puzzle_data["rows"], puzzle_data["cols"]
    num_1x2 = sum(1 for p in puzzle_data["pieces"] if p["piece_type"] == "1x2")
    num_2x1 = sum(1 for p in puzzle_data["pieces"] if p["piece_type"] == "2x1")
    
    placements_h = []
    placements_v = []
    for r in range(rows):
        for c in range(cols - 1):
            placements_h.append(((r, c), (r, c + 1)))
    for r in range(rows - 1):
        for c in range(cols):
            placements_v.append(((r, c), (r + 1, c)))
    
    valid_states = set()
    for chosen_h in combinations(placements_h, num_1x2):
        for chosen_v in combinations(placements_v, num_2x1):
            occupied = set()
            valid = True
            state = []
            for placement in chosen_h + chosen_v:
                if placement[0] in occupied or placement[1] in occupied:
                    valid = False
                    break
                occupied.add(placement[0])
                occupied.add(placement[1])
                state.append(placement)
            if valid:
                valid_states.add(frozenset(state))
    print(f"Total valid hyper arrangements (Hyper-Nodes): {len(valid_states)}")
    return list(valid_states)

def generate_supernode_states(hyper_node, puzzle_data):
    """
    For a given hyper node (a frozenset of placements), generate all super node states.
    A super node state assigns placements to the pieces (assumed order: horizontal then vertical)
    and then places the extra 1x1 blocks in the remaining empty cells.
    """
    rows, cols = puzzle_data["rows"], puzzle_data["cols"]
    horizontal_placements = sorted([p for p in hyper_node if p[0][0] == p[1][0]], key=lambda x: (x[0][0], x[0][1]))
    vertical_placements = sorted([p for p in hyper_node if p[0][1] == p[1][1]], key=lambda x: (x[0][0], x[0][1]))
    
    horiz_pieces = [copy.deepcopy(p) for p in puzzle_data["pieces"] if p["piece_type"] == "1x2"]
    vert_pieces = [copy.deepcopy(p) for p in puzzle_data["pieces"] if p["piece_type"] == "2x1"]
    
    if len(horizontal_placements) != len(horiz_pieces) or len(vertical_placements) != len(vert_pieces):
        print("Warning: Mismatch in number of placements and pieces.")
    
    assigned_pieces = []
    for piece, placement in zip(horiz_pieces, horizontal_placements):
        piece["row"], piece["col"] = placement[0]
        assigned_pieces.append(piece)
    for piece, placement in zip(vert_pieces, vertical_placements):
        piece["row"], piece["col"] = placement[0]
        assigned_pieces.append(piece)
    
    occupied_cells = {cell for placement in hyper_node for cell in placement}
    total_cells = {(r, c) for r in range(rows) for c in range(cols)}
    empty_spaces = list(total_cells - occupied_cells)
    
    supernode_states = []
    for extra in combinations(empty_spaces, 4):
        state = {
            "pieces": copy.deepcopy(assigned_pieces),
            "extra_blocks": list(extra)
        }
        supernode_states.append(state)
    
    print(f"Hyper node {hyper_node} generated {len(supernode_states)} super node states.")
    return supernode_states

def build_hyper_super_structure(hyper_states, puzzle_data):
    """
    Builds the hyper–super relationships and returns a list of all super node states.
    (No plotting is performed.)
    """
    all_super_states = []
    for idx, hyper_state in enumerate(hyper_states):
        hyper_label = f"H{idx}"
        super_states = generate_supernode_states(hyper_state, puzzle_data)
        print(f"{hyper_label} has {len(super_states)} children (Super-Nodes)")
        all_super_states.extend(super_states)
    return all_super_states

# ----------------------------------
# BFS to Find the Shortest Path to a Solution
# ----------------------------------

def target_piece_in_bottom_left(piece, rows, cols):
    """
    Checks if the target piece covers the bottom-left cell (rows-1, 0).
    (For pieces wider than 1 cell, only one cell needs to cover the bottom-left.)
    """
    height, width = piece["height"], piece["width"]
    occupied_cells = {(piece["row"] + r, piece["col"] + c) for r in range(height) for c in range(width)}
    return (rows - 1, 0) in occupied_cells

def find_shortest_path_from_supernode(initial_state, puzzle_data, target_label):
    """
    From a given super node state, perform a BFS to find the shortest sequence of moves
    that leads to a solution state (target piece covers the bottom-left cell).
    Returns the move sequence and the resulting solved state, or (None, None) if no solution is found.
    """
    rows, cols = puzzle_data["rows"], puzzle_data["cols"]
    queue = deque()
    visited = set()
    start_hash = board_to_tuple(initial_state)
    queue.append((initial_state, []))
    visited.add(start_hash)
    
    while queue:
        current_state, move_history = queue.popleft()
        target_piece = next((p for p in current_state["pieces"] if p["label"] == target_label), None)
        if target_piece and target_piece_in_bottom_left(target_piece, rows, cols):
            return move_history, current_state  # Found a solution
        
        moves = get_all_possible_moves(current_state["pieces"], current_state["extra_blocks"], rows, cols)
        for piece in current_state["pieces"]:
            for direction, new_row, new_col in moves[piece["label"]]:
                new_state = copy_state(current_state)
                for p in new_state["pieces"]:
                    if p["label"] == piece["label"]:
                        p["row"], p["col"] = new_row, new_col
                        break
                new_hash = board_to_tuple(new_state)
                if new_hash not in visited:
                    visited.add(new_hash)
                    queue.append((new_state, move_history + [(piece["label"], direction)]))
    return None, None  # No solution found

# ----------------------------------
# Main Execution
# ----------------------------------

def main():
    puzzle_data = load_puzzle_config()
    if not puzzle_data:
        return

    # Generate hyper node arrangements.
    hyper_states = count_valid_arrangements(puzzle_data)
    
    # Build hyper-super structure (super node states).
    print("\nBuilding Hyper-Super structure and generating Super-Nodes...")
    super_nodes = build_hyper_super_structure(hyper_states, puzzle_data)
    print(f"\nTotal super node states generated: {len(super_nodes)}")
    
    # For each super node, run BFS to find the shortest path to a solution.
    target_label = puzzle_data["target"]
    solved_count = 0
    for idx, state in enumerate(super_nodes):
        moves, solved_state = find_shortest_path_from_supernode(state, puzzle_data, target_label)
        if moves is not None:
            solved_count += 1
            print(f"\nSuper-node #{idx} solution (shortest path in {len(moves)} moves):")
            for move in moves:
                print(f"  Piece {move[0]} moves {move[1]}")
        else:
            print(f"\nSuper-node #{idx} did NOT yield a solution.")
    
    print("\n================================================")
    print(f"Total super nodes that produced a solution: {solved_count}")
    print("================================================")

if __name__ == "__main__":
    main()