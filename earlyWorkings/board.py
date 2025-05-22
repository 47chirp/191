import tkinter as tk

class Piece:
    def __init__(self, id, x, y, width, height, label, color="lightblue"):
        """
        Initialize a puzzle piece.
        
        :param id: Unique string identifier (e.g., "A", "B").
        :param x: Leftmost column (0-based).
        :param y: Bottom row (0-based).
        :param width: How many columns wide (e.g., 2 for a 2×1).
        :param height: How many rows tall (e.g., 1 for a 2×1).
        :param label: String label to show on the piece.
        :param color: Fill color for drawing the piece.
        """
        self.id = id
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.label = label
        self.color = color

    def cells(self):
        """
        Return a list of (row, col) tuples that this piece occupies.
        Row 0 is bottom. If the piece’s bottom is y and height is h,
        it covers rows [y, y+1, ..., y+h-1].
        """
        return [
            (self.y + dy, self.x + dx)
            for dy in range(self.height)
            for dx in range(self.width)
        ]

class PuzzleBoard:
    def __init__(self, rows, cols, pieces, target_piece_id, cell_size=80):
        """
        Initialize the puzzle board.

        :param rows: Number of rows (0-based from the bottom).
        :param cols: Number of columns.
        :param pieces: A list of Piece objects.
        :param target_piece_id: ID of the target piece (for checking "win" condition).
        :param cell_size: Size in pixels of each cell in the drawing.
        """
        self.rows = rows
        self.cols = cols
        self.cell_size = cell_size

        self.move_count = 0

        # Store pieces in a dict by their ID
        self.pieces = {}
        for p in pieces:
            self.add_piece(p)

        # Build a 2D board array, then find empties
        self.rebuild_board()
        self.empties = self.find_empties()

        self.target_piece_id = target_piece_id
        self.selected_piece_id = None

        self.setup_gui()

    def add_piece(self, piece):
        if piece.id in self.pieces:
            raise ValueError(f"Duplicate piece ID: {piece.id}")
        self.pieces[piece.id] = piece

    def rebuild_board(self):
        """
        Create a 2D list self.board[row][col] with piece IDs or None.
        row=0 is bottom, row=rows-1 is top.
        """
        self.board = [
            [None for _ in range(self.cols)] for _ in range(self.rows)
        ]
        for p in self.pieces.values():
            for (r, c) in p.cells():
                if not (0 <= r < self.rows and 0 <= c < self.cols):
                    raise ValueError(f"Piece {p.id} out of bounds: (r={r}, c={c})")
                self.board[r][c] = p.id

        # Clear out empties in board if we already computed them
        if hasattr(self, "empties"):
            for (r, c) in self.empties:
                if 0 <= r < self.rows and 0 <= c < self.cols:
                    self.board[r][c] = None

    def find_empties(self):
        """
        Return a set of (row, col) cells not occupied by any piece.
        """
        covered = set()
        for p in self.pieces.values():
            for cell in p.cells():
                covered.add(cell)
        all_cells = {(r, c) for r in range(self.rows) for c in range(self.cols)}
        return all_cells - covered

    def can_move(self, piece, direction):
        """
        Check if this piece can move exactly 1 cell in 'direction' ("up","down","left","right").
        Returns True if the required new cell(s) is/are in self.empties, False otherwise.
        """
        empties = self.empties

        # 1×1 piece can move in any direction if that cell is empty
        if piece.width == 1 and piece.height == 1:
            if direction == "up":
                return (piece.y + 1, piece.x) in empties
            elif direction == "down":
                return (piece.y - 1, piece.x) in empties
            elif direction == "left":
                return (piece.y, piece.x - 1) in empties
            elif direction == "right":
                return (piece.y, piece.x + 1) in empties

        # 2×1 horizontal piece that can also move vertically
        elif piece.width == 2 and piece.height == 1:
            if direction == "left":
                # The new left cell is (y, x-1)
                return (piece.y, piece.x - 1) in empties
            elif direction == "right":
                # The new right cell is (y, x+2)
                return (piece.y, piece.x + 2) in empties
            elif direction == "up":
                # Check the two cells above: (y+1, x) and (y+1, x+1)
                return ((piece.y + 1, piece.x) in empties and
                        (piece.y + 1, piece.x + 1) in empties)
            elif direction == "down":
                # Check the two cells below: (y-1, x) and (y-1, x+1)
                return ((piece.y - 1, piece.x) in empties and
                        (piece.y - 1, piece.x + 1) in empties)

        # 1×2 vertical piece that can also move horizontally
        elif piece.width == 1 and piece.height == 2:
            if direction == "up":
                # The new top cell is (y+2, x)
                return (piece.y + 2, piece.x) in empties
            elif direction == "down":
                # The new bottom cell is (y-1, x)
                return (piece.y - 1, piece.x) in empties
            elif direction == "left":
                # Two cells on the left: (y, x-1) and (y+1, x-1)
                return ((piece.y, piece.x - 1) in empties and
                        (piece.y + 1, piece.x - 1) in empties)
            elif direction == "right":
                # Two cells on the right: (y, x+1) and (y+1, x+1)
                return ((piece.y, piece.x + 1) in empties and
                        (piece.y + 1, piece.x + 1) in empties)

        return False

    def move_piece(self, piece_id, direction):
        """
        Move the piece with ID piece_id by exactly 1 cell in 'direction' if possible.
        Update self.empties accordingly and return True if the move succeeded.
        Otherwise return False.
        """
        if piece_id not in self.pieces:
            return False
        piece = self.pieces[piece_id]

        if not self.can_move(piece, direction):
            return False

        old_y, old_x = piece.y, piece.x

        # 1×1 piece
        if piece.width == 1 and piece.height == 1:
            if direction == "up":
                piece.y += 1
                freed_cell = (old_y, old_x)
            elif direction == "down":
                piece.y -= 1
                freed_cell = (old_y, old_x)
            elif direction == "left":
                piece.x -= 1
                freed_cell = (old_y, old_x)
            elif direction == "right":
                piece.x += 1
                freed_cell = (old_y, old_x)

            newly_occupied = (piece.y, piece.x)
            # Remove newly occupied from empties, add freed cell
            if newly_occupied in self.empties:
                self.empties.remove(newly_occupied)
            self.empties.add(freed_cell)

        # 2×1 horizontal that also moves vertically
        elif piece.width == 2 and piece.height == 1:
            if direction == "left":
                piece.x -= 1
                # Freed cell is the old right cell: (old_y, old_x+1)
                freed_cell = (old_y, old_x + 1)
                newly_occupied = (piece.y, piece.x)
                if newly_occupied in self.empties:
                    self.empties.remove(newly_occupied)
                self.empties.add(freed_cell)

            elif direction == "right":
                piece.x += 1
                # Freed cell is the old left cell: (old_y, old_x)
                freed_cell = (old_y, old_x)
                newly_occupied = (piece.y, piece.x + 1)
                if newly_occupied in self.empties:
                    self.empties.remove(newly_occupied)
                self.empties.add(freed_cell)

            elif direction == "up":
                piece.y += 1
                # Freed cells are the old bottom row: (old_y, old_x), (old_y, old_x+1)
                # Newly occupied are (old_y+1, old_x), (old_y+1, old_x+1)
                self.empties.add((old_y, old_x))
                self.empties.add((old_y, old_x + 1))
                self.empties.remove((old_y + 1, old_x))
                self.empties.remove((old_y + 1, old_x + 1))

            elif direction == "down":
                piece.y -= 1
                # Freed cells are the old top row: (old_y, old_x), (old_y, old_x+1)
                # Newly occupied are (old_y-1, old_x), (old_y-1, old_x+1)
                self.empties.add((old_y, old_x))
                self.empties.add((old_y, old_x + 1))
                self.empties.remove((old_y - 1, old_x))
                self.empties.remove((old_y - 1, old_x + 1))

        # 1×2 vertical that can also move horizontally
        elif piece.width == 1 and piece.height == 2:
            if direction == "up":
                piece.y += 1
                # Freed cell is the old bottom: (old_y, old_x)
                freed_cell = (old_y, old_x)
                # Newly occupied is the new top: (old_y+2, old_x)
                newly_occupied = (old_y + 2, old_x)
                if newly_occupied in self.empties:
                    self.empties.remove(newly_occupied)
                self.empties.add(freed_cell)

            elif direction == "down":
                piece.y -= 1
                # Freed cell is the old top: (old_y+1, old_x)
                freed_cell = (old_y + 1, old_x)
                newly_occupied = (old_y - 1, old_x)
                if newly_occupied in self.empties:
                    self.empties.remove(newly_occupied)
                self.empties.add(freed_cell)

            elif direction == "left":
                piece.x -= 1
                # Freed cells: (old_y, old_x), (old_y+1, old_x)
                # Newly occupied: (old_y, old_x-1), (old_y+1, old_x-1)
                self.empties.add((old_y, old_x))
                self.empties.add((old_y + 1, old_x))
                self.empties.remove((old_y, old_x - 1))
                self.empties.remove((old_y + 1, old_x - 1))

            elif direction == "right":
                piece.x += 1
                # Freed cells: (old_y, old_x), (old_y+1, old_x)
                # Newly occupied: (old_y, old_x+1), (old_y+1, old_x+1)
                self.empties.add((old_y, old_x))
                self.empties.add((old_y + 1, old_x))
                self.empties.remove((old_y, old_x + 1))
                self.empties.remove((old_y + 1, old_x + 1))

        else:
            return False

        self.rebuild_board()
        self.draw_board()
        return True

    def check_goal(self):
        """
        Example 'win' condition: the target piece is at the bottom-left corner (top-left of it = (0,0) in internal coords).
        """
        target = self.pieces[self.target_piece_id]
        return (target.x, target.y) == (0, 0)

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("Sliding Block Puzzle: 2×1 Moves in All Directions")

        self.canvas = tk.Canvas(
            self.root,
            width=self.cols * self.cell_size,
            height=self.rows * self.cell_size,
            bg="white"
        )
        self.canvas.pack()

        # Bind mouse click
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        # Move counter
        self.move_counter_label = tk.Label(self.root, text="Moves: 0")
        self.move_counter_label.pack(pady=2)

        # Status label
        self.status_label = tk.Label(
            self.root,
            text="Click a piece, then use arrow keys to move."
        )
        self.status_label.pack(pady=5)

        # Selection label
        self.selection_label = tk.Label(self.root, text="Selected piece: None")
        self.selection_label.pack(pady=5)

        # Bind arrow keys
        self.root.bind("<KeyPress>", self.on_key_press)

        self.draw_board()
        self.root.mainloop()

    def draw_board(self):
        """
        Redraw the board in the canvas.
        Note that row=0 is the bottom in our logic, but y=0 is top in Tkinter,
        so we flip by using (rows - 1 - r).
        """
        self.canvas.delete("all")

        # Draw the background grid
        for r in range(self.rows):
            top_y = (self.rows - 1 - r) * self.cell_size
            bot_y = top_y + self.cell_size
            for c in range(self.cols):
                left_x = c * self.cell_size
                right_x = left_x + self.cell_size
                fill = "white"
                if (r, c) in self.empties:
                    fill = "lightgrey"  # highlight empties
                self.canvas.create_rectangle(
                    left_x, top_y, right_x, bot_y, fill=fill, outline="black"
                )

        # Draw the pieces
        for p in self.pieces.values():
            # piece top row is y + height - 1
            top_y_piece = (self.rows - 1 - (p.y + p.height - 1)) * self.cell_size
            bot_y_piece = (self.rows - p.y) * self.cell_size
            left_x_piece = p.x * self.cell_size
            right_x_piece = (p.x + p.width) * self.cell_size

            fill_color = p.color if p.id == self.target_piece_id else "lightblue"
            if p.id == self.selected_piece_id:
                outline_col = "green"
                outline_w = 4
            else:
                outline_col = "black"
                outline_w = 1

            self.canvas.create_rectangle(
                left_x_piece, top_y_piece, right_x_piece, bot_y_piece,
                fill=fill_color, outline=outline_col, width=outline_w
            )
            self.canvas.create_text(
                (left_x_piece + right_x_piece)/2,
                (top_y_piece + bot_y_piece)/2,
                text=p.label,
                font=("Helvetica", 16)
            )

        # Draw the "goal" region for the target piece
        target = self.pieces[self.target_piece_id]
        gx1 = 0
        gx2 = target.width * self.cell_size
        gy1 = (self.rows - target.height) * self.cell_size
        gy2 = gy1 + target.height * self.cell_size
        self.canvas.create_rectangle(gx1, gy1, gx2, gy2, outline="red", width=3)

    def on_canvas_click(self, event):
        """
        Convert (event.x, event.y) to puzzle coords and select piece if any.
        """
        col = event.x // self.cell_size
        row = (self.rows - 1) - (event.y // self.cell_size)

        if 0 <= row < self.rows and 0 <= col < self.cols:
            clicked_id = self.board[row][col]
            if clicked_id is not None:
                self.selected_piece_id = clicked_id
                self.selection_label.config(text=f"Selected piece: {clicked_id}")
            else:
                self.selected_piece_id = None
                self.selection_label.config(text="Selected piece: None")

        self.draw_board()

    def on_key_press(self, event):
        """
        Handle Up/Down/Left/Right key presses.
        If no piece is selected, automatically select target piece.
        """
        if event.keysym in ("Up", "Down", "Left", "Right"):
            if self.selected_piece_id is None:
                self.selected_piece_id = self.target_piece_id
                self.selection_label.config(text=f"Selected piece: {self.target_piece_id}")
            self.move_and_check(event.keysym.lower())

    def move_and_check(self, direction):
        """
        Attempt to move the selected piece in 'direction'.
        If it moves, increment move_count, check for goal, update status.
        """
        if self.selected_piece_id is None:
            self.status_label.config(text="No piece selected!")
            return

        if self.move_piece(self.selected_piece_id, direction):
            # Moved successfully
            self.move_count += 1
            self.move_counter_label.config(text=f"Moves: {self.move_count}")

            # Check if puzzle is solved
            if self.selected_piece_id == self.target_piece_id and self.check_goal():
                self.status_label.config(text="Congratulations! Puzzle solved!")
            else:
                self.status_label.config(text=f"Moved {self.selected_piece_id} {direction}.")
        else:
            self.status_label.config(text=f"Cannot move {self.selected_piece_id} {direction}.")

# --------------------------------------------------------------------
# Example usage:
if __name__ == "__main__":
    rows = 3
    cols = 4
    pieces = []

    # A 2×1 block at top-left
    pieces.append(Piece("A", x=0, y=0, width=2, height=1, label="A"))
    # B 2×1 (target) at top-right; can now move in all directions if space is free
    pieces.append(Piece("B", x=2, y=2, width=2, height=1, label="B", color="yellow"))
    # C 1×2 vertical block on the left side
    pieces.append(Piece("C", x=1, y=1, width=1, height=2, label="C"))
    # D 1×1 block in middle
    pieces.append(Piece("D", x=2, y=1, width=1, height=1, label="D"))
    # E 1×1
    pieces.append(Piece("E", x=3, y=1, width=1, height=1, label="E"))
    # F, G 1×1 on bottom row
    pieces.append(Piece("F", x=2, y=0, width=1, height=1, label="F"))
    pieces.append(Piece("G", x=3, y=0, width=1, height=1, label="G"))

    board = PuzzleBoard(rows, cols, pieces, target_piece_id="B", cell_size=80)