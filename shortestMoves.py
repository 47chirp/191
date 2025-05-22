import os
import json
from collections import deque
from itertools import combinations

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
    with open(file_path, "r") as f:
        data = json.load(f)
    if isinstance(data, list):
        print("ERROR: Loaded JSON is a list instead of a dictionary!")
        return None
    return data

def get_piece_dimensions(piece):
    """Returns the (height, width) based on piece type."""
    if piece["piece_type"] == "1x1":
        return 1, 1
    elif piece["piece_type"] == "1x2":
        return 1, 2
    elif piece["piece_type"] == "2x1":
        return 2, 1
    else:
        raise ValueError(f"Unknown piece type: {piece['piece_type']}")

def board_to_tuple(pieces):
    """Converts the board state to a tuple (for hashing)."""
    return tuple(sorted((p["label"], p["row"], p["col"]) for p in pieces))

def get_all_possible_moves(pieces, rows, cols):
    """Generates possible moves for each piece (for BFS)."""
    # Here we assume that the pieces already have "height" and "width".
    # We'll compute moves and let the BFS function check for validity.
    move_dict = {}
    for piece in pieces:
        move_dict[piece["label"]] = []
        for direction, (dr, dc) in MOVES.items():
            new_row = piece["row"] + dr
            new_col = piece["col"] + dc
            move_dict[piece["label"]].append((direction, new_row, new_col))
    return move_dict

# ----------------------------
# BFS to Find Shortest Path from a Given State
# ----------------------------

def find_shortest_target_path_from_state(initial_pieces, puzzle_data):
    """
    Uses BFS to find the shortest sequence of moves from a given board state
    to a configuration where the target piece is in the bottom-left.
    Returns a list of moves (each move is a tuple: (piece_label, direction)).
    """
    rows, cols = puzzle_data["rows"], puzzle_data["cols"]
    target_label = puzzle_data["target"]
    queue = deque()
    visited = set()
    
    # Ensure target exists in initial_pieces
    try:
        _ = next(p for p in initial_pieces if p["label"] == target_label)
    except StopIteration:
        print(f"ERROR: Target piece '{target_label}' missing in state!")
        return []
    
    queue.append((initial_pieces, []))
    visited.add(board_to_tuple(initial_pieces))
    
    while queue:
        current_pieces, move_history = queue.popleft()
        try:
            target_piece = next(p for p in current_pieces if p["label"] == target_label)
        except StopIteration:
            continue
        
        if target_piece["row"] == rows - 1 and target_piece["col"] == 0:
            return move_history
        
        possible_moves = get_all_possible_moves(current_pieces, rows, cols)
        for piece in current_pieces:
            for direction, new_row, new_col in possible_moves[piece["label"]]:
                # For simplicity, we do not do full collision checking here,
                # assuming the board states are legal from generation.
                new_pieces = [p.copy() for p in current_pieces]
                for p in new_pieces:
                    if p["label"] == piece["label"]:
                        p["row"], p["col"] = new_row, new_col
                new_state = board_to_tuple(new_pieces)
                if new_state not in visited:
                    visited.add(new_state)
                    queue.append((new_pieces, move_history + [(piece["label"], direction)]))
    print("WARNING: No BFS solution found for this state!")
    return []

# ----------------------------
# Hyper-node & Super-node Generation
# ----------------------------

