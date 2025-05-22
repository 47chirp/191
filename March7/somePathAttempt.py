'''
Want to see if certain configurations of hypernodes work
By this we are just saying we are interested in some path existing between two nodes
'''

import os
import json
import networkx as nx
import matplotlib.pyplot as plt

# --- Graph Building Functions ---
def load_json(filepath):
    """Loads JSON data from the given file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def build_graph_from_connections(nodes_file, connections_file):
    """
    Builds a NetworkX graph using the nodes (with "id") and a connection mapping JSON.
    Each node is given a simplified label in the format "H<id>".
    """
    nodes = load_json(nodes_file)
    connections = load_json(connections_file)
    
    G = nx.Graph()
    for node in nodes:
        node_id = node["id"]
        label = f"H{node_id}"
        G.add_node(node_id, label=label)
    
    for node_str, neighbors in connections.items():
        node = int(node_str)
        for neighbor in neighbors:
            neighbor = int(neighbor)
            if not G.has_edge(node, neighbor):
                G.add_edge(node, neighbor)
    
    return G

def fully_connected_graph(G):
    """Checks if the graph is fully connected."""
    return nx.is_connected(G)

# --- Plotting Function with Component Colors ---
def plot_graph(G, output_file="hypernode_graph.png"):
    """
    Plots the graph using a spring layout with nodes color-coded by connected component.
    Saves the graph as an image file before displaying.
    """
    pos = nx.spring_layout(G, seed=42, k=1.0)
    plt.figure(figsize=(16, 16))
    
    # Determine connected components and assign a color to each.
    components = list(nx.connected_components(G))
    cmap = plt.cm.get_cmap('Set1', len(components))
    color_map = {node: cmap(i) for i, comp in enumerate(components) for node in comp}
    node_colors = [color_map[node] for node in G.nodes()]
    
    node_sizes = [300 * G.degree(n) for n in G.nodes()]
    
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes)
    labels = nx.get_node_attributes(G, "label")
    nx.draw_networkx_labels(G, pos, labels, font_size=12)
    nx.draw_networkx_edges(G, pos, width=2, edge_color="gray")
    
    plt.title("Hypernode Graph with Color-Coded Connected Components")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_file)
    print(f"Graph image saved as {output_file}")
    plt.show()

# --- New Function: Check for Inter-Component Edges ---
def check_inter_component_edges(G):
    """
    Checks if any edge connects nodes in different connected components.
    Prints a simple message with the result.
    """
    components = list(nx.connected_components(G))
    comp_mapping = {}
    for idx, comp in enumerate(components):
        for node in comp:
            comp_mapping[node] = idx

    for u, v in G.edges():
        if comp_mapping[u] != comp_mapping[v]:
            print("Inter-component edge found.")
            return
    print("No inter-component edges found.")

# --- New Function: Move Statistics Between Two Hypernodes ---
def move_statistics(G, start_label, end_label):
    """
    Given two hypernode labels (e.g., 'H0' and 'H5'),
    this function determines:
      - Whether any sequence of moves exists between them.
      - The length of the shortest sequence (minimum moves).
      - The total number of distinct simple sequences (paths) between them.
    """
    start_node = None
    end_node = None

    for node, data in G.nodes(data=True):
        if data.get("label") == start_label:
            start_node = node
        if data.get("label") == end_label:
            end_node = node

    if start_node is None or end_node is None:
        print("One or both hypernodes not found in the graph.")
        return

    if not nx.has_path(G, start_node, end_node):
        print(f"No sequence of moves exists from {start_label} to {end_label}.")
        print("They belong to different connected components.")
        return

    shortest_path = nx.shortest_path(G, source=start_node, target=end_node)
    shortest_moves = len(shortest_path) - 1
    all_paths = list(nx.all_simple_paths(G, source=start_node, target=end_node))
    total_paths = len(all_paths)

    print(f"Sequence exists from {start_label} to {end_label}.")
    print(f"Shortest sequence requires {shortest_moves} move(s).")
    print(f"Total distinct simple move sequences: {total_paths}")

# --- New Function: Count Reachable Configurations ---
def count_reachable_configurations(G, start_label):
    """
    Given a hypernode label (e.g., 'H0'),
    this function computes the number of unique configurations (nodes) reachable
    from that hypernode. This is simply the size of the connected component containing the hypernode.
    """
    start_node = None
    for node, data in G.nodes(data=True):
        if data.get("label") == start_label:
            start_node = node
            break
    if start_node is None:
        print(f"Hypernode {start_label} not found in the graph.")
        return
    component = nx.node_connected_component(G, start_node)
    count = len(component)
    print(f"Total unique configurations reachable from {start_label}: {count}")

# --- Main Function ---
def main():
    nodes_file = os.path.join("March7", "nodes.json")
    connections_file = os.path.join("March7", "hypernode_connections.json")
    
    if not os.path.exists(nodes_file) or not os.path.exists(connections_file):
        print("Nodes or connections JSON file not found.")
        return
    
    G = build_graph_from_connections(nodes_file, connections_file)
    print(f"Graph has {len(G.nodes())} nodes and {len(G.edges())} edges.")
    
    if fully_connected_graph(G):
        print("The graph is fully connected.")
    else:
        print("The graph is not fully connected.")
        components = list(nx.connected_components(G))
        print(f"Number of connected components: {len(components)}")
    
    # Plot the graph with color-coded connected components.
    plot_graph(G)
    
    # Check for any inter-component edge.
    check_inter_component_edges(G)
    
    # Ask the user for two hypernode labels and output move statistics.
    print("\nMove Analysis Between Two Hypernodes:")
    start_label = input("Enter start hypernode label (e.g., 'H0'): ").strip()
    end_label = input("Enter end hypernode label (e.g., 'H1'): ").strip()
    move_statistics(G, start_label, end_label)
    
    # Ask the user for a hypernode label to count reachable configurations.
    print("\nReachable Configurations:")
    config_label = input("Enter hypernode label to analyze (e.g., 'H0'): ").strip()
    count_reachable_configurations(G, config_label)

if __name__ == "__main__":
    main()