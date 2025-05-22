import json
import os
import matplotlib.pyplot as plt

def load_hypernodes(folder="March7", filename="hyperNode.json"):
    """Loads the stored hyper-node configurations from the JSON file."""
    file_path = os.path.join(folder, filename)
    if not os.path.exists(file_path):
        print("Error: Hyper-node file not found!")
        return None
    with open(file_path, "r") as f:
        return json.load(f)

def display_board(board):
    """Displays a given board configuration using Matplotlib."""
    rows, cols = len(board), len(board[0])
    
    fig, ax = plt.subplots(figsize=(cols, rows))
    ax.set_xticks(range(cols+1))
    ax.set_yticks(range(rows+1))
    ax.grid(True)
    
    for r in range(rows):
        for c in range(cols):
            cell_value = board[r][c]
            if cell_value != "empty":
                ax.text(c + 0.5, rows - r - 0.5, cell_value, fontsize=14, ha='center', va='center')

    ax.set_xticklabels([])
    ax.set_yticklabels([])
    plt.show()

def view_hypernodes():
    """Loads and displays each board from the hyperNode.json file."""
    hypernodes = load_hypernodes()
    if not hypernodes:
        return
    
    for idx, node in enumerate(hypernodes):
        print(f"Board {idx+1}")
        display_board(node["board"])

if __name__ == "__main__":
    view_hypernodes()