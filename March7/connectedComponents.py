'''
We have already done the viewHypernodeDist and preConnect functions in this folder.

The next step for us is for each hyper-node, we need to find the connected components.

These will be represented as green dots with lines connecting them if they are connected.

This will be stored in another JSON file in the same folder, which will be used to display the connected components.

That file is called "components.json".

Working!!!! As of 3, March 2025. 4:42 PM.
'''

import json
import os
import networkx as nx
from collections import deque

def load_hypernodes(folder="March7", filename="hyperNode.json"):
    """Loads the hypernodes from the stored JSON file."""
    hypernode_file = os.path.join(folder, filename)
    if not os.path.exists(hypernode_file):
        print(f"Error: {hypernode_file} not found!")
        return None

    with open(hypernode_file, "r") as f:
        return json.load(f)

def build_hypernode_graph(hypernodes):
    """Builds a graph where each unique valid arrangement is treated as a node."""
    G = nx.Graph()
    
    for i, hypernode in enumerate(hypernodes):
        G.add_node(i, board=hypernode["board"], pieces=hypernode["pieces"])
    
    for i in range(len(hypernodes)):
        for j in range(i + 1, len(hypernodes)):
            # Two nodes are connected if they differ by exactly one move
            if is_one_move_away(hypernodes[i], hypernodes[j]):
                G.add_edge(i, j)
    
    return G

def is_one_move_away(state_a, state_b):
    """
    Determines if two hyper-nodes differ by exactly one move.
    This means that one piece has moved while all others remain in the same position.
    """
    pieces_a = {frozenset(map(tuple, piece["cells"])) for piece in state_a["pieces"]}
    pieces_b = {frozenset(map(tuple, piece["cells"])) for piece in state_b["pieces"]}

    # Compute the symmetric difference (what changed between the two states)
    diff = pieces_a.symmetric_difference(pieces_b)

    return len(diff) == 2  # Only one piece should have moved

def find_internal_grouping(hypernode):
    """
    Finds fully connected groups of empty cells using horizontal/vertical adjacency.
    A cell is considered empty if its value (after stripping and lowercasing) equals "empty".
    """
    visited = set()  # Track visited empty cells
    group_sizes = []

    def bfs(start, empty_cells):
        """Breadth-first search to find connected groups of empty cells."""
        queue = deque([start])
        visited.add(start)
        size = 0

        while queue:
            r, c = queue.popleft()
            size += 1

            # Explore adjacent (up, down, left, right) cells
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor = (r + dr, c + dc)
                if neighbor in empty_cells and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return size

    # Extract empty cells from the board.
    empty_cells = set()
    board = hypernode.get("board", [])
    processed_board = []  # for debug printing

    for r, row in enumerate(board):
        # If row is a string, split it into cells; if it's a list, use it directly.
        cells = row.split() if isinstance(row, str) else row
        processed_board.append(cells)
        for c, cell in enumerate(cells):
            if cell.strip().lower() == "empty":  # Consider cell empty if it's "empty"
                empty_cells.add((r, c))

    # Debug info: print the board and the detected empty cells.
    print("\n🟢 Processing Hypernode:")
    print("🗺️ Board Representation:")
    for row in processed_board:
        print(" ".join(row))
    print(f"📍 Detected Empty Cells: {empty_cells}")

    if not empty_cells:
        print("⚠️ No empty cells found! Double-check board format.")

    # Find all fully connected empty regions
    for cell in empty_cells:
        if cell not in visited:
            cluster_size = bfs(cell, empty_cells)
            group_sizes.append(cluster_size)

    print(f"🔗 Connected Empty Cell Groups Found: {group_sizes}\n")
    return tuple(sorted(group_sizes))

def save_connected_components(hypernodes, folder="March7", filename="components.json"):
    """Saves the connected components for each hypernode individually to a JSON file."""
    if not os.path.exists(folder):
        os.makedirs(folder)

    component_data = {}
    global_breakdown = {}

    for node_id, hypernode in enumerate(hypernodes):
        internal_structure = find_internal_grouping(hypernode)  # Process each hypernode

        # Store the breakdown per hypernode using string keys
        component_data[str(node_id)] = str(internal_structure)

        # Track global counts of different structures using string keys
        global_breakdown[str(internal_structure)] = global_breakdown.get(str(internal_structure), 0) + 1

    # Save results to JSON
    component_file = os.path.join(folder, filename)
    with open(component_file, "w") as f:
        json.dump({
            "node_component_mapping": component_data,
            "graph_component_breakdown": global_breakdown
        }, f, indent=2)

    print(f"✅ Connected component structures saved to {component_file}")

def main():
    hypernodes = load_hypernodes()
    if not hypernodes:
        return
    
    G = build_hypernode_graph(hypernodes)
    
    save_connected_components(hypernodes)

if __name__ == "__main__":
    main()