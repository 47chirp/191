import os
import json
import networkx as nx
import matplotlib.pyplot as plt

def load_json(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

def build_hierarchy(allocation_json):
    """
    Builds a directed tree (DiGraph) for hierarchical visualization.
    
    - Root is "H0" (hypernode 0).
    - For each key in allocation_json (formatted "0-<neighbor>"), create a child node (e.g. "H71").
    - Under each neighbor, each allocation possibility is added as a leaf node, labeled generically ("Alloc 1", etc.).
    
    Returns:
      - T: the DiGraph.
      - alloc_details: a dictionary mapping allocation leaf node names to their full allocation details.
    """
    T = nx.DiGraph()
    alloc_details = {}  # key: allocation leaf node, value: full allocation details (list of coordinates)
    
    root = "H0"
    T.add_node(root)
    
    for edge_key, alloc_list in allocation_json.items():
        # Process only edges from hypernode 0 (format: "0-<neighbor>")
        parts = edge_key.split("-")
        if parts[0] != "0":
            continue
        neighbor = f"H{parts[1]}"
        T.add_node(neighbor)
        T.add_edge(root, neighbor)
        for i, alloc in enumerate(alloc_list):
            alloc_node = f"{neighbor}_alloc_{i+1}"
            # Label allocation leaves generically.
            T.add_node(alloc_node, label=f"Alloc {i+1}")
            T.add_edge(neighbor, alloc_node)
            alloc_details[alloc_node] = alloc  # store full allocation details
    # Force a top-to-bottom layout.
    T.graph['graph'] = {'rankdir': 'TB'}
    return T, alloc_details

def plot_hierarchy_with_key(T, alloc_details, output_file="hierarchical_allocations_colored_downward.png"):
    """
    Plots the directed tree T in a hierarchical, top-to-bottom layout.
    Node colors are assigned as:
      - Root (H0): Red
      - Direct neighbors: Blue
      - Allocation leaves: Green
    A key (text box) with allocation details is placed in the upper right corner.
    """
    try:
        pos = nx.nx_pydot.graphviz_layout(T, prog="dot")
    except Exception as e:
        print("Graphviz layout failed; using spring layout instead.", e)
        pos = nx.spring_layout(T)
    
    plt.figure(figsize=(14, 10))
    
    # Determine node colors based on node names.
    node_colors = {}
    for n in T.nodes():
        if n == "H0":
            node_colors[n] = "red"
        elif "alloc" in n:
            node_colors[n] = "green"
        else:
            node_colors[n] = "blue"
    colors = [node_colors[n] for n in T.nodes()]
    
    # Use node attribute 'label' if available; otherwise, node name.
    labels = {n: T.nodes[n].get("label", n) for n in T.nodes()}
    
    nx.draw(T, pos, with_labels=True, labels=labels, node_color=colors,
            node_size=1500, font_size=10, arrows=True)
    
    # Build key string from allocation details.
    key_lines = ["Allocation Key:"]
    for alloc_node, detail in alloc_details.items():
        key_lines.append(f"{alloc_node}: {detail}")
    key_text = "\n".join(key_lines)
    
    # Place the key in the upper right corner.
    plt.gcf().text(0.75, 0.75, key_text, bbox=dict(facecolor="white", edgecolor="black"), fontsize=10)
    
    # Legend for node colors.
    import matplotlib.patches as mpatches
    red_patch = mpatches.Patch(color="red", label="Root (H0)")
    blue_patch = mpatches.Patch(color="blue", label="Direct Neighbors")
    green_patch = mpatches.Patch(color="green", label="Allocation Leaves")
    plt.legend(handles=[red_patch, blue_patch, green_patch], loc="lower left")
    
    plt.title("Hierarchical Allocation Tree for Hypernode 0 (Downward)", fontsize=14)
    plt.tight_layout()
    plt.savefig(output_file)
    plt.show()
    print(f"Hierarchical plot saved as {output_file}")

def main():
    json_file = os.path.join("March7", "allocation_4_1x1s.json")
    if not os.path.exists(json_file):
        print("Allocation JSON file not found.")
        return
    allocation_json = load_json(json_file)
    T, alloc_details = build_hierarchy(allocation_json)
    plot_hierarchy_with_key(T, alloc_details)

if __name__ == "__main__":
    main()