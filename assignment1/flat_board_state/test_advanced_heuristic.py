"""Check advanced estimates against exact, heuristic-independent BFS costs."""

import unittest
from collections import deque
from copy import deepcopy
from itertools import combinations, product

from flat_board_state import flat_board_state
from heuristics import advanced_heuristic, base_heuristic
from search import search


def key(state):
    return tuple(tuple(row) for row in state.get_state_board())


def bfs_cost(board):
    """FIFO BFS: unit edges, visited states, no A* or heuristic calls."""
    start = flat_board_state(board)
    queue = deque([(start, 0)])
    visited = {key(start)}
    while queue:
        state, cost = queue.popleft()
        if flat_board_state.is_goal_state(state):
            return cost
        for neighbor, edge_cost in state.get_neighbors():
            if edge_cost != 1:
                raise AssertionError('BFS requires unit costs')
            neighbor_key = key(neighbor)
            if neighbor_key not in visited:
                visited.add(neighbor_key)
                queue.append((neighbor, cost + 1))
    return None


def small_boards():
    # Every 2x3 configuration over all four cell values with balanced counts.
    for cells in product((0, 1, 2, 3), repeat=6):
        if cells.count(0) == cells.count(3):
            yield [list(cells[:3]), list(cells[3:])]
    # All wall-free 3x3 boards with one, two, or three cube/hole pairs.
    for count in (1, 2, 3):
        for cubes in combinations(range(9), count):
            available = [index for index in range(9) if index not in cubes]
            for holes in combinations(available, count):
                cells = [1] * 9
                for index in cubes:
                    cells[index] = 3
                for index in holes:
                    cells[index] = 0
                yield [cells[:3], cells[3:6], cells[6:]]


class AdvancedHeuristicTests(unittest.TestCase):
    def check_example(self, board, expected, optimal):
        original = deepcopy(board)
        state = flat_board_state(board)
        actual = advanced_heuristic(state)
        self.assertEqual(actual, expected)
        self.assertGreaterEqual(actual, base_heuristic(state))
        self.assertEqual(bfs_cost(board), optimal)
        if optimal is not None:
            self.assertLessEqual(actual, optimal)
        self.assertEqual(state.get_state_board(), original)
        self.assertEqual(board, original)

    def test_goal(self):
        self.check_example([[1, 2], [1, 1]], 0, 0)

    def test_right(self):
        self.check_example([[3, 1, 0]], 2, 2)

    def test_left(self):
        self.check_example([[0, 1, 3]], 2, 2)

    def test_up(self):
        self.check_example([[0], [1], [3]], 2, 2)

    def test_down(self):
        self.check_example([[3], [1], [0]], 2, 2)

    def test_diagonal(self):
        self.check_example([[3, 1, 1], [1, 1, 0]], 3, 3)

    def test_adjacent_cubes_same_row(self):
        # Sorted columns: cubes [0,1], holes [2,3]; need >=2 rights.
        # Actual solution needs 3 rights because each cube disappears in a hole.
        self.check_example([[3, 3, 0, 0]], 2, 3)

    def test_simultaneous_cubes_in_different_rows(self):
        self.check_example([[3, 1, 0], [3, 1, 0]], 2, 2)

    def test_opposite_horizontal_directions_stronger_than_base(self):
        board = [[0, 3, 1], [2, 2, 2], [1, 3, 0]]
        # Left fills the top hole but moves the bottom cube to column 0.
        # Two right moves then fill the bottom hole: three actions in total.
        self.check_example(board, 2, 3)
        self.assertEqual(base_heuristic(flat_board_state(board)), 1)

    def test_opposite_vertical_directions(self):
        # Up, down, down (or down, up, up): three actions.
        self.check_example([[0, 2, 1], [3, 2, 3], [1, 2, 0]], 2, 3)

    def test_three_pairs_and_repeated_calls(self):
        board = [[3, 3, 3, 1], [1, 1, 1, 1], [0, 1, 0, 0]]
        # Two downward moves and at least one rightward move: bound 3.
        self.check_example(board, 3, 4)
        state = flat_board_state(board)
        self.assertEqual(advanced_heuristic(state), advanced_heuristic(state))

    def test_walls_require_detour(self):
        self.check_example([[3, 2, 0], [1, 1, 1]], 2, 4)

    def test_unsolvable_board_is_not_an_admissibility_counterexample(self):
        self.check_example([[3, 2, 0]], 2, None)

    def test_deterministic_exhaustive_collection(self):
        totals = dict(boards=0, solvable=0, unsolvable=0, stronger=0, edges=0)
        max_gain = 0
        max_example = None
        for board in small_boards():
            with self.subTest(board=board):
                totals['boards'] += 1
                state = flat_board_state(board)
                snapshot = deepcopy(board)
                base = base_heuristic(state)
                advanced = advanced_heuristic(state)
                self.assertGreaterEqual(advanced, base)
                self.assertGreaterEqual(advanced, 0)
                if advanced > base:
                    totals['stronger'] += 1
                if advanced - base > max_gain:
                    max_gain = advanced - base
                    max_example = board
                optimal = bfs_cost(board)
                if optimal is None:
                    totals['unsolvable'] += 1
                else:
                    totals['solvable'] += 1
                    self.assertLessEqual(advanced, optimal,
                                         msg=f'Overestimate: h={advanced}, BFS={optimal}')
                # Integration check: A* with the advanced heuristic matches BFS.
                path = search(state, advanced_heuristic)
                actual_cost = None if path is None else len(path) - 1
                self.assertEqual(actual_cost, optimal)
                for neighbor, cost in state.get_neighbors():
                    totals['edges'] += 1
                    self.assertLessEqual(advanced, cost + advanced_heuristic(neighbor),
                                         msg='Inconsistent estimate across a legal edge')
                self.assertEqual(state.get_state_board(), snapshot)
                self.assertEqual(board, snapshot)
        print(f'\nExhaustive totals: {totals}; largest gain={max_gain}; example={max_example}',
              flush=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
