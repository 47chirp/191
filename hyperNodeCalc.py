def generate_domino_placements():
    board_rows = 3
    board_cols = 4
    horizontal_positions = []
    vertical_positions = []
    # Horizontal domino placements: (r, c) and (r, c+1)
    for r in range(board_rows):
        for c in range(board_cols - 1):
            horizontal_positions.append(((r, c), (r, c+1)))
    # Vertical domino placements: (r, c) and (r+1, c)
    for r in range(board_rows - 1):
        for c in range(board_cols):
            vertical_positions.append(((r, c), (r+1, c)))
    
    return horizontal_positions, vertical_positions

def enumerate_placements():
    horizontal, vertical = generate_domino_placements()
    possibilities = []
    # Loop over each vertical domino placement.
    for v in vertical:
        v_cells = set(v)
        # Loop over choices for first horizontal domino (H1).
        for i, h1 in enumerate(horizontal):
            h1_cells = set(h1)
            # Check H1 does not overlap with V.
            if v_cells & h1_cells:
                continue
            # Loop over choices for second horizontal domino (H2).
            for j, h2 in enumerate(horizontal):
                if j == i:  # Ensure H1 and H2 are different placements.
                    continue
                h2_cells = set(h2)
                # Check H2 does not overlap with V or H1.
                if v_cells & h2_cells:
                    continue
                if h1_cells & h2_cells:
                    continue
                possibilities.append({
                    "H1": h1,
                    "H2": h2,
                    "V": v
                })
    return possibilities

possibilities = enumerate_placements()

print("Number of possibilities:", len(possibilities))
for idx, placement in enumerate(possibilities, 1):
    print(f"{idx}: H1: {placement['H1']}, H2: {placement['H2']}, V: {placement['V']}")