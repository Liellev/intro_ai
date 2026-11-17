"""Explicit movement examples. Run with python -B -m unittest discover -v."""

import unittest
from copy import deepcopy

from flat_board_state import flat_board_state


class MovementTests(unittest.TestCase):
    def assert_neighbors(self, board, expected):
        """Compare all returned boards, including multiplicity, without relying on order."""
        neighbors = flat_board_state(board).get_neighbors()
        self.assertIsInstance(neighbors, list)
        actual = []
        for transition in neighbors:
            self.assertIsInstance(transition, tuple)
            self.assertEqual(len(transition), 2)
            state, cost = transition
            self.assertIsInstance(state, flat_board_state)
            self.assertEqual(cost, 1)
            actual.append(state.get_state_board())
        self.assertCountEqual(actual, expected, msg=f"Incorrect neighbors for {board}")

    def test_single_cube_all_four_directions_exactly_one_square(self):
        self.assert_neighbors(
            [[1, 1, 1], [1, 3, 1], [1, 1, 1]],
            [
                [[1, 3, 1], [1, 1, 1], [1, 1, 1]],
                [[1, 1, 1], [1, 1, 1], [1, 3, 1]],
                [[1, 1, 1], [3, 1, 1], [1, 1, 1]],
                [[1, 1, 1], [1, 1, 3], [1, 1, 1]],
            ],
        )

    def test_walls_block_all_four_directions(self):
        self.assert_neighbors([[1, 2, 1], [2, 3, 2], [1, 2, 1]], [])

    def test_horizontal_boundaries(self):
        self.assert_neighbors([[3, 1, 1]], [[[1, 3, 1]]])
        self.assert_neighbors([[1, 1, 3]], [[[1, 3, 1]]])

    def test_vertical_boundaries(self):
        self.assert_neighbors([[3], [1], [1]], [[[1], [3], [1]]])
        self.assert_neighbors([[1], [1], [3]], [[[1], [3], [1]]])

    def test_single_cell_boundary_and_no_op(self):
        self.assert_neighbors([[3]], [])

    def test_hole_filling_all_four_directions(self):
        cases = [
            ([[3, 0]], [[[1, 1]]]),
            ([[0, 3]], [[[1, 1]]]),
            ([[3], [0]], [[[1], [1]]]),
            ([[0], [3]], [[[1], [1]]]),
        ]
        for board, expected in cases:
            with self.subTest(board=board):
                self.assert_neighbors(board, expected)

    def test_adjacent_cubes_move_right(self):
        self.assert_neighbors([[3, 3, 1]], [[[1, 3, 3]]])

    def test_adjacent_cubes_move_left(self):
        self.assert_neighbors([[1, 3, 3]], [[[3, 3, 1]]])

    def test_adjacent_cubes_blocked_by_wall_all_directions(self):
        for board in (
            [[3, 3, 2]], [[2, 3, 3]],
            [[3], [3], [2]], [[2], [3], [3]],
        ):
            with self.subTest(board=board):
                self.assert_neighbors(board, [])

    def test_adjacent_cubes_blocked_by_boundary(self):
        self.assert_neighbors([[3, 3]], [])
        self.assert_neighbors([[3], [3]], [])

    def test_adjacent_cubes_move_down(self):
        self.assert_neighbors([[3], [3], [1]], [[[1], [3], [3]]])

    def test_adjacent_cubes_move_up(self):
        self.assert_neighbors([[1], [3], [3]], [[[3], [3], [1]]])

    def test_multiple_cubes_blocked_cube_stays_while_other_moves(self):
        self.assert_neighbors(
            [[3, 2, 1], [2, 2, 2], [3, 1, 1]],
            [[[3, 2, 1], [2, 2, 2], [1, 3, 1]]],
        )

    def test_separated_cubes_take_same_global_direction(self):
        self.assert_neighbors(
            [[1, 3, 1, 1, 3, 1]],
            [[[3, 1, 1, 3, 1, 1]], [[1, 1, 3, 1, 1, 3]]],
        )

    def test_following_cube_after_hole_filling_all_directions(self):
        cases = [
            ([[3, 3, 0]], [[[1, 3, 1]]]),
            ([[0, 3, 3]], [[[1, 3, 1]]]),
            ([[3], [3], [0]], [[[1], [3], [1]]]),
            ([[0], [3], [3]], [[[1], [3], [1]]]),
        ]
        for board, expected in cases:
            with self.subTest(board=board):
                self.assert_neighbors(board, expected)

    def test_longer_chain_moves_only_one_square(self):
        self.assert_neighbors([[3, 3, 3, 1, 1]], [[[1, 3, 3, 3, 1]]])

    def test_two_cubes_fill_two_holes_in_one_action(self):
        self.assert_neighbors(
            [[3, 0], [2, 2], [3, 0]],
            [[[1, 1], [2, 2], [1, 1]]],
        )

    def test_no_cubes_produces_no_neighbors(self):
        self.assert_neighbors([[1, 2], [1, 1]], [])

    def test_original_input_and_state_unchanged_and_neighbors_independent(self):
        board = [[1, 1, 1], [1, 3, 1], [1, 1, 1]]
        snapshot = deepcopy(board)
        state = flat_board_state(board)
        neighbors = state.get_neighbors()
        self.assertEqual(board, snapshot)
        self.assertEqual(state.get_state_board(), snapshot)
        saved_neighbors = [deepcopy(other.board) for other, _ in neighbors]
        neighbors[0][0].board[0][0] = 2
        self.assertEqual(state.get_state_board(), snapshot)
        self.assertEqual(board, snapshot)
        for index in range(1, len(neighbors)):
            self.assertEqual(neighbors[index][0].board, saved_neighbors[index])
        self.assertEqual(
            [other.board for other, _ in state.get_neighbors()], saved_neighbors
        )


if __name__ == '__main__':
    unittest.main(verbosity=2)
