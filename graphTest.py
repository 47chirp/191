'''
Wanting to see if we can graph the moves of the pieces in the puzzle
Hierarchial graph?
What if we start with moving the largest pieces, then seeing how the smaller pieces can move?
'''

import os
import json
import networkx as nx
import matplotlib.pyplot as plt
from collections import deque

MOVES = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1)
}

def load_puzzle_config(file_path="puzzle_config.json"):
    """Loads the puzzle configuration from JSON."""
    abs_path = os.path.abspath(file_path)
    if not os.path.exists(abs_path):
        print("Error: Puzzle configuration file not found!")
        return None

    with open(abs_path, "r") as f:
        return json.load(f)

def get_piece_dimensions(piece):
    """Returns the height and width based on piece type."""
    return {"1x1": (1, 1), "1x2": (1, 2), "2x1": (2, 1)}.get(piece["piece_type"], (1, 1))

def create_board_representation(pieces):
    """Creates a board representation with occupied positions."""
    board = {}
    for piece in pieces:
        height, width = get_piece_dimensions(piece)
        piece["height"], piece["width"] = height, width  
        for r in range(height):
            for c in range(width):
                board[(piece["row"] + r, piece["col"] + c)] = piece["label"]
    return board

def is_valid_move(piece, new_row, new_col, board, rows, cols):
    """Checks if a piece can move one step without collisions or leaving the board."""
    height, width = piece["height"], piece["width"]

    if new_row < 0 or new_col < 0 or new_row + height > rows or new_col + width > cols:
        return False

    for r in range(height):
        for c in range(width):
            cell = (new_row + r, new_col + c)
            if cell in board and board[cell] != piece["label"]:
                return False

    return True

def get_all_possible_moves(pieces, rows, cols):
    """Finds all valid moves for each piece in the puzzle."""
    board = create_board_representation(pieces)
    move_dict = {}

    for piece in sorted(pieces, key=lambda p: -(p["height"] * p["width"])):  # Prioritize largest pieces
        move_dict[piece["label"]] = []
        for direction, (dr, dc) in MOVES.items():
            new_row, new_col = piece["row"] + dr, piece["col"] + dc
            if is_valid_move(piece, new_row, new_col, board, rows, cols):
                move_dict[piece["label"]].append((direction, new_row, new_col))
    return move_dict

def board_to_tuple(pieces):
    """Converts the board state to a tuple for hashing (used in visited states)."""
    return tuple(sorted((p["label"], p["row"], p["col"]) for p in pieces))

def find_shortest_target_path_with_graph(puzzle_data):
    """Finds the shortest path where the target piece reaches the bottom-left and builds a graph."""
    rows, cols = puzzle_data["rows"], puzzle_data["cols"]
    initial_pieces = puzzle_data["pieces"]
    target_label = puzzle_data["target"]

    # Record the initial board state
    initial_state = board_to_tuple(initial_pieces)
    queue = deque()
    visited = set()
    graph = nx.DiGraph()  # Directed graph to store moves

    # Queue holds tuples of (current configuration, path of board states)
    queue.append((initial_pieces, [initial_state]))
    visited.add(initial_state)

    while queue:
        current_pieces, state_history = queue.popleft()
        current_state = board_to_tuple(current_pieces)
        
        # Find the target piece in the current state
        target_piece = next(p for p in current_pieces if p["label"] == target_label)

        # Check if the target piece is in bottom-left
        if target_piece["row"] == rows - 1 and target_piece["col"] == 0:
            return graph, state_history  # Return graph and the solution path (as board states)
        
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
                    queue.append((new_pieces, state_history + [new_state]))
                    
                    # Add the transition to the graph with a label for the move
                    graph.add_edge(current_state, new_state, label=f"{piece['label']} {direction}")

    return graph, None  # No solution found

def visualize_graph(graph, shortest_path):
    """Draws the force-directed move graph using spring_layout()."""
    plt.figure(figsize=(12, 8))

    pos = nx.spring_layout(graph, seed=42)  # Compute positions using a force-directed layout

    # Draw all nodes and edges in black
    nx.draw(graph, pos, with_labels=False, node_size=300, node_color="k", edge_color="gray")

    # Highlight the shortest solution path in red, if it exists
    if shortest_path:
        print("\nShortest solution path (board states):")
        for state in shortest_path:
            print(state)

        # Determine the edges along the path
        path_edges = list(zip(shortest_path, shortest_path[1:]))
        nx.draw_networkx_nodes(graph, pos, nodelist=shortest_path, node_color="r")
        nx.draw_networkx_edges(graph, pos, edgelist=path_edges, edge_color="r", width=2)

    plt.title("Puzzle Move Graph (Spring Layout)")
    plt.show()

def main():
    puzzle_data = load_puzzle_config()
    if not puzzle_data:
        return

    # Find the shortest solution path and generate the corresponding graph
    graph, shortest_path = find_shortest_target_path_with_graph(puzzle_data)
    
    print(f"\nTotal graph nodes: {len(graph.nodes)}")
    print(f"Total graph edges: {len(graph.edges)}")
    
    # Visualize the graph with the solution path highlighted
    visualize_graph(graph, shortest_path)

if __name__ == "__main__":
    main()