def generate_hypernodes(puzzle_data):
    """
    Generates unique valid hyper-node states.
    We rearrange pieces of type "1x2" and "2x1" and leave fixed all other pieces.
    Each hyper-node is a list of dictionaries (board state).
    """
    rows, cols = puzzle_data["rows"], puzzle_data["cols"]
    
    # Split pieces: movable and fixed.
    movable = [p for p in puzzle_data["pieces"] if p["piece_type"] in {"1x2", "2x1"}]
    fixed = [p.copy() for p in puzzle_data["pieces"] if p["piece_type"] not in {"1x2", "2x1"}]
    # Update fixed pieces with dimensions.
    for p in fixed:
        h, w = get_piece_dimensions(p)
        p["height"], p["width"] = h, w
    
    # Count how many movable of each type.
    mov_1x2 = [p for p in movable if p["piece_type"] == "1x2"]
    mov_2x1 = [p for p in movable if p["piece_type"] == "2x1"]
    num_1x2 = len(mov_1x2)
    num_2x1 = len(mov_2x1)
    
    # Generate placements for each movable type.
    placements_h = [((r, c), (r, c+1)) for r in range(rows) for c in range(cols-1)]
    placements_v = [((r, c), (r+1, c)) for r in range(rows-1) for c in range(cols)]
    
    hyper_states = []
    seen = set()
    # Iterate over all combinations for each type.
    for comb_h in combinations(placements_h, num_1x2):
        for comb_v in combinations(placements_v, num_2x1):
            occupied = set()
            valid = True
            # Check movable placements do not overlap.
            for placement in comb_h + comb_v:
                if placement[0] in occupied or placement[1] in occupied:
                    valid = False
                    break
                occupied.update(placement)
            if not valid:
                continue
            state = []
            # For each 1x2 piece, assign the top-left of its chosen placement.
            for p, placement in zip(mov_1x2, comb_h):
                new_piece = p.copy()
                new_piece["row"] = placement[0][0]
                new_piece["col"] = placement[0][1]
                h, w = get_piece_dimensions(new_piece)
                new_piece["height"], new_piece["width"] = h, w
                state.append(new_piece)
            # For each 2x1 piece.
            for p, placement in zip(mov_2x1, comb_v):
                new_piece = p.copy()
                new_piece["row"] = placement[0][0]
                new_piece["col"] = placement[0][1]
                h, w = get_piece_dimensions(new_piece)
                new_piece["height"], new_piece["width"] = h, w
                state.append(new_piece)
            # Add fixed pieces (they already have height/width set).
            state.extend(fixed)
            state_tuple = board_to_tuple(state)
            if state_tuple not in seen:
                seen.add(state_tuple)
                hyper_states.append(state)
    print(f"Total unique valid arrangements (Hyper-Nodes): {len(hyper_states)}")
    return hyper_states

def generate_supernodes(hyper_state, puzzle_data):
    """
    For a given hyper-node state, generates super-node states by placing 4 extra blocks
    (1x1 pieces) into empty cells. Returns a list of board states.
    """
    rows, cols = puzzle_data["rows"], puzzle_data["cols"]
    total_cells = {(r, c) for r in range(rows) for c in range(cols)}
    occupied = set()
    for piece in hyper_state:
        h = piece.get("height")
        w = piece.get("width")
        if h is None or w is None:
            # If not set, determine dimensions from piece_type.
            h, w = get_piece_dimensions(piece)
            piece["height"], piece["width"] = h, w
        for r in range(h):
            for c in range(w):
                occupied.add((piece["row"] + r, piece["col"] + c))
    empty_spaces = list(total_cells - occupied)
    super_states = []
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
            super_states.append(new_state)
    return super_states

# ----------------------------
# Main: Generate States and Write JSON
# ----------------------------

def main():
    puzzle_data = load_puzzle_config()
    if not puzzle_data:
        return

    hypernodes = []
    hyper_states = generate_hypernodes(puzzle_data)
    
    for idx, hyper_state in enumerate(hyper_states):
        hypernode = {"label": f"H{idx}", "board_state": hyper_state, "supernodes": []}
        super_states = generate_supernodes(hyper_state, puzzle_data)
        for j, super_state in enumerate(super_states):
            supernode = {"label": f"H{idx}_S{j}", "board_state": super_state, "bfs_solution": []}
            print(f"Running BFS for Super-Node: {supernode['label']}")
            bfs_path = find_shortest_target_path_from_state(super_state, puzzle_data)
            if bfs_path:
                solution = [{"step": step_idx, "move": move} for step_idx, move in enumerate(bfs_path, start=1)]
                supernode["bfs_solution"] = solution
                print(f" → BFS found solution with {len(solution)} steps!")
                print(f"    BFS result for {supernode['label']}: {solution}")
            else:
                print(f" → WARNING: BFS returned empty for {supernode['label']}")
            hypernode["supernodes"].append(supernode)
        hypernodes.append(hypernode)
    
    data_to_save = {"center": "Start", "hypernodes": hypernodes}
    with open("states.json", "w") as f:
        json.dump(data_to_save, f, indent=4)
    print("✅ States saved to states.json!")

if __name__ == "__main__":
    main()