import json
import os
import random
from itertools import combinations
from collections import deque

import networkx as nx


def load_puzzle_config(file_path="puzzle_config.json"):
    """Load the puzzle configuration from a JSON file."""
    if not os.path.exists(file_path):
        print("Error: Puzzle configuration file not found!")
        return None
    with open(file_path, "r") as f:
        return json.load(f)


def count_valid_arrangements(puzzle_data):
    """
    Count unique valid, non-overlapping arrangements from puzzle_data.
    Each unique valid board arrangement is treated as a Hyper-Node in a graph.
    """
    rows, cols = puzzle_data["rows"], puzzle_data["cols"]
    num_1x2 = sum(1 for p in puzzle_data["pieces"] if p["piece_type"] == "1x2")
    num_2x1 = sum(1 for p in puzzle_data["pieces"] if p["piece_type"] == "2x1")

    placements_h = [((r, c), (r, c + 1)) for r in range(rows) for c in range(cols - 1)]
    placements_v = [((r, c), (r + 1, c)) for r in range(rows - 1) for c in range(cols)]

    valid_states = set()
    for chosen_h in combinations(placements_h, num_1x2):
        for chosen_v in combinations(placements_v, num_2x1):
            occupied = set()
            state = []
            valid = True
            for piece in chosen_h + chosen_v:
                if piece[0] in occupied or piece[1] in occupied:
                    valid = False
                    break
                occupied.update(piece)
                state.append(piece)
            if valid:
                valid_states.add(frozenset(state))
    print(f"Total unique valid arrangements (Hyper-Nodes): {len(valid_states)}")
    return valid_states


def count_supernode_arrangements(hyper_state, puzzle_data):
    """
    Count the number of ways to place 4 blocks in the remaining empty spaces of a Hyper-Node.
    """
    rows, cols = puzzle_data["rows"], puzzle_data["cols"]
    total_cells = {(r, c) for r in range(rows) for c in range(cols)}
    occupied_cells = {cell for piece in hyper_state for cell in piece}
    empty_spaces = list(total_cells - occupied_cells)
    if len(empty_spaces) < 4:
        return []
    return list(combinations(empty_spaces, 4))


def can_reach_solution(super_state, puzzle_data):
    """
    Check if the target piece can reach the bottom-left goal from a given Super-Node.
    """
    rows, cols = puzzle_data["rows"], puzzle_data["cols"]
    target_label = puzzle_data["target"]
    pieces = puzzle_data["pieces"]

    target_pos = None
    for piece in pieces:
        if piece["label"] == target_label:
            target_pos = (piece["row"], piece["col"])
            break
    if target_pos is None:
        return False

    goal_pos = (rows - 1, 0)
    queue = deque([target_pos])
    visited = {target_pos}
    moves = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    while queue:
        current = queue.popleft()
        if current == goal_pos:
            return True
        for dr, dc in moves:
            new_pos = (current[0] + dr, current[1] + dc)
            if (0 <= new_pos[0] < rows and 0 <= new_pos[1] < cols and
                    new_pos not in visited and new_pos not in super_state):
                visited.add(new_pos)
                queue.append(new_pos)
    return False


def build_hyper_super_structure(valid_states, puzzle_data):
    """
    Builds a three-tiered data structure instead of plotting:
    - Hyper-Nodes (H)
    - Super-Nodes (S)
    - Reachability to Solution
    """
    structure = {}

    for idx, state in enumerate(valid_states):
        hyper_label = f"H{idx}"
        structure[hyper_label] = {"super_nodes": {}}

        super_arrangements = count_supernode_arrangements(state, puzzle_data)

        for i, super_state in enumerate(super_arrangements):
            super_label = f"S{idx}_{i}"
            can_reach = can_reach_solution(set(super_state), puzzle_data)

            structure[hyper_label]["super_nodes"][super_label] = {
                "can_reach_solution": can_reach
            }

    return structure


def save_structure_to_json(structure, file_name="structData.json"):
    """
    Save the three-tiered structure to a JSON file.
    """
    with open(file_name, "w") as f:
        json.dump(structure, f, indent=4)
    print(f"Structure saved to {file_name}")


def main():
    puzzle_data = load_puzzle_config()
    if not puzzle_data:
        return

    valid_states = count_valid_arrangements(puzzle_data)
    structure = build_hyper_super_structure(valid_states, puzzle_data)

    # Save the structure to a JSON file
    save_structure_to_json(structure)


if __name__ == "__main__":
    main()