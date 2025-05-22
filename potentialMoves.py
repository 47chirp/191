'''
This file will contain the functions that will be used to find all possible moves for each piece in the puzzle,
'''

import os
import json
from collections import deque

MOVES = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1)
}

# we take our puzzle configuration and we want to find all possible moves for each piece
def load_puzzle_config(file_path="puzzle_config.json"):
    """Loads the puzzle configuration from JSON."""
    abs_path = os.path.abspath(file_path)
    print(f"Looking for puzzle config at: {abs_path}")  # Debugging output

    if not os.path.exists(abs_path):
        print("Error: Puzzle configuration file not found!")
        return None

    with open(abs_path, "r") as f:
        data = json.load(f)

    if isinstance(data, list):
        print("ERROR: Loaded JSON is a list instead of a dictionary!")
        print("Check your puzzle_config.json formatting.")
        return None
    
    return data

# we want to find all possible moves for each piece in the puzzle
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

# we want to create a board representation with occupied positions
def create_board_representation(pieces):
    """Creates a board representation with occupied positions."""
    board = {}
    for piece in pieces:
        height, width = get_piece_dimensions(piece)
        piece["height"], piece["width"] = height, width  # Store size
        for r in range(height):
            for c in range(width):
                board[(piece["row"] + r, piece["col"] + c)] = piece["label"]
    return board

# we want to check if a move is valid
def is_valid_move(piece, new_row, new_col, board, rows, cols):
    """Checks if a move to (new_row, new_col) is valid without collisions."""
    height, width = piece["height"], piece["width"]

    # Check board boundaries
    if new_row < 0 or new_col < 0 or new_row + height > rows or new_col + width > cols:
        return False

    # Check for collision with other pieces
    new_cells = {(new_row + r, new_col + c) for r in range(height) for c in range(width)}
    for cell in new_cells:
        if cell in board and board[cell] != piece["label"]:
            return False  # Collision detected

    return True

# we want to find all possible moves for each piece in the puzzle
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

# we want to convert the board state to a tuple for hashing
def board_to_tuple(pieces):
    """Converts the board state to a tuple for hashing (used in visited states)."""
    return tuple(sorted((p["label"], p["row"], p["col"]) for p in pieces))

# we want to use BFS to find all valid board configurations
def BFS(puzzle_data):
    """Uses BFS to find all valid board configurations."""
    rows, cols = puzzle_data["rows"], puzzle_data["cols"]
    initial_pieces = puzzle_data["pieces"]

    queue = deque()
    visited = set()

    # Start with the initial state
    queue.append(initial_pieces)
    visited.add(board_to_tuple(initial_pieces))

    total_configurations = 0

    while queue:
        current_pieces = queue.popleft()
        total_configurations += 1  # Count valid configurations

        # Get all possible moves from the current configuration
        possible_moves = get_all_possible_moves(current_pieces, rows, cols)

        for piece in current_pieces:
            for direction, new_row, new_col in possible_moves[piece["label"]]:
                # Generate new board state by moving this piece
                new_pieces = [p.copy() for p in current_pieces]
                for p in new_pieces:
                    if p["label"] == piece["label"]:
                        p["row"], p["col"] = new_row, new_col

                new_state = board_to_tuple(new_pieces)
                if new_state not in visited:
                    visited.add(new_state)
                    queue.append(new_pieces)

    return total_configurations

# want to make another function that will find all configurations that lead to the starred piece ending in the bottom left
def find_target_piece_paths(puzzle_data):
    """Finds all configurations where the target piece ends in the bottom-left."""
    rows, cols = puzzle_data["rows"], puzzle_data["cols"]
    initial_pieces = puzzle_data["pieces"]
    target_label = puzzle_data["target"]

    queue = deque()
    visited = set()
    valid_end_states = []

    # Start with the initial state
    queue.append((initial_pieces, []))  # Store move history
    visited.add(board_to_tuple(initial_pieces))

    while queue:
        current_pieces, move_history = queue.popleft()

        # Get reference to target piece
        target_piece = next(p for p in current_pieces if p["label"] == target_label)

        # Check if target piece is in bottom-left corner
        if target_piece["row"] == rows - 1 and target_piece["col"] == 0:
            valid_end_states.append((current_pieces, move_history))
            continue  # No need to explore further from this state

        # Get all possible moves
        possible_moves = get_all_possible_moves(current_pieces, rows, cols)

        for piece in current_pieces:
            for direction, new_row, new_col in possible_moves[piece["label"]]:
                # Generate new board state by moving this piece
                new_pieces = [p.copy() for p in current_pieces]
                for p in new_pieces:
                    if p["label"] == piece["label"]:
                        p["row"], p["col"] = new_row, new_col

                new_state = board_to_tuple(new_pieces)
                if new_state not in visited:
                    visited.add(new_state)
                    queue.append((new_pieces, move_history + [(piece["label"], direction)]))

    return valid_end_states

# Modify main() to use find_target_piece_paths
def main():
    puzzle_data = load_puzzle_config()
    if not puzzle_data:
        return

    move_dict = get_all_possible_moves(puzzle_data["pieces"], puzzle_data["rows"], puzzle_data["cols"])
    
    # Print out all possible moves
    print("\n=== Possible Moves ===")
    for piece, moves in move_dict.items():
        print(f"Piece {piece} can move: {[m[0] for m in moves]}")

    # Find all unique board configurations using BFS
    total_configurations = BFS(puzzle_data)
    print(f"\nTotal unique valid board configurations: {total_configurations}")

    # Find paths where the target piece ends in the bottom-left
    valid_paths = find_target_piece_paths(puzzle_data)
    print(f"\nTotal valid configurations where '{puzzle_data['target']}' ends in bottom-left: {len(valid_paths)}")

    for i, (config, moves) in enumerate(valid_paths):
        print(f"\nPath {i+1}: {moves}")

if __name__ == "__main__":
    main()