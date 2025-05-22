import tkinter as tk
from tkinter import messagebox, simpledialog, Toplevel, Listbox, END
import time
import json
import os
from PIL import Image  # Pillow is required

CELL_SIZE = 150  # Each grid cell is 150x150 pixels
PRESETS_FILE = "presets.json"  # File to store presets

def grid_to_canvas(row, col):
    """Return canvas (x,y) coordinates for the top-left of cell (row, col)."""
    return col * CELL_SIZE, row * CELL_SIZE

# ---------------------------
# Piece class (Setup & Solve)
# ---------------------------
class Piece:
    def __init__(self, label, piece_type, canvas, app, init_pos=(0,0)):
        """
        label: Unique letter (e.g., 'a', 'b', …)
        piece_type: "1x1", "1x2", or "2x1" (defines dimensions)
        canvas: Tkinter Canvas on which the piece is drawn
        app: Reference to the main PuzzleApp
        init_pos: (row, col) grid position (row 0 is top in Setup Mode)
        """
        self.label = label
        self.piece_type = piece_type
        self.canvas = canvas
        self.app = app

        # Determine dimensions from piece_type.
        if piece_type == "1x1":
            self.height, self.width = 1, 1
        elif piece_type == "1x2":
            self.height, self.width = 1, 2
        elif piece_type == "2x1":
            self.height, self.width = 2, 1
        elif piece_type == "2x2":
            self.height, self.width = 2, 2
        else:
            raise ValueError("Unknown piece type: " + piece_type)


        self.row, self.col = init_pos
        self.last_valid_pos = (self.row, self.col)
        x0, y0 = grid_to_canvas(self.row, self.col)
        x1, y1 = grid_to_canvas(self.row + self.height, self.col + self.width)
        self.item = canvas.create_rectangle(x0, y0, x1, y1,
                                            fill="skyblue", outline="black", width=2)
        self.text = canvas.create_text((x0+x1)//2, (y0+y1)//2,
                                       text=self.label, font=("Arial", 24))
        self.bind_setup_events()
        self._drag_data = {"x": 0, "y": 0}

    def bind_setup_events(self):
        for tag in (self.item, self.text):
            self.canvas.tag_bind(tag, "<ButtonPress-1>", self.on_start)
            self.canvas.tag_bind(tag, "<B1-Motion>", self.on_drag)
            self.canvas.tag_bind(tag, "<ButtonRelease-1>", self.on_drop)

    def unbind_setup_events(self):
        for tag in (self.item, self.text):
            self.canvas.tag_unbind(tag, "<ButtonPress-1>")
            self.canvas.tag_unbind(tag, "<B1-Motion>")
            self.canvas.tag_unbind(tag, "<ButtonRelease-1>")

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
        candidate_row = max(0, min(candidate_row, self.app.setup_rows - self.height))
        candidate_col = max(0, min(candidate_col, self.app.setup_cols - self.width))
        if self.app.is_free(self, candidate_row, candidate_col):
            self.set_position(candidate_row, candidate_col)
            self.last_valid_pos = (candidate_row, candidate_col)
        else:
            old_row, old_col = self.last_valid_pos
            self.set_position(old_row, old_col)
            messagebox.showinfo("Invalid Drop", "That cell is occupied!")
        self.app.update_setup_board()

    def set_position(self, row, col):
        self.row, self.col = row, col
        x0, y0 = grid_to_canvas(row, col)
        x1, y1 = grid_to_canvas(row + self.height, col + self.width)
        self.canvas.coords(self.item, x0, y0, x1, y1)
        self.canvas.coords(self.text, (x0+x1)//2, (y0+y1)//2)

    def occupied_cells(self):
        return {(self.row + r, self.col + c) for r in range(self.height) for c in range(self.width)}

# ---------------------------
# TargetStar class (for setting target piece)
# ---------------------------
class TargetStar:
    def __init__(self, canvas, app, init_pos=(CELL_SIZE, CELL_SIZE)):
        self.canvas = canvas
        self.app = app
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
        target = None
        for piece in self.app.pieces:
            x0, y0 = grid_to_canvas(piece.row, piece.col)
            x1, y1 = grid_to_canvas(piece.row + piece.height, piece.col + piece.width)
            if x0 <= center_x <= x1 and y0 <= center_y <= y1:
                target = piece
                break
        if target:
            self.app.set_target_piece(target)
        self.canvas.delete(self.item)
        self.app.target_star = None

# ---------------------------
# Main Application Class (Setup & Solve)
# ---------------------------
class PuzzleApp:
    def __init__(self, root):
        self.root = root
        self.mode = "setup"  # "setup" or "solve"
        self.setup_rows = 3
        self.setup_cols = 4
        self.solve_rows = self.setup_rows
        self.solve_cols = self.setup_cols

        self.pieces = []         # List of Piece objects
        self.next_label_index = 0
        self.target_piece = None # The target piece
        self.selected_piece = None  # Currently selected piece in Solve Mode
        self.move_count = 0
        self.best_time = None
        self.start_time = None
        self.timer_id = None

        self.create_setup_ui()

    def create_setup_ui(self):
        # Top frame: board size entries and control buttons.
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(top_frame, text="Rows:").pack(side="left")
        self.rows_entry = tk.Entry(top_frame, width=3)
        self.rows_entry.insert(0, str(self.setup_rows))
        self.rows_entry.pack(side="left", padx=5)
        tk.Label(top_frame, text="Cols:").pack(side="left")
        self.cols_entry = tk.Entry(top_frame, width=3)
        self.cols_entry.insert(0, str(self.setup_cols))
        self.cols_entry.pack(side="left", padx=5)
        tk.Button(top_frame, text="Set Board Size", command=self.set_board_size).pack(side="right", padx=5)
        tk.Button(top_frame, text="LOCK BOARD", command=self.lock_board).pack(side="right", padx=5)
        tk.Button(top_frame, text="Set Target", command=self.start_drag_target).pack(side="right", padx=5)

        # Left frame: Palette and preset buttons.
        self.palette_frame = tk.Frame(self.root)
        self.palette_frame.pack(side="left", padx=10, pady=10, fill="y")
        tk.Label(self.palette_frame, text="Palette").pack(pady=5)
        tk.Button(self.palette_frame, text="Add 1x1", command=lambda: self.add_piece("1x1")).pack(fill="x", pady=2)
        tk.Button(self.palette_frame, text="Add 1x2", command=lambda: self.add_piece("1x2")).pack(fill="x", pady=2)
        tk.Button(self.palette_frame, text="Add 2x1", command=lambda: self.add_piece("2x1")).pack(fill="x", pady=2)
        tk.Button(self.palette_frame, text="Add 2x2", command=lambda: self.add_piece("2x2")).pack(fill="x", pady=2)
        tk.Button(self.palette_frame, text="Delete Piece", command=self.delete_piece_mode).pack(fill="x", pady=2)
        tk.Button(self.palette_frame, text="Save as Preset", command=self.save_as_preset).pack(fill="x", pady=2)
        tk.Button(self.palette_frame, text="Load Preset", command=self.load_preset).pack(fill="x", pady=2)
        tk.Button(self.palette_frame, text="SAVE", command=self.save_configuration).pack(pady=10, fill="x")
        tk.Button(self.palette_frame, text="Capture Board", command=self.capture_board).pack(pady=10, fill="x")

        # Right frame: Board canvas.
        self.canvas = tk.Canvas(self.root, width=self.setup_cols*CELL_SIZE,
                                  height=self.setup_rows*CELL_SIZE, bg="white")
        self.canvas.pack(side="right", padx=10, pady=10)
        self.draw_setup_grid()
        self.update_setup_board()

    def set_board_size(self):
        try:
            new_rows = int(self.rows_entry.get())
            new_cols = int(self.cols_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid board dimensions.")
            return
        self.setup_rows = new_rows
        self.setup_cols = new_cols
        self.canvas.config(width=self.setup_cols*CELL_SIZE, height=self.setup_rows*CELL_SIZE)
        self.draw_setup_grid()
        self.update_setup_board()

    def draw_setup_grid(self):
        self.canvas.delete("grid")
        for r in range(self.setup_rows):
            for c in range(self.setup_cols):
                x0, y0 = grid_to_canvas(r, c)
                x1, y1 = grid_to_canvas(r+1, c+1)
                self.canvas.create_rectangle(x0, y0, x1, y1, outline="gray", tags="grid")

    def update_setup_board(self):
        self.setup_board = {}
        for piece in self.pieces:
            for cell in piece.occupied_cells():
                self.setup_board[cell] = piece

    def is_free(self, moving_piece, row, col):
        new_cells = {(row+r, col+c) for r in range(moving_piece.height) for c in range(moving_piece.width)}
        for cell in new_cells:
            occupant = self.setup_board.get(cell)
            if occupant and occupant != moving_piece:
                return False
        return True

    def add_piece(self, piece_type):
        label = chr(ord('a') + self.next_label_index)
        self.next_label_index += 1
        new_piece = Piece(label, piece_type, self.canvas, self, init_pos=(0,0))
        self.pieces.append(new_piece)
        self.update_setup_board()

    def delete_piece_mode(self):
        messagebox.showinfo("Delete Mode", "Click on a piece to delete it.")
        self.canvas.bind("<Button-1>", self.delete_piece_click)

    def delete_piece_click(self, event):
        col = event.x // CELL_SIZE
        row = event.y // CELL_SIZE
        to_delete = None
        for piece in self.pieces:
            if (piece.row <= row < piece.row + piece.height and
                piece.col <= col < piece.col + piece.width):
                to_delete = piece
                break
        if to_delete:
            self.canvas.delete(to_delete.item)
            self.canvas.delete(to_delete.text)
            self.pieces.remove(to_delete)
            self.update_setup_board()
            messagebox.showinfo("Deleted", f"Piece {to_delete.label} deleted.")
        self.canvas.unbind("<Button-1>")
        self.canvas.bind("<Button-1>", lambda e: None)

    def save_as_preset(self):
        preset_name = simpledialog.askstring("Save Preset", "Enter a name for this preset:")
        if not preset_name:
            return
        preset = {
            "name": preset_name,
            "rows": self.setup_rows,
            "cols": self.setup_cols,
            "pieces": []
        }
        if self.target_piece:
            preset["target"] = self.target_piece.label
        for p in self.pieces:
            preset["pieces"].append({
                "label": p.label,
                "piece_type": p.piece_type,
                "row": p.row,
                "col": p.col
            })
        presets = {}
        if os.path.exists(PRESETS_FILE):
            with open(PRESETS_FILE, "r") as f:
                try:
                    presets = json.load(f)
                except:
                    presets = {}
        presets[preset_name] = preset
        with open(PRESETS_FILE, "w") as f:
            json.dump(presets, f, indent=4)
        messagebox.showinfo("Preset Saved", f"Preset '{preset_name}' saved.")

    def load_preset(self):
        if not os.path.exists(PRESETS_FILE):
            messagebox.showerror("Error", "No presets saved yet.")
            return
        with open(PRESETS_FILE, "r") as f:
            try:
                presets = json.load(f)
            except:
                messagebox.showerror("Error", "Error reading presets file.")
                return
        if not presets:
            messagebox.showerror("Error", "No presets saved yet.")
            return
        win = Toplevel(self.root)
        win.title("Load Preset")
        lb = Listbox(win, width=40, height=10)
        lb.pack(padx=10, pady=10)
        for name in presets.keys():
            lb.insert(END, name)
        def load_selected():
            selection = lb.curselection()
            if not selection:
                return
            name = lb.get(selection[0])
            preset = presets[name]
            self.setup_rows = preset["rows"]
            self.setup_cols = preset["cols"]
            self.rows_entry.delete(0, END)
            self.rows_entry.insert(0, str(self.setup_rows))
            self.cols_entry.delete(0, END)
            self.cols_entry.insert(0, str(self.setup_cols))
            self.canvas.config(width=self.setup_cols*CELL_SIZE, height=self.setup_rows*CELL_SIZE)
            self.draw_setup_grid()
            for p in self.pieces:
                self.canvas.delete(p.item)
                self.canvas.delete(p.text)
            self.pieces = []
            self.next_label_index = 0
            for p in preset["pieces"]:
                new_piece = Piece(p["label"], p["piece_type"], self.canvas, self, init_pos=(p["row"], p["col"]))
                self.pieces.append(new_piece)
                self.next_label_index = max(self.next_label_index, ord(p["label"]) - ord('a') + 1)
            if "target" in preset:
                for p in self.pieces:
                    if p.label == preset["target"]:
                        self.set_target_piece(p)
                        break
            self.update_setup_board()
            win.destroy()
            messagebox.showinfo("Preset Loaded", f"Preset '{name}' loaded.")
        tk.Button(win, text="Load", command=load_selected).pack(pady=5)
        
    def save_configuration(self):
        puzzle_data = {
            "rows": self.setup_rows,
            "cols": self.setup_cols,
            "pieces": [
                {"label": p.label, "piece_type": p.piece_type, "row": p.row, "col": p.col}
                for p in self.pieces
            ],
            "target": self.target_piece.label if self.target_piece else None
        }
        config_json = json.dumps(puzzle_data, indent=4)
        with open("puzzle_config.json", "w") as f:
            f.write(config_json)
        # Show a brief confirmation instead of the full config.
        messagebox.showinfo("Configuration Saved", "Puzzle saved to puzzle_config.json!")

    def start_drag_target(self):
        if hasattr(self, "target_star") and self.target_star is not None:
            return
        init_x = (self.setup_cols//2) * CELL_SIZE
        init_y = (self.setup_rows//2) * CELL_SIZE
        self.target_star = TargetStar(self.canvas, self, init_pos=(init_x, init_y))

    def set_target_piece(self, piece):
        self.target_piece = piece
        self.canvas.itemconfig(piece.item, fill="gold")
        messagebox.showinfo("Target Set", f"Piece {piece.label} set as target.")

    def lock_board(self):
        try:
            self.setup_rows = int(self.rows_entry.get())
            self.setup_cols = int(self.cols_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid board dimensions.")
            return
        self.canvas.config(width=self.setup_cols*CELL_SIZE, height=self.setup_rows*CELL_SIZE)
        self.draw_setup_grid()
        self.update_setup_board()
        for widget in self.palette_frame.winfo_children():
            widget.config(state="disabled")
        for piece in self.pieces:
            piece.unbind_setup_events()
        self.initial_positions = {p.label: (p.row, p.col) for p in self.pieces}
        self.mode = "solve"
        self.prepare_solve_mode()

    # ---------------------------
    # Solve Mode Methods
    # ---------------------------
    def prepare_solve_mode(self):
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.focus_set()
        self.move_count = 0
        self.start_time = time.time()
        self.control_frame = tk.Frame(self.root)
        self.control_frame.pack(pady=5)
        self.move_counter_label = tk.Label(self.control_frame, text="Moves: 0", font=("Arial", 16))
        self.move_counter_label.pack(side="left", padx=10)
        self.timer_label = tk.Label(self.control_frame, text="Time: 0 s", font=("Arial", 16))
        self.timer_label.pack(side="left", padx=10)
        self.best_time_label = tk.Label(self.control_frame, text="Best: --", font=("Arial", 16))
        self.best_time_label.pack(side="left", padx=10)
        self.reset_btn = tk.Button(self.control_frame, text="Reset Puzzle", command=self.reset_puzzle)
        self.reset_btn.pack(side="left", padx=10)
        self.menu_btn = tk.Button(self.control_frame, text="Main Menu", command=self.back_to_menu)
        self.menu_btn.pack(side="left", padx=10)
        self.update_timer()
        self.draw_goal_region()
        messagebox.showinfo("Solve Mode", "Board locked!\nClick a piece to select it (light green outline) and use arrow keys to move it.")

    def draw_goal_region(self):
        if not self.target_piece:
            return
        goal_row = self.setup_rows - self.target_piece.height
        goal_col = 0
        x0, y0 = grid_to_canvas(goal_row, goal_col)
        x1, y1 = grid_to_canvas(goal_row + self.target_piece.height, goal_col + self.target_piece.width)
        self.canvas.delete("goal")
        self.canvas.create_rectangle(x0, y0, x1, y1, outline="red", width=3, tags="goal")

    def on_canvas_click(self, event):
        col = event.x // CELL_SIZE
        row = event.y // CELL_SIZE
        clicked = None
        for piece in self.pieces:
            if (piece.row <= row < piece.row + piece.height and
                piece.col <= col < piece.col + piece.width):
                clicked = piece
                break
        if clicked:
            self.selected_piece = clicked
        else:
            self.selected_piece = None
        self.update_selection()

    def update_selection(self):
        for piece in self.pieces:
            if self.selected_piece and piece.label == self.selected_piece.label:
                self.canvas.itemconfig(piece.item, outline="lightgreen", width=4)
            else:
                if self.target_piece and piece.label == self.target_piece.label:
                    self.canvas.itemconfig(piece.item, outline="black", width=2, fill="gold")
                else:
                    self.canvas.itemconfig(piece.item, outline="black", width=2, fill="skyblue")

    def on_key_press(self, event):
        if not self.selected_piece:
            return
        direction = event.keysym.lower()
        if direction in ("up", "down", "left", "right"):
            if self.try_move(self.selected_piece, direction):
                self.move_count += 1
                self.move_counter_label.config(text=f"Moves: {self.move_count}")
                self.draw_goal_region()

    def try_move(self, piece, direction):
        board = {}
        for p in self.pieces:
            for cell in p.occupied_cells():
                board[cell] = p
        new_row, new_col = piece.row, piece.col
        if direction == "up":
            new_row -= 1
        elif direction == "down":
            new_row += 1
        elif direction == "left":
            new_col -= 1
        elif direction == "right":
            new_col += 1
        if new_row < 0 or new_col < 0 or new_row + piece.height > self.setup_rows or new_col + piece.width > self.setup_cols:
            return False
        new_cells = {(new_row + r, new_col + c) for r in range(piece.height) for c in range(piece.width)}
        for cell in new_cells:
            occupant = board.get(cell)
            if occupant and occupant != piece:
                return False
        piece.set_position(new_row, new_col)
        self.update_setup_board()
        return True

    def update_timer(self):
        elapsed = int(time.time() - self.start_time)
        self.timer_label.config(text=f"Time: {elapsed} s")
        self.timer_id = self.root.after(1000, self.update_timer)

    def reset_puzzle(self):
        for piece in self.pieces:
            init_pos = self.initial_positions.get(piece.label, (0,0))
            piece.set_position(*init_pos)
        self.move_count = 0
        self.move_counter_label.config(text="Moves: 0")
        self.start_time = time.time()
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
        self.update_timer()

    def back_to_menu(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
        self.root.unbind("<KeyPress>")
        self.canvas.unbind("<Button-1>")
        self.control_frame.destroy()
        for widget in self.palette_frame.winfo_children():
            widget.config(state="normal")
        for piece in self.pieces:
            piece.bind_setup_events()
        self.mode = "setup"
        self.canvas.delete("goal")
        messagebox.showinfo("Main Menu", "Returned to Setup Mode.")

    def capture_board(self):
        """Capture an image of just the board (canvas) and save it as a PNG file."""
        # Save the canvas drawing as a PostScript file
        ps_file = "board_capture.eps"
        self.canvas.postscript(file=ps_file)
        try:
            image = Image.open(ps_file)
            save_file = "board_capture.png"
            image.save(save_file, "png")
            os.remove(ps_file)  # Remove the temporary file
            messagebox.showinfo("Board Captured", f"Board image saved as '{save_file}'.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to capture board image:\n{e}")

# ---------------------------
# Run the Application
# ---------------------------
if __name__ == '__main__':
    root = tk.Tk()
    root.title("Puzzle Setup & Solve")
    root.geometry("1200x800")
    app = PuzzleApp(root)
    root.mainloop()