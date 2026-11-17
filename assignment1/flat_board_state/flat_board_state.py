# you can add global params

class flat_board_state:
    def __init__(self, instance_map=None, *args, **kwargs):
        # Copy each row so changes to this state do not affect the input board.
        self.board = [list(row) for row in instance_map] if instance_map is not None else []
        self.rows = len(self.board)
        self.cols = len(self.board[0]) if self.rows else 0

    @staticmethod
    def is_goal_state(_flat_board_state):
        for row in _flat_board_state.board:
            for cell in row:
                if cell == 0:
                    return False
        return True

    
    def get_neighbors(self):
        neighbors = []

        original_board = self.get_state_board()

        rows = len(original_board)
        cols = len(original_board[0])

        # Each direction is represented by (row_change, col_change)
        directions = [
            (-1, 0),  # Up
            (1, 0),   # Down
            (0, -1),  # Left
            (0, 1)    # Right
        ]

        # Try each of the four directions
        for dr, dc in directions:

            # Create a separate copy for this direction
            new_board = self.get_state_board()

            # Choose the order in which we scan the board
            if dr == -1:  # Up
                row_order = range(rows)
                col_order = range(cols)

            elif dr == 1:  # Down
                row_order = range(rows - 1, -1, -1)
                col_order = range(cols)

            elif dc == -1:  # Left
                row_order = range(rows)
                col_order = range(cols)

            else:  # Right
                row_order = range(rows)
                col_order = range(cols - 1, -1, -1)

            # Go over all the cells in the chosen order
            for r in row_order:
                for c in col_order:

                    # Only cubes can move
                    if new_board[r][c] != 3:
                        continue

                    # Calculate the next position
                    new_r = r + dr
                    new_c = c + dc

                    # Check if the next position is inside the board
                    if new_r < 0 or new_r >= rows:
                        continue

                    if new_c < 0 or new_c >= cols:
                        continue

                    next_cell = new_board[new_r][new_c]

                    # A cube cannot move into a wall or blocked cube
                    if next_cell == 2 or next_cell == 3:
                        continue

                    # The cube leaves its original position
                    new_board[r][c] = 1

                    if next_cell == 0:
                        # The cube fills the hole and disappears
                        new_board[new_r][new_c] = 1

                    elif next_cell == 1:
                        # The cube moves to an empty square
                        new_board[new_r][new_c] = 3

            # Add the new state only if the board changed
            if new_board != original_board:
                new_state = flat_board_state(new_board)

                # Every action costs 1
                neighbors.append((new_state, 1))

        return neighbors


    # you can change the body of the function if you want
    # def __hash__(self):

    # you can change the body of the function if you want
    # def __eq__(self, other):
    # you can change the body of the function if you want

    def get_state_board(self):
        return [row[:] for row in self.board]

    def get_state_str(self):
        board = self.get_state_board()
        result = ""

        for row in board:
            for cell in row:
                result += str(cell) + " "

            result += "\n"

        return result

    # you can add helper functions
