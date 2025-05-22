'''
This file finds the shortest path to move the target piece to the bottom-left corner,
simulates each move, and saves images that closely mimic the Tkinter UI (150x150 cells,
skyblue pieces, target in gold, Arial labels) in the "beamerTest1" folder.
'''

import os
import json
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# Constants matching the Tkinter UI
CELL_SIZE = 150  # Each grid cell is 150x150 pixels
FONT_SIZE = 24   # Base font size to match UI
DPI = 150        # DPI for the saved image

MOVES = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1)
}

# ----------------------------
# Puzzle Configuration Functions
# ----------------------------

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
    if piece["piece_type"] == "1x1":
        return 1, 1
    elif piece["piece_type"] == "1x2":
        return 1, 2
    elif piece["piece_type"] == "2x1":
        return 2, 1
    elif piece["piece_type"] == "2x2":
        return 2, 2
    else:
        raise ValueError(f"Unknown piece type: {piece['piece_type']}")

def create_board_representation(pieces):
    """Creates a board representation with occupied positions."""
    board = {}
    for piece in pieces:
        height, width = get_piece_dimensions(piece)
        piece["height"], piece["width"] = height, width  # Store for later use
        for r in range(height):
            for c in range(width):
                board[(piece["row"] + r, piece["col"] + c)] = piece["label"]
    return board

def is_valid_move(piece, new_row, new_col, board, rows, cols):
    """Checks if a move to (new_row, new_col) is valid (in bounds and without collisions)."""
    height, width = piece["height"], piece["width"]
    if new_row < 0 or new_col < 0 or new_row + height > rows or new_col + width > cols:
        return False
    new_cells = {(new_row + r, new_col + c) for r in range(height) for c in range(width)}
    for cell in new_cells:
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
    """Converts the board state to a tuple for hashing (used in visited states)."""
    return tuple(sorted((p["label"], p["row"], p["col"]) for p in pieces))

# ----------------------------
# BFS for Shortest Path
# ----------------------------

def find_shortest_target_path(puzzle_data):
    """
    Uses BFS to find the shortest sequence of moves that leads from the initial state
    to a configuration where the target piece ends in the bottom-left corner.
    Returns the move history as a list of (piece_label, direction) tuples.
    """
    rows, cols = puzzle_data["rows"], puzzle_data["cols"]
    initial_pieces = puzzle_data["pieces"]
    target_label = puzzle_data["target"]

    queue = deque()
    visited = set()
    queue.append((initial_pieces, []))
    visited.add(board_to_tuple(initial_pieces))

    while queue:
        current_pieces, move_history = queue.popleft()
        target_piece = next(p for p in current_pieces if p["label"] == target_label)
        target_height, _ = get_piece_dimensions(target_piece)
        # Check if target piece is at the bottom-left (adjust for its height)
        if target_piece["row"] == rows - target_height and target_piece["col"] == 0:
            return move_history
        possible_moves = get_all_possible_moves(current_pieces, rows, cols)
        for piece in current_pieces:
            for direction, new_row, new_col in possible_moves[piece["label"]]:
                new_pieces = [p.copy() for p in current_pieces]
                for np in new_pieces:
                    if np["label"] == piece["label"]:
                        np["row"], np["col"] = new_row, new_col
                new_state = board_to_tuple(new_pieces)
                if new_state not in visited:
                    visited.add(new_state)
                    queue.append((new_pieces, move_history + [(piece["label"], direction)]))
    return []  # No solution found

# ----------------------------
# Image Generation Functions (Mimicking Tkinter UI)
# ----------------------------

def grid_to_canvas(row, col):
    """Converts grid cell (row, col) to canvas (x, y) coordinates."""
    return col * CELL_SIZE, row * CELL_SIZE

