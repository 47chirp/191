import os
import json
import networkx as nx
import matplotlib.pyplot as plt

# --- DSU / Union-Find Implementation ---
class DSU:
    def __init__(self, n):
        # Initialize parent and rank arrays for n nodes.
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x):
        # Path compression.
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        # Union by rank.
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return
        if self.rank[rx] < self.rank[ry]:
            self.parent[rx] = ry
        elif self.rank[rx] > self.rank[ry]:
            self.parent[ry] = rx
        else:
            self.parent[ry] = rx
            self.rank[rx] += 1

def all_connected(dsu, nodes):
    """
    Check if all nodes in the provided list belong to the same connected component.
    """
    root = dsu.find(nodes[0])
    return all(dsu.find(n) == root for n in nodes)

def incremental_connectivity_check(nodes, edge_list):
    """
    Given a list of nodes and a list of edges (tuples (u, v)),
    add edges one by one and print the point at which the graph becomes connected.
    """
    n = max(nodes) + 1  # Assuming nodes are labeled 0..n-1.
    dsu = DSU(n)
    for i, (u, v) in enumerate(edge_list, start=1):
        dsu.union(u, v)
        if all_connected(dsu, nodes):
            print(f"Graph becomes connected after adding edge {i}: ({u}, {v})")
            break
    else:
        print("Graph never becomes fully connected.")

# --- Graph Building and Plotting Functions ---
def load_json(filepath):
    """Loads JSON data from the given file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def build_graph_from_connections(nodes_file, connections_file):
    """
    Builds a NetworkX graph using the nodes (with "id") and a connection mapping JSON.
    Uses simplified node labels in the format "H<id>".
    """
    nodes = load_json(nodes_file)
    connections = load_json(connections_file)
    
    G = nx.Graph()
    
    # Add nodes with simplified labels: "H0", "H1", etc.
    for node in nodes:
        node_id = node["id"]
        label = f"H{node_id}"
        G.add_node(node_id, label=label)
    
    # Add edges based on the connection mapping.
    # Assumes the keys in connections are string representations of node IDs.
    for node_str, neighbors in connections.items():
        node = int(node_str)
        for neighbor in neighbors:
            neighbor = int(neighbor)
            if not G.has_edge(node, neighbor):
                G.add_edge(node, neighbor)
    
    return G

def plot_graph(G, output_file="hypernode_graph.png"):
    """
    Plots the entire graph using a spring layout with increased spacing and degree-based node sizes.
    Saves the graph as an image file before displaying.
    """
    pos = nx.spring_layout(G, seed=42, k=1.0)
    plt.figure(figsize=(16, 16))
    
    # Compute node sizes based on degree.
    degrees = dict(G.degree())
    node_sizes = [300 * degrees[n] for n in G.nodes()]
    
    nx.draw_networkx_nodes(G, pos, node_color="lightblue", node_size=node_sizes)
    labels = nx.get_node_attributes(G, "label")
    nx.draw_networkx_labels(G, pos, labels, font_size=12)
    nx.draw_networkx_edges(G, pos, width=2, edge_color="gray")
    
    plt.title("Hypernode Graph (Simplified Labels, Degree-Based Node Sizes)")
    plt.axis("off")
    plt.tight_layout()
    
    plt.savefig(output_file)
    print(f"Graph image saved as {output_file}")
    plt.show()

def plot_graph_components(G):
    """
    For a graph with multiple connected components, plots each component in a separate figure
    and saves each as an image file.
    """
    components = list(nx.connected_components(G))
    for i, component in enumerate(components, start=1):
        subG = G.subgraph(component)
        pos = nx.spring_layout(subG, seed=42, k=1.0)
        plt.figure(figsize=(10, 10))
        
        # Compute node sizes based on degree.
        degrees = dict(subG.degree())
        node_sizes = [300 * degrees[n] for n in subG.nodes()]
        
        nx.draw_networkx_nodes(subG, pos, node_color="lightblue", node_size=node_sizes)
        labels = nx.get_node_attributes(subG, "label")
        nx.draw_networkx_labels(subG, pos, labels, font_size=12)
        nx.draw_networkx_edges(subG, pos, width=2, edge_color="gray")
        
        plt.title(f"Connected Component {i}")
        plt.axis("off")
        plt.tight_layout()
        
        # Save the current figure with a unique filename.
        output_file = f"connected_component_{i}.png"
        plt.savefig(output_file)
        print(f"Connected component {i} image saved as {output_file}")
        plt.show()

def fully_connected_graph(G):
    """
    Checks if the graph is fully connected.
    A graph is fully connected if there is a path between every pair of nodes.
    """
    return nx.is_connected(G)

# --- Main Function ---
def main():
    nodes_file = os.path.join("March7", "nodes.json")
    connections_file = os.path.join("March7", "hypernode_connections.json")
    
    if not os.path.exists(nodes_file) or not os.path.exists(connections_file):
        print("Nodes or connections JSON file not found.")
        return
    
    G = build_graph_from_connections(nodes_file, connections_file)
    print(f"Graph has {len(G.nodes())} nodes and {len(G.edges())} edges.")
    
    # Plot the entire graph first.
    plot_graph(G)
    
    if fully_connected_graph(G):
        print("The graph is fully connected.")
    else:
        print("The graph is not fully connected.")
        components = list(nx.connected_components(G))
        print(f"Number of connected components: {len(components)}")
        for i, component in enumerate(components, start=1):
            print(f"Component {i}: {component}")
        
        # Plot and save each connected component separately.
        plot_graph_components(G)
    
    # Incremental connectivity check.
    # Assumes nodes are labeled from 0 to n-1.
    nodes = list(G.nodes())
    edge_list = list(G.edges())
    print("\nIncremental Connectivity Check:")
    incremental_connectivity_check(nodes, edge_list)

if __name__ == "__main__":
    main()