import json
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

def load_states(filename="states.json"):
    """Loads the precomputed puzzle states from JSON."""
    with open(filename, "r") as f:
        return json.load(f)

def build_graph_from_states(states_data):
    """Builds a directed graph from the JSON state data."""
    G = nx.DiGraph()
    center = states_data["center"]
    G.add_node(center)
    
    for hyper in states_data["hypernodes"]:
        h_label = hyper["label"]
        G.add_node(h_label)
        G.add_edge(center, h_label)
        
        for supernode in hyper["supernodes"]:
            s_label = supernode["label"]
            G.add_node(s_label)
            G.add_edge(h_label, s_label)
            
            # BFS Solution Steps (if available)
            prev_label = s_label
            for sol in supernode["bfs_solution"]:
                step_label = f"{s_label}_step{sol['step']}"
                G.add_node(step_label)
                G.add_edge(prev_label, step_label)
                prev_label = step_label  # Link step-to-step in BFS path
                
    return G

def assign_positions(G, states_data):
    """Assigns positions to nodes for radial layout."""
    pos = {}
    center = states_data["center"]
    pos[center] = (0, 0)
    
    # Tier 1: Hypernodes (radius 3)
    hypernodes = states_data["hypernodes"]
    hyper_labels = [h["label"] for h in hypernodes]
    total_hyper = len(hyper_labels)
    
    for i, label in enumerate(hyper_labels):
        angle = 2 * np.pi * i / max(1, total_hyper)
        pos[label] = (3 * np.cos(angle), 3 * np.sin(angle))
    
    # Tier 2: Supernodes (radius 6)
    super_labels = []
    for hyper in hypernodes:
        for supernode in hyper["supernodes"]:
            super_labels.append(supernode["label"])
    
    total_super = len(super_labels)
    for i, label in enumerate(super_labels):
        angle = 2 * np.pi * i / max(1, total_super)
        pos[label] = (6 * np.cos(angle), 6 * np.sin(angle))
    
    # Tier 3: BFS path steps (expanding outwards)
    base_offset = 1.0  # Distance per step
    curvature = 0.3  # Curvature factor
    for node in G.nodes():
        if "_step" in node:
            parent_label = node.rsplit("_step", 1)[0]
            if parent_label in pos:
                parent_pos = pos[parent_label]
                branch_angle = np.arctan2(parent_pos[1], parent_pos[0])
                try:
                    step = int(node.split("_step")[1])
                except:
                    step = 1
                displacement = base_offset * step
                perp_offset = curvature * (step ** 1.5)
                x = parent_pos[0] + displacement * np.cos(branch_angle) - perp_offset * np.sin(branch_angle)
                y = parent_pos[1] + displacement * np.sin(branch_angle) + perp_offset * np.cos(branch_angle)
                pos[node] = (x, y)
    
    return pos

def plot_graph(G, pos):
    """Plots the radial graph with different colors for each tier."""
    plt.figure(figsize=(16, 16))
    
    # Define node categories
    center_node = "Start"
    hyper_nodes = [n for n in G.nodes if n.startswith("H") and "_S" not in n]
    super_nodes = [n for n in G.nodes if "_S" in n and "_step" not in n]
    bfs_nodes = [n for n in G.nodes if "_step" in n]

    # Assign colors
    color_map = {
        center_node: "black",
        **{n: "red" for n in hyper_nodes},
        **{n: "blue" for n in super_nodes},
        **{n: "green" for n in bfs_nodes},
    }
    
    # Assign sizes (outer rings smaller)
    size_map = {
        center_node: 400,
        **{n: 250 for n in hyper_nodes},
        **{n: 180 for n in super_nodes},
        **{n: 100 for n in bfs_nodes},
    }
    
    # Draw graph
    nx.draw(
        G, pos, 
        node_color=[color_map[n] for n in G.nodes], 
        edge_color="gray",
        node_size=[size_map[n] for n in G.nodes],
        alpha=0.9,
        with_labels=False  # REMOVE ALL LABELS
    )
    
    plt.title("Radial Graph of Puzzle States", fontsize=18)
    plt.show()

def main():
    states_data = load_states("states.json")
    G = build_graph_from_states(states_data)
    pos = assign_positions(G, states_data)
    plot_graph(G, pos)

if __name__ == "__main__":
    main()