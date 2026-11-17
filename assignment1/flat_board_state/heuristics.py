import math




def base_heuristic(_flat_board_state):

    # Step 1: Check if the state is a goal state
    if _flat_board_state.is_goal_state(_flat_board_state):
        return 0

    board = _flat_board_state.get_state_board()

    cubes = []
    holes = []

    # Step 2: Find all cubes and holes
    for row in range(len(board)):
        for col in range(len(board[row])):

            if board[row][col] == 3:
                cubes.append((row, col))

            elif board[row][col] == 0:
                holes.append((row, col))

    max_distance = 0

    # Step 3: Find the closest cube for each hole
    for hole in holes:

        min_distance = float('inf')

        for cube in cubes:

            # Calculate Manhattan distance
            distance = abs(hole[0] - cube[0]) + abs(hole[1] - cube[1])

            if distance < min_distance:
                min_distance = distance

        # Step 4: Find the maximum of all minimum distances
        if min_distance > max_distance:
            max_distance = min_distance

    return max_distance





def advanced_heuristic(_flat_board_state):

    # Step 1: Check goal state
    if _flat_board_state.is_goal_state(_flat_board_state):
        return 0

    board = _flat_board_state.get_state_board()

    cube_rows = []
    cube_cols = []
    hole_rows = []
    hole_cols = []

    # Step 2: Find cubes and holes
    for row in range(len(board)):
        for col in range(len(board[row])):

            if board[row][col] == 3:
                cube_rows.append(row)
                cube_cols.append(col)

            elif board[row][col] == 0:
                hole_rows.append(row)
                hole_cols.append(col)

    # Step 3: Sort coordinates
    cube_rows.sort()
    cube_cols.sort()
    hole_rows.sort()
    hole_cols.sort()

    right_moves = 0
    left_moves = 0
    up_moves = 0
    down_moves = 0

    # Step 4: Calculate required horizontal moves
    for i in range(len(cube_cols)):

        difference = hole_cols[i] - cube_cols[i]

        if difference > 0:
            right_moves = max(right_moves, difference)

        elif difference < 0:
            left_moves = max(left_moves, -difference)

    # Step 5: Calculate required vertical moves
    for i in range(len(cube_rows)):

        difference = hole_rows[i] - cube_rows[i]

        if difference > 0:
            down_moves = max(down_moves, difference)

        elif difference < 0:
            up_moves = max(up_moves, -difference)

    # Step 6: Lower bound based on required directions
    direction_heuristic = (
        right_moves +
        left_moves +
        up_moves +
        down_moves
    )

    # Step 7: Combine with base heuristic
    base = base_heuristic(_flat_board_state)

    return max(base, direction_heuristic)


