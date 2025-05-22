'''
This file is set up to take in the puzzle_config.json file

After taking this in, we will find all potential configurations of the larger blocks (non-overlapping)

This is then stored into the March7, "hyperNode.json" file", where March7 is the folder that contains the hyperNode.json file

If the piece is starred, we will treat it always as a unique piece

We want to take every output as a unique configuration, and store it in the hyperNode.json file

This will then be used as the top level of the graph
'''

import json
import os
import networkx as nx

def load_hypernodes(folder="March7", filename="hyperNode.json"):
    """Loads the hypernodes from the stored JSON file."""
    hypernode_file = os.path.join(folder, filename)
    if not os.path.exists(hypernode_file):
        print(f"Error: {hypernode_file} not found!")
        return None

    with open(hypernode_file, "r") as f:
        return json.load(f)

def get_move_info(state_a, state_b):
    """
    Determines if two hypernodes differ by exactly one move.
    Returns a dictionary with move details if they are one move away.
    Otherwise, returns None.
    
    It compares the pieces (by their "cells") and, if exactly one piece
    has changed, returns a dictionary with 'moved_from' and 'moved_to'.
    """
    # Represent each piece by a sorted tuple of its cell coordinates.
    pieces_a = [tuple(sorted(map(tuple, piece["cells"]))) for piece in state_a["pieces"]]
    pieces_b = [tuple(sorted(map(tuple, piece["cells"]))) for piece in state_b["pieces"]]

    set_a = set(pieces_a)
    set_b = set(pieces_b)

    diff_a = set_a - set_b
    diff_b = set_b - set_a

    if len(diff_a) == 1 and len(diff_b) == 1:
        moved_from = list(diff_a)[0]
        moved_to = list(diff_b)[0]
        return {"moved_from": moved_from, "moved_to": moved_to}
    return None

def build_hypernode_graph(hypernodes):
    """
    Builds a graph where each unique valid arrangement is treated as a node.
    Each hypernode is assigned a label to facilitate plotting.
    Two nodes are connected by an edge if they are exactly one move away.
    The edge stores move details that indicate how the two hypernodes are connected.
    """
    G = nx.Graph()
    
    # Add nodes with board, pieces, and a label attribute.
    for i, hypernode in enumerate(hypernodes):
        label = f"Hypernode {i}"
        G.add_node(i, board=hypernode["board"], pieces=hypernode["pieces"], label=label)
    
    # Compare each pair of hypernodes.
    for i in range(len(hypernodes)):
        for j in range(i + 1, len(hypernodes)):
            move_info = get_move_info(hypernodes[i], hypernodes[j])
            if move_info is not None:
                G.add_edge(i, j, move=move_info)
    
    return G

def find_connected_components(G):
    """Finds all connected components in the hypernode graph and returns them in a JSON-serializable format."""
    components = list(nx.connected_components(G))
    component_data = []
    for i, component in enumerate(components):
        component_data.append({
            "component_id": i,
            "nodes": list(component)
        })
    return component_data

def save_connected_components(components, folder="March7", filename="components.json"):
    """Saves the connected components data to a JSON file."""
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    component_file = os.path.join(folder, filename)
    with open(component_file, "w") as f:
        json.dump(components, f, indent=2)
    
    print(f"Connected components saved to {component_file}")

def get_edge_info(G):
    """
    Extracts information about all edges in the graph.
    Each edge entry includes:
      - 'source': index of the starting hypernode
      - 'target': index of the connected hypernode
      - 'move': details about the move (if available) that connects them
    """
    edge_list = []
    for source, target, data in G.edges(data=True):
        edge_entry = {
            "source": source,
            "target": target
        }
        if "move" in data:
            edge_entry["move"] = data["move"]
        edge_list.append(edge_entry)
    return edge_list

def save_edge_info(edge_list, folder="March7", filename="edges.json"):
    """Saves the edge information to a JSON file."""
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    edge_file = os.path.join(folder, filename)
    with open(edge_file, "w") as f:
        json.dump(edge_list, f, indent=2)
    
    print(f"Edge information saved to {edge_file}")

def get_node_info(G):
    """
    Extracts node information from the graph.
    Each node entry includes:
      - 'id': the node's index
      - 'label': the assigned label for plotting
    """
    node_list = []
    for node, data in G.nodes(data=True):
        node_list.append({
            "id": node,
            "label": data.get("label", f"Node {node}")
        })
    return node_list

def save_node_info(node_list, folder="March7", filename="nodes.json"):
    """Saves the node (hypernode) information to a JSON file."""
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    node_file = os.path.join(folder, filename)
    with open(node_file, "w") as f:
        json.dump(node_list, f, indent=2)
    
    print(f"Node information saved to {node_file}")

def main():
    hypernodes = load_hypernodes()
    if not hypernodes:
        return
    
    # Build the hypernode graph.
    G = build_hypernode_graph(hypernodes)
    
    # Save node information with labels.
    node_list = get_node_info(G)
    save_node_info(node_list)
    
    # Find and save connected components.
    components = find_connected_components(G)
    save_connected_components(components)
    
    # Extract and save edge information detailing direct connections and move details.
    edge_list = get_edge_info(G)
    save_edge_info(edge_list)

if __name__ == "__main__":
    main()
