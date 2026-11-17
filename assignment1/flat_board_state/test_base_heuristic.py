"""Manually calculated examples for base_heuristic only."""

import unittest
from copy import deepcopy

from flat_board_state import flat_board_state
from heuristics import base_heuristic


class BaseHeuristicTests(unittest.TestCase):
    def assert_heuristic(self, board, expected):
        # Every example has equal numbers of cubes and holes.
        cells = [cell for row in board for cell in row]
        self.assertEqual(cells.count(3), cells.count(0))
        self.assertEqual(base_heuristic(flat_board_state(board)), expected)

    def test_goal_state_returns_zero(self):
        self.assert_heuristic([[1, 2], [1, 1]], 0)

    def test_single_cube_adjacent_hole(self):
        self.assert_heuristic([[3, 0]], 1)

    def test_single_cube_horizontal_distance(self):
        self.assert_heuristic([[0, 1, 1, 3]], 3)

    def test_single_cube_vertical_distance(self):
        self.assert_heuristic([[3], [1], [1], [0]], 3)

    def test_single_cube_diagonal_distance(self):
        # (0, 0) to (2, 3): 2 + 3 = 5.
        self.assert_heuristic(
            [[3, 1, 1, 1], [1, 1, 1, 1], [1, 1, 1, 0]], 5
        )

    def test_maximum_of_minimum_distances_not_sum(self):
        # Cubes: (0, 0), (0, 6). Holes: (0, 1), (0, 4).
        # Nearest distances: min(1, 5) = 1, min(4, 2) = 2.
        # Return max(1, 2) = 2, rather than their sum, 3.
        self.assert_heuristic([[3, 0, 1, 1, 0, 1, 3]], 2)

    def test_multiple_cubes_and_holes_in_two_dimensions(self):
        # Cubes: (0, 0), (0, 4), (3, 0).
        # Holes: (0, 2), (2, 4), (3, 1).
        # Distance lists: (2, 2, 5), (6, 2, 5), (4, 6, 1).
        # Minimum distances are 2, 2, 1; their maximum is 2.
        self.assert_heuristic(
            [[3, 1, 0, 1, 3],
             [1, 1, 1, 1, 1],
             [1, 1, 1, 1, 0],
             [3, 0, 1, 1, 1]],
            2,
        )

    def test_same_cube_can_be_nearest_to_more_than_one_hole(self):
        # Holes at columns 1 and 2 are both nearest to the cube at 0.
        # The cube at 6 need not be assigned to either hole: max(1, 2) = 2.
        self.assert_heuristic([[3, 0, 0, 1, 1, 1, 3]], 2)

    def test_walls_do_not_increase_manhattan_distance(self):
        # A wall forces a walking detour, but Manhattan distance remains 2.
        self.assert_heuristic([[3, 2, 0], [1, 1, 1]], 2)
        self.assert_heuristic([[3, 1, 0], [1, 1, 1]], 2)

    def test_call_does_not_modify_board(self):
        board = [[3, 2, 0], [0, 1, 3]]
        original = deepcopy(board)
        state = flat_board_state(board)
        # Each hole is one step from its closest cube.
        # (1, 0) is below (0, 0); (0, 2) is above (1, 2).
        self.assertEqual(base_heuristic(state), 1)
        self.assertEqual(state.get_state_board(), original)
        self.assertEqual(board, original)
        self.assertEqual(base_heuristic(state), 1)
        self.assertEqual(state.get_state_board(), original)


if __name__ == '__main__':
    unittest.main(verbosity=2)
