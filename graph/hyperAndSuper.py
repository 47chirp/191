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

def count_supernode_arrangements(hyper_state, puzzle_data):
    """Counts the number of ways to place 4 blocks in the remaining empty spaces of a Hyper-Node."""
    rows, cols = puzzle_data["rows"], puzzle_data["cols"]
    total_cells = {(r, c) for r in range(rows) for c in range(cols)}
    occupied_cells = {cell for piece in hyper_state for cell in piece}
    empty_spaces = list(total_cells - occupied_cells)
    
    if len(empty_spaces) < 4:
        return 0  # Not enough space to place 4 blocks
    
    supernode_count = len(list(combinations(empty_spaces, 4)))
    return supernode_count

def build_hyper_super_graph(valid_states, puzzle_data):
    """Builds a graph where each Hyper-Node is linked to multiple Super-Nodes."""
    G = nx.DiGraph()
    
    hypernode_children = {}
    
    # Add hyper-nodes
    for idx, state in enumerate(valid_states):
        hyper_label = f"H{idx}"
        G.add_node(hyper_label)
        supernode_count = count_supernode_arrangements(state, puzzle_data)
        hypernode_children[hyper_label] = supernode_count
        
        # Add corresponding super-nodes
        for i in range(supernode_count):
            super_label = f"S{idx}_{i}"
            G.add_node(super_label)
            G.add_edge(hyper_label, super_label)
    
    # Print the number of children each hypernode has
    for hyper, count in hypernode_children.items():
        print(f"{hyper} has {count} children (Super-Nodes)")
    
    # Draw the graph
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_color='lightblue', edge_color='gray')
    plt.show()

def main():
    puzzle_data = load_puzzle_config()
    if not puzzle_data:
        return
    valid_states = count_valid_arrangements(puzzle_data)
    build_hyper_super_graph(valid_states, puzzle_data)

# Run the function
if __name__ == "__main__":
    main()