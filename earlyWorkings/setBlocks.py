'''
I have a ui pop up with the 3x4 dimension of the board. 
On the lefthand side is potential blocks, 1x1, 2x1, and 1x2. 
I can drag these into the board and then hit save to save the board state to then work on after.
'''

import tkinter as tk
from tkinter import messagebox
import json

CELL_SIZE = 150       # Pixel size per grid cell
ROWS, COLS = 3, 4     # Board dimensions

def grid_to_canvas(row, col):
    """Return the canvas coordinates of the top-left of cell (row, col)."""
    return col * CELL_SIZE, row * CELL_SIZE

class Piece:
    def __init__(self, label, piece_type, canvas, board_ui, init_pos=(0,0)):
        """
        label: Unique letter for this piece (e.g., 'a', 'b', etc.)
        piece_type: "1x1", "1x2", or "2x1"
        """
        self.label = label
        self.piece_type = piece_type
        self.canvas = canvas
        self.board_ui = board_ui

        # Set dimensions
        if piece_type == "1x1":
            self.rows, self.cols = 1, 1
        elif piece_type == "1x2":
            self.rows, self.cols = 1, 2
        elif piece_type == "2x1":
            self.rows, self.cols = 2, 1
        else:
            raise ValueError("Unknown piece type: " + piece_type)

        self.row, self.col = init_pos  # Current grid position
        self.last_valid_pos = (self.row, self.col)  # For reverting if drop is invalid

        # Create the rectangle and text
        x0, y0 = grid_to_canvas(self.row, self.col)
        x1, y1 = grid_to_canvas(self.row + self.rows, self.col + self.cols)
        self.item = canvas.create_rectangle(x0, y0, x1, y1,
                                            fill="skyblue", outline="black", width=2)
        self.text = canvas.create_text((x0+x1)//2, (y0+y1)//2,
                                       text=self.label, font=("Arial", 12))
        self.bind_events()

        self._drag_data = {"x": 0, "y": 0}

    def bind_events(self):
        for tag in (self.item, self.text):
            self.canvas.tag_bind(tag, "<ButtonPress-1>", self.on_start)
            self.canvas.tag_bind(tag, "<B1-Motion>", self.on_drag)
            self.canvas.tag_bind(tag, "<ButtonRelease-1>", self.on_drop)

    def on_start(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
        self.last_valid_pos = (self.row, self.col)

    def on_drag(self, event):
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
        self.canvas.move(self.item, dx, dy)
        self.canvas.move(self.text, dx, dy)

    def on_drop(self, event):
        coords = self.canvas.coords(self.item)  # [x0, y0, x1, y1]
        x0, y0 = coords[0], coords[1]
        candidate_col = int(x0 // CELL_SIZE)
        candidate_row = int(y0 // CELL_SIZE)
        candidate_row = max(0, min(candidate_row, ROWS - self.rows))
        candidate_col = max(0, min(candidate_col, COLS - self.cols))
        if self.board_ui.is_free(self, candidate_row, candidate_col):
            self.set_position(candidate_row, candidate_col)
            self.last_valid_pos = (candidate_row, candidate_col)
        else:
            old_row, old_col = self.last_valid_pos
            self.set_position(old_row, old_col)
            messagebox.showinfo("Invalid Drop", "That cell is already occupied.")
        self.board_ui.update_board()

    def set_position(self, row, col):
        self.row, self.col = row, col
        x0, y0 = grid_to_canvas(row, col)
        x1, y1 = grid_to_canvas(row + self.rows, col + self.cols)
        self.canvas.coords(self.item, x0, y0, x1, y1)
        self.canvas.coords(self.text, (x0+x1)//2, (y0+y1)//2)

    def occupied_cells(self):
        return {(self.row + r, self.col + c) for r in range(self.rows)
                                       for c in range(self.cols)}

class TargetStar:
    def __init__(self, canvas, board_ui, init_pos=(CELL_SIZE, CELL_SIZE)):
        self.canvas = canvas
        self.board_ui = board_ui
        self.item = canvas.create_text(init_pos[0], init_pos[1],
                                       text="★", font=("Arial", 24), fill="orange")
        self._drag_data = {"x": 0, "y": 0}
        self.bind_events()

    def bind_events(self):
        self.canvas.tag_bind(self.item, "<ButtonPress-1>", self.on_start)
        self.canvas.tag_bind(self.item, "<B1-Motion>", self.on_drag)
        self.canvas.tag_bind(self.item, "<ButtonRelease-1>", self.on_drop)

    def on_start(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def on_drag(self, event):
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
        self.canvas.move(self.item, dx, dy)

    def on_drop(self, event):
        bbox = self.canvas.bbox(self.item)
        center_x = (bbox[0] + bbox[2]) / 2
        center_y = (bbox[1] + bbox[3]) / 2
        target_piece = None
        for piece in self.board_ui.pieces:
            x0, y0 = grid_to_canvas(piece.row, piece.col)
            x1, y1 = grid_to_canvas(piece.row + piece.rows, piece.col + piece.cols)
            if x0 <= center_x <= x1 and y0 <= center_y <= y1:
                target_piece = piece
                break
        if target_piece:
            self.board_ui.set_target_piece(target_piece)
        self.canvas.delete(self.item)
        self.board_ui.target_star = None

class BoardUI:
    def __init__(self, root):
        self.root = root
        self.pieces = []
        self.target_piece = None
        self.target_star = None
        self.next_label_index = 0  # For unique letters: 0 -> 'a', 1 -> 'b', etc.

        # Left panel: Palette and controls.
        self.left_frame = tk.Frame(root)
        self.left_frame.pack(side=tk.LEFT, padx=10, pady=10, fill="y")
        tk.Label(self.left_frame, text="Palette").pack(pady=5)
        tk.Button(self.left_frame, text="Drag 1x1",
                  command=lambda: self.add_piece("1x1")).pack(fill="x", pady=2)
        tk.Button(self.left_frame, text="Drag 1x2",
                  command=lambda: self.add_piece("1x2")).pack(fill="x", pady=2)
        tk.Button(self.left_frame, text="Drag 2x1",
                  command=lambda: self.add_piece("2x1")).pack(fill="x", pady=2)
        tk.Button(self.left_frame, text="Set Target",
                  command=self.start_drag_target).pack(pady=10, fill="x")
        tk.Button(self.left_frame, text="SAVE",
                  command=self.save_configuration).pack(pady=10, fill="x")

        # Right panel: Board canvas with grid outlines.
        self.canvas = tk.Canvas(root, bg="white")
        self.canvas.pack(side=tk.RIGHT, padx=10, pady=10, fill="both", expand=True)
        self.draw_grid()
        self.update_board()

    def draw_grid(self):
        self.canvas.delete("grid")  # Remove previous grid lines.
        for r in range(ROWS):
            for c in range(COLS):
                x0, y0 = grid_to_canvas(r, c)
                x1, y1 = grid_to_canvas(r+1, c+1)
                self.canvas.create_rectangle(x0, y0, x1, y1,
                                               outline="gray", fill="white", tags="grid")

    def update_board(self):
        self.board = {}
        for piece in self.pieces:
            for cell in piece.occupied_cells():
                self.board[cell] = piece

    def is_free(self, moving_piece, row, col):
        new_cells = {(row + r, col + c) for r in range(moving_piece.rows)
                                       for c in range(moving_piece.cols)}
        for cell in new_cells:
            occupant = self.board.get(cell)
            if occupant and occupant != moving_piece:
                return False
        return True

    def add_piece(self, piece_type):
        label_char = chr(ord('a') + self.next_label_index)
        self.next_label_index += 1
        new_piece = Piece(label_char, piece_type, self.canvas, self, init_pos=(0,0))
        self.pieces.append(new_piece)
        self.update_board()

    def start_drag_target(self):
        if self.target_star is not None:
            return
        init_x = (COLS//2)*CELL_SIZE
        init_y = (ROWS//2)*CELL_SIZE
        self.target_star = TargetStar(self.canvas, self, init_pos=(init_x, init_y))

    def set_target_piece(self, piece):
        if self.target_piece and self.target_piece != piece:
            self.canvas.itemconfig(self.target_piece.item, fill="skyblue")
        self.target_piece = piece
        self.canvas.itemconfig(piece.item, fill="gold")

    def save_configuration(self):
        grid = [["_"] * COLS for _ in range(ROWS)]
        for piece in self.pieces:
            for (r, c) in piece.occupied_cells():
                grid[r][c] = piece.label
        config = json.dumps(grid, indent=4)
        messagebox.showinfo("Puzzle Configuration", config)
        with open("puzzle_config.json", "w") as f:
            f.write(config)

if __name__ == '__main__':
    root = tk.Tk()
    root.title("3x4 Puzzle Setup & Save")
    # Set an initial window size and allow resizing.
    root.geometry("800x600")
    # Allow the main window to expand its grid.
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)
    board_ui = BoardUI(root)
    root.mainloop()