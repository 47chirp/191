import json
import os
import math
from fpdf import FPDF

class PDF(FPDF):
    pass  # You can customize headers/footers if desired.

def draw_board(pdf, board, x_offset, y_offset, cell_size):
    """
    Draws a board on the PDF at the given x,y offset.
    The board is assumed to be a list of rows (top to bottom) where each row is a list of strings.
    """
    rows = len(board)
    cols = len(board[0])
    
    # Draw the board grid and labels.
    for i in range(rows):
        for j in range(cols):
            # Compute cell coordinates.
            # FPDF's coordinate origin (0,0) is at the top-left.
            # We want the top row of the board to appear at y_offset.
            x = x_offset + j * cell_size
            y = y_offset + i * cell_size
            pdf.rect(x, y, cell_size, cell_size)
            value = board[i][j]
            if value != "empty":
                # Draw the label roughly centered.
                pdf.set_font("Helvetica", size=8)
                # Adjust text position a bit inside the cell.
                pdf.text(x + cell_size * 0.3, y + cell_size * 0.6, value)

def create_pdf(json_path, output_pdf):
    # Load the JSON data.
    with open(json_path, "r") as f:
        nodes = json.load(f)
    
    # Create an FPDF instance using Letter size (216 x 279 mm).
    pdf = PDF(format='letter')
    
    # Layout settings.
    margin = 10  # mm margin
    columns = 5
    rows = 10  # 5 * 10 = 50 boards per page.
    boards_per_page = columns * rows
    
    # Letter dimensions in mm.
    page_width = 216
    page_height = 279
    avail_width = page_width - 2 * margin
    avail_height = page_height - 2 * margin
    grid_cell_width = avail_width / columns
    grid_cell_height = avail_height / rows
    
    # Board configuration dimensions (assuming 3 rows x 4 columns).
    board_rows = 3
    board_cols = 4
    # Compute maximum cell size so the board fits in the grid cell.
    cell_size_x = grid_cell_width / board_cols
    cell_size_y = grid_cell_height / board_rows
    board_cell_size = min(cell_size_x, cell_size_y)
    board_width = board_cols * board_cell_size
    board_height = board_rows * board_cell_size
    
    total_nodes = len(nodes)
    pages = math.ceil(total_nodes / boards_per_page)
    
    for page in range(pages):
        pdf.add_page()
        start_index = page * boards_per_page
        end_index = min(start_index + boards_per_page, total_nodes)
        page_nodes = nodes[start_index:end_index]
        
        for idx, node in enumerate(page_nodes):
            # Determine grid position.
            col_index = idx % columns
            row_index = idx // columns
            
            # Compute the top-left corner of the grid cell.
            cell_x = margin + col_index * grid_cell_width
            cell_y = margin + row_index * grid_cell_height
            
            # Center the board in the grid cell.
            board_x = cell_x + (grid_cell_width - board_width) / 2
            board_y = cell_y + (grid_cell_height - board_height) / 2
            
            # Label the configuration (optional).
            pdf.set_font("Helvetica", size=7)
            config_label = f"Config {start_index + idx + 1}"
            # Draw label above the board, if space permits.
            pdf.text(cell_x + 1, cell_y + 4, config_label)
            
            board = node.get("board")
            draw_board(pdf, board, board_x, board_y, board_cell_size)
    
    pdf.output(output_pdf)

if __name__ == "__main__":
    folder_path = "March7"
    json_file = os.path.join(folder_path, "hyperNode.json")
    output_file = os.path.join(folder_path, "configurations.pdf")
    
    create_pdf(json_file, output_file)