def save_board_image(pieces, puzzle_data, filepath):
    """
    Draws the current board state and saves it as an image that mimics the Tkinter UI.
    Each cell is 150x150 pixels; pieces are drawn with "skyblue" fill (or "gold" for target)
    with a 2px black outline, and labels are centered using Arial (slightly smaller than FONT_SIZE)
    in white. The grid is drawn first (with light gray, thin lines), and then the pieces are drawn
    on top so that 1x2 and 2x1 blocks appear to stick out over the grid.
    """
    rows, cols = puzzle_data["rows"], puzzle_data["cols"]
    width_pixels = cols * CELL_SIZE
    height_pixels = rows * CELL_SIZE
    figsize = (width_pixels / DPI, height_pixels / DPI)
    
    # Ensure matplotlib uses Arial (if available)
    plt.rcParams["font.family"] = "Arial"
    
    fig, ax = plt.subplots(figsize=figsize, dpi=DPI)
    
    # Draw grid lines in light gray and with thinner lines.
    for r in range(rows + 1):
        y = r * CELL_SIZE
        ax.plot([0, width_pixels], [y, y], color='lightgray', linewidth=0.5, zorder=1)
    for c in range(cols + 1):
        x = c * CELL_SIZE
        ax.plot([x, x], [0, height_pixels], color='lightgray', linewidth=0.5, zorder=1)
    
    # Draw each piece with a higher zorder so they appear on top of the grid.
    for piece in pieces:
        height, width = get_piece_dimensions(piece)
        x0, y0 = grid_to_canvas(piece["row"], piece["col"])
        x1, y1 = grid_to_canvas(piece["row"] + height, piece["col"] + width)
        rect = Rectangle((x0, y0), x1 - x0, y1 - y0,
                         edgecolor='black',
                         facecolor=("gold" if piece["label"] == puzzle_data["target"] else "skyblue"),
                         linewidth=2,
                         zorder=2)
        ax.add_patch(rect)
        cx = (x0 + x1) / 2
        cy = (y0 + y1) / 2
        ax.text(cx, cy, piece["label"], ha='center', va='center',
                fontsize=FONT_SIZE - 4, color="white", zorder=3)
    
    ax.set_xlim(0, width_pixels)
    ax.set_ylim(height_pixels, 0)  # Invert y-axis to match top-left origin
    ax.axis('off')
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.savefig(filepath, bbox_inches='tight', pad_inches=0)
    plt.close(fig)

def simulate_shortest_path_and_save_images(puzzle_data, shortest_path, folder="beamerTest1"):
    """
    Simulates the moves in the shortest path and saves an image after each move.
    Images are saved in the specified folder.
    """
    if not os.path.exists(folder):
        os.makedirs(folder)

    current_pieces = [p.copy() for p in puzzle_data["pieces"]]
    image_files = []
    
    # Save the initial state.
    image_path = os.path.join(folder, "move_0.png")
    save_board_image(current_pieces, puzzle_data, image_path)
    image_files.append(image_path)
    
    step = 1
    for move in shortest_path:
        piece_label, direction = move
        dr, dc = MOVES[direction]
        for piece in current_pieces:
            if piece["label"] == piece_label:
                piece["row"] += dr
                piece["col"] += dc
                break
        image_path = os.path.join(folder, f"move_{step}.png")
        save_board_image(current_pieces, puzzle_data, image_path)
        image_files.append(image_path)
        step += 1

    return image_files

# ----------------------------
# Main Execution
# ----------------------------

def main():
    puzzle_data = load_puzzle_config()
    if not puzzle_data:
        return

    shortest_path = find_shortest_target_path(puzzle_data)
    if shortest_path:
        print("\n=== Shortest Path for Target Piece ===")
        print(shortest_path)
    else:
        print("\nNo valid path found for the target piece.")
        return

    image_files = simulate_shortest_path_and_save_images(puzzle_data, shortest_path, folder="beamerTest1")
    
    print("\nImages saved in the 'beamerTest1' folder:")
    for img in image_files:
        print(img)

if __name__ == "__main__":
    main()