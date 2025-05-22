import os
import json
from collections import deque
from itertools import combinations

MOVES = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1)
}

# ----------------------------
# Load Puzzle Configuration
# ----------------------------

def load_puzzle_config(file_path="puzzle_config.json"):
    """Loads the puzzle configuration from JSON."""
    abs_path = os.path.abspath(file_path)
    print(f"Looking for puzzle config at: {abs_path}")
    if not os.path.exists(abs_path):
        print("Error: Puzzle configuration file not found!")
        return None
    with open(file_path, "r") as f:
        return json.load(f)

def board_to_tuple(pieces):
    """Converts board state (list of pieces) to a hashable tuple."""
    return tuple(sorted((p["label"], p["row"], p["col"]) for p in pieces))

# ----------------------------
# Generate Hyper-Nodes (Valid Unique Board Arrangements)
# ----------------------------

def generate_hypernodes(puzzle_data):
    """
    Generates all unique, valid hyper-nodes by placing movable pieces.
    Movable pieces are those with piece_type "1x2" or "2x1".
    Fixed pieces (any other type) are kept in place.
    """
    rows, cols = puzzle_data["rows"], puzzle_data["cols"]
    
    # Separate fixed vs. movable pieces
    fixed_pieces = [p for p in puzzle_data["pieces"] if p["piece_type"] not in {"1x2", "2x1"}]
    movable_pieces = [p for p in puzzle_data["pieces"] if p["piece_type"] in {"1x2", "2x1"}]
    
    num_1x2 = sum(1 for p in movable_pieces if p["piece_type"] == "1x2")
    num_2x1 = sum(1 for p in movable_pieces if p["piece_type"] == "2x1")
    
    # Generate valid placements
    placements_h = [((r, c), (r, c + 1)) for r in range(rows) for c in range(cols - 1)]
    placements_v = [((r, c), (r + 1, c)) for r in range(rows - 1) for c in range(cols)]
    
    valid_states = []
    seen_states = set()
    
    for chosen_h in combinations(placements_h, num_1x2):
        for chosen_v in combinations(placements_v, num_2x1):
            occupied = set()
            valid = True
            state = []
            
            # Place 1x2 pieces
            for placement in chosen_h:
                if placement[0] in occupied or placement[1] in occupied:
                    valid = False
                    break
                occupied.update(placement)
                state.append({"label": f"H1x2_{len(state)}", "row": placement[0][0], "col": placement[0][1], "piece_type": "1x2"})
            
            # Place 2x1 pieces
            for placement in chosen_v:
                if placement[0] in occupied or placement[1] in occupied:
                    valid = False
                    break
                occupied.update(placement)
                state.append({"label": f"H2x1_{len(state)}", "row": placement[0][0], "col": placement[0][1], "piece_type": "2x1"})
            
            if valid:
                state.extend(fixed_pieces)  # Keep fixed pieces in place
                state_tuple = board_to_tuple(state)
                if state_tuple not in seen_states:
                    seen_states.add(state_tuple)
                    valid_states.append(state)
    
    print(f"Total unique valid arrangements (Hyper-Nodes): {len(valid_states)}")
    return valid_states

# ----------------------------
# 📌 Generate Super-Nodes (Adding Extra Blocks)
# ----------------------------

def generate_supernodes(hyper_state, puzzle_data):
    """
    For a given hyper-node, generate valid super-nodes by placing extra 1x1 blocks.
    """
    rows, cols = puzzle_data["rows"], puzzle_data["cols"]
    total_cells = {(r, c) for r in range(rows) for c in range(cols)}
    occupied_cells = set()

    for piece in hyper_state:
        # Determine piece dimensions:
        if piece["piece_type"] == "1x1":
            height, width = 1, 1
        elif piece["piece_type"] == "1x2":
            height, width = 1, 2
        elif piece["piece_type"] == "2x1":
            height, width = 2, 1
        else:
            height, width = 1, 1
        for r in range(height):
            for c in range(width):
                occupied_cells.add((piece["row"] + r, piece["col"] + c))

    empty_spaces = list(total_cells - occupied_cells)
    super_states = []

    if len(empty_spaces) >= 4:
        for combo in combinations(empty_spaces, 4):
            new_state = [p.copy() for p in hyper_state]
            for idx, cell in enumerate(combo):
                new_state.append({"label": f"Block{idx+1}", "row": cell[0], "col": cell[1], "piece_type": "1x1"})
            super_states.append(new_state)
    
    return super_states

