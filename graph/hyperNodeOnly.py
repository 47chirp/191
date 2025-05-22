from itertools import combinations
import networkx as nx
import matplotlib.pyplot as plt
import json
import os

def load_puzzle_config(file_path="puzzle_config.json"):
    """Loads the puzzle configuration from JSON."""
    if not os.path.exists(file_path):
        print("Error: Puzzle configuration file not found!")
        return None
    with open(file_path, "r") as f:
        return json.load(f)

def count_valid_arrangements(puzzle_data):
    """
    Counts unique valid, non-overlapping arrangements from JSON file.
    Each unique valid board arrangement is treated as a Hyper-Node in a graph.
    """
    rows, cols = puzzle_data["rows"], puzzle_data["cols"]
    num_1x2 = sum(1 for p in puzzle_data["pieces"] if p["piece_type"] == "1x2")
    num_2x1 = sum(1 for p in puzzle_data["pieces"] if p["piece_type"] == "2x1")
    
    placements_h = []
    placements_v = []
    
    # Generate all possible placements of horizontal 1x2 pieces
    for r in range(rows):
        for c in range(cols - 1):  # Ensure room for horizontal placement
            placements_h.append(((r, c), (r, c + 1)))
    
    # Generate all possible placements of vertical 2x1 pieces
    for r in range(rows - 1):  # Ensure room for vertical placement
        for c in range(cols):
            placements_v.append(((r, c), (r + 1, c)))
    
    # Generate unique valid arrangements using combinations
    valid_states = set()
    
    for chosen_h in combinations(placements_h, num_1x2):
        for chosen_v in combinations(placements_v, num_2x1):
            occupied = set()
            valid = True
            state = []
            
            for piece in chosen_h + chosen_v:
                if piece[0] in occupied or piece[1] in occupied:
                    valid = False
                    break
                occupied.add(piece[0])
                occupied.add(piece[1])
                state.append(piece)
            
            if valid:
                valid_states.add(frozenset(state))  # Store unique board states
    
    print(f"Total unique valid arrangements (Hyper-Nodes): {len(valid_states)}")
    return valid_states

def build_hypernode_graph(valid_states):
    """Builds a graph where each unique valid arrangement is treated as a Hyper-Node."""
    G = nx.Graph()
    
    # Add hyper-nodes
    for idx, state in enumerate(valid_states):
        G.add_node(f"H{idx}")
    
    # Connect hyper-nodes based on one-move transitions (pieces shifting positions)
    state_list = list(valid_states)
    for i, state_a in enumerate(state_list):
        for j, state_b in enumerate(state_list):
            if i < j:  # Avoid duplicate comparisons
                diff = state_a.symmetric_difference(state_b)
                if len(diff) == 2:  # Only one move difference
                    G.add_edge(f"H{i}", f"H{j}")
    
    # Draw the graph
    plt.figure(figsize=(10, 6))
    nx.draw(G, with_labels=True, node_color='lightblue', edge_color='gray')
    plt.show()

def main():
    puzzle_data = load_puzzle_config()
    if not puzzle_data:
        return
    valid_states = count_valid_arrangements(puzzle_data)
    build_hypernode_graph(valid_states)

# Run the function
if __name__ == "__main__":
    main()