# ----------------------------
# 📌 Get All Possible Moves for a State
# ----------------------------

def get_all_possible_moves(pieces, rows, cols):
    """
    Returns a dictionary mapping each movable piece's label to a list of legal moves.
    Movable pieces are those with type "1x2" or "2x1".
    Fixed pieces (including extra blocks of type "1x1") are not moved.
    Each move is represented as (direction, new_row, new_col).
    """
    board = {}
    # First, populate the board with all pieces.
    for p in pieces:
        if p["piece_type"] == "1x2":
            h, w = 1, 2
        elif p["piece_type"] == "2x1":
            h, w = 2, 1
        else:  # For 1x1 (extra blocks or fixed pieces)
            h, w = 1, 1
        for r in range(h):
            for c in range(w):
                board[(p["row"] + r, p["col"] + c)] = p["label"]
    
    moves_dict = {}
    for p in pieces:
        # Only generate moves for movable pieces.
        if p["piece_type"] in {"1x2", "2x1"}:
            moves_dict[p["label"]] = []
            if p["piece_type"] == "1x2":
                h, w = 1, 2
            elif p["piece_type"] == "2x1":
                h, w = 2, 1
            for direction, (dr, dc) in MOVES.items():
                new_row = p["row"] + dr
                new_col = p["col"] + dc
                if new_row < 0 or new_col < 0 or new_row + h > rows or new_col + w > cols:
                    continue
                can_move = True
                for r in range(h):
                    for c in range(w):
                        cell = (new_row + r, new_col + c)
                        if cell in board and board[cell] != p["label"]:
                            can_move = False
                            break
                    if not can_move:
                        break
                if can_move:
                    moves_dict[p["label"]].append((direction, new_row, new_col))
        else:
            moves_dict[p["label"]] = []
    return moves_dict

# ----------------------------
# 📌 BFS to Find the Shortest Path to a Solution
# ----------------------------

def find_shortest_target_path_from_state(initial_pieces, puzzle_data):
    """
    Uses BFS to find the shortest sequence of moves that leads from the current state
    (list of pieces) to a solution state, where the target piece is at position (rows-1, 0).
    Returns the move sequence, or an empty list if no solution is found.
    """
    rows, cols = puzzle_data["rows"], puzzle_data["cols"]
    target_label = puzzle_data["target"]
    queue = deque()
    visited = set()
    
    # Ensure the target piece is present.
    try:
        _ = next(p for p in initial_pieces if p["label"] == target_label)
    except StopIteration:
        print(f"ERROR: Target piece '{target_label}' missing from state!")
        return []
    
    queue.append((initial_pieces, []))
    visited.add(board_to_tuple(initial_pieces))
    
    while queue:
        current_pieces, move_history = queue.popleft()
        target_piece = next(p for p in current_pieces if p["label"] == target_label)
        # Check if target piece is at (rows-1, 0)
        if target_piece["row"] == rows - 1 and target_piece["col"] == 0:
            return move_history
        
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
    
    print("WARNING: No BFS solution found for this super-node!")
    return []

# ----------------------------
# 📌 Generate and Save States
# ----------------------------

def main():
    puzzle_data = load_puzzle_config()
    if not puzzle_data:
        return

    hypernodes = []
    
    for idx, hyper_state in enumerate(generate_hypernodes(puzzle_data)):
        hypernode = {"label": f"H{idx}", "board_state": hyper_state, "supernodes": []}
        
        for j, super_state in enumerate(generate_supernodes(hyper_state, puzzle_data)):
            supernode = {"label": f"H{idx}_S{j}", "board_state": super_state, "bfs_solution": []}

            bfs_path = find_shortest_target_path_from_state(super_state, puzzle_data)
            if bfs_path:
                supernode["bfs_solution"] = [{"step": step_idx, "move": move} for step_idx, move in enumerate(bfs_path, start=1)]
            hypernode["supernodes"].append(supernode)
        
        hypernodes.append(hypernode)

    with open("states.json", "w") as f:
        json.dump({"center": "Start", "hypernodes": hypernodes}, f, indent=4)
    print("✅ States saved to states.json!")

if __name__ == "__main__":
    main()
    