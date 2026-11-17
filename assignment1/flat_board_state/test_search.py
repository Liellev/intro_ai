"""Tests for OPEN, CLOSED, duplicates, and A*; no submission code is changed."""

import unittest
from collections import deque
from itertools import permutations
from unittest.mock import patch

import search as search_module
from flat_board_state import flat_board_state
from heuristics import base_heuristic
from search_node import search_node


def make_node(column=0, g=0, h=0):
    board = [[1, 1, 1, 0]]
    board[0][column] = 3
    return search_node(flat_board_state(board), g, h)


def board_key(state):
    return tuple(tuple(row) for row in state.get_state_board())


def bfs_distance(board):
    """Independent FIFO search, using the already tested movement generator.

    Does not use search.py, its duplicate functions, or any heuristic.
    """
    start = flat_board_state(board)
    queue = deque([(start, 0)])
    visited = {board_key(start)}
    while queue:
        state, distance = queue.popleft()
        if flat_board_state.is_goal_state(state):
            return distance
        for neighbor, cost in state.get_neighbors():
            if cost != 1:
                raise AssertionError('BFS assumes unit movement costs')
            key = board_key(neighbor)
            if key not in visited:
                visited.add(key)
                queue.append((neighbor, distance + 1))
    return None


class OpenTests(unittest.TestCase):
    def test_empty_and_insert(self):
        opened = search_module.create_open_set()
        self.assertFalse(search_module.open_not_empty(opened))
        node = make_node()
        search_module.add_to_open(node, opened)
        self.assertTrue(search_module.open_not_empty(opened))
        self.assertIs(search_module.get_best(opened), node)
        self.assertFalse(search_module.open_not_empty(opened))

    def test_lowest_f_removed_first(self):
        opened = search_module.create_open_set()
        high = make_node(0, 4, 3)
        low = make_node(1, 1, 1)
        search_module.add_to_open(high, opened)
        search_module.add_to_open(low, opened)
        self.assertIs(search_module.get_best(opened), low)
        self.assertIs(search_module.get_best(opened), high)
        self.assertFalse(search_module.open_not_empty(opened))

    def test_equal_f_prefers_lower_h(self):
        opened = search_module.create_open_set()
        high_h = make_node(0, 1, 3)
        low_h = make_node(1, 3, 1)
        self.assertTrue(low_h < high_h)
        search_module.add_to_open(high_h, opened)
        search_module.add_to_open(low_h, opened)
        self.assertIs(search_module.get_best(opened), low_h)

    def test_priority_order_for_all_insertion_orders(self):
        first = make_node(0, 1, 1)  # f=2
        second = make_node(1, 3, 1)  # f=4, h=1
        third = make_node(2, 1, 3)  # f=4, h=3
        for order in permutations([first, second, third]):
            with self.subTest(order=[node.g for node in order]):
                opened = search_module.create_open_set()
                for node in order:
                    search_module.add_to_open(node, opened)
                self.assertEqual(
                    [search_module.get_best(opened) for _ in range(3)],
                    [first, second, third],
                )
                self.assertFalse(search_module.open_not_empty(opened))

    def test_equal_priority_nodes_both_preserved(self):
        opened = search_module.create_open_set()
        nodes = [make_node(0, 1, 1), make_node(1, 1, 1)]
        for node in nodes:
            search_module.add_to_open(node, opened)
        self.assertCountEqual(
            [search_module.get_best(opened), search_module.get_best(opened)], nodes
        )

    def test_empty_get_best_raises(self):
        with self.assertRaises(IndexError):
            search_module.get_best(search_module.create_open_set())

    def test_open_instances_are_independent(self):
        first = search_module.create_open_set()
        second = search_module.create_open_set()
        search_module.add_to_open(make_node(), first)
        self.assertFalse(search_module.open_not_empty(second))


class ClosedTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(search_module.create_closed_set(), {})

    def test_store_and_retrieve(self):
        closed = search_module.create_closed_set()
        node = make_node()
        search_module.add_to_closed(node, closed)
        self.assertIs(closed[search_module.get_state_key(node)], node)

    def test_different_states_stored_independently(self):
        closed = search_module.create_closed_set()
        first, second = make_node(0), make_node(1)
        search_module.add_to_closed(first, closed)
        search_module.add_to_closed(second, closed)
        self.assertEqual(len(closed), 2)
        self.assertIs(closed[search_module.get_state_key(first)], first)
        self.assertIs(closed[search_module.get_state_key(second)], second)
        self.assertEqual(search_module.create_closed_set(), {})


class DuplicateTests(unittest.TestCase):
    def check_duplicate(self, structure_name, candidate_g, expected):
        if structure_name == 'open':
            structure = search_module.create_open_set()
            add = search_module.add_to_open
            duplicate = search_module.duplicate_in_open
            active = structure['nodes']
        else:
            structure = search_module.create_closed_set()
            add = search_module.add_to_closed
            duplicate = search_module.duplicate_in_closed
            active = structure
        original = make_node(0, 5, 2)
        candidate = make_node(0, candidate_g, 2)
        self.assertIsNot(original.state, candidate.state)
        add(original, structure)
        self.assertEqual(duplicate(candidate, structure), expected)
        key = search_module.get_state_key(original)
        if expected:
            self.assertIs(active[key], original)
        else:
            self.assertNotIn(key, active)
            add(candidate, structure)
            self.assertIs(active[key], candidate)

    def test_higher_g_rejected(self):
        for name in ('open', 'closed'):
            with self.subTest(structure=name):
                self.check_duplicate(name, 6, True)

    def test_equal_g_rejected(self):
        for name in ('open', 'closed'):
            with self.subTest(structure=name):
                self.check_duplicate(name, 5, True)

    def test_lower_g_invalidates_old_node(self):
        for name in ('open', 'closed'):
            with self.subTest(structure=name):
                self.check_duplicate(name, 2, False)

    def test_absent_and_different_states_are_not_duplicates(self):
        opened = search_module.create_open_set()
        closed = search_module.create_closed_set()
        for structure, add, duplicate in (
            (opened, search_module.add_to_open, search_module.duplicate_in_open),
            (closed, search_module.add_to_closed, search_module.duplicate_in_closed),
        ):
            self.assertFalse(duplicate(make_node(0), structure))
            add(make_node(0), structure)
            self.assertFalse(duplicate(make_node(1), structure))

    def test_stale_heap_entry_skipped_before_active_node(self):
        opened = search_module.create_open_set()
        old = make_node(0, 5, 1)
        better = make_node(0, 2, 1)
        other = make_node(1, 9, 1)
        search_module.add_to_open(old, opened)
        self.assertFalse(search_module.duplicate_in_open(better, opened))
        search_module.add_to_open(better, opened)
        search_module.add_to_open(other, opened)
        self.assertIs(search_module.get_best(opened), better)
        # Old f=6 entry precedes other's f=10 entry in the heap.
        self.assertIs(search_module.get_best(opened), other)
        self.assertFalse(search_module.open_not_empty(opened))

    def test_only_stale_entries_do_not_keep_open_active(self):
        opened = search_module.create_open_set()
        search_module.add_to_open(make_node(0, 5), opened)
        self.assertFalse(search_module.duplicate_in_open(make_node(0, 1), opened))
        self.assertFalse(search_module.open_not_empty(opened))
        with self.assertRaises(IndexError):
            search_module.get_best(opened)

    def test_closed_state_can_be_reopened(self):
        opened = search_module.create_open_set()
        closed = search_module.create_closed_set()
        search_module.add_to_closed(make_node(0, 5), closed)
        better = make_node(0, 2)
        self.assertFalse(search_module.duplicate_in_closed(better, closed))
        search_module.add_to_open(better, opened)
        self.assertEqual(closed, {})
        self.assertIs(search_module.get_best(opened), better)


class SearchTests(unittest.TestCase):
    def run_search(self, board):
        # Fail with a clear message instead of hanging on a duplicate/cycle bug.
        real_get_best = search_module.get_best
        calls = 0

        def bounded_get_best(opened):
            nonlocal calls
            calls += 1
            if calls > 1000:
                self.fail('Search exceeded 1000 pops on a tiny board; possible cycle bug')
            return real_get_best(opened)

        with patch.object(search_module, 'get_best', bounded_get_best):
            return search_module.search(flat_board_state(board), base_heuristic)

    def assert_solution(self, board, steps):
        path = self.run_search(board)
        self.assertIsNotNone(path)
        self.assertEqual(len(path) - 1, steps)
        self.assertEqual(path[0].state.get_state_board(), board)
        self.assertIsNone(path[0].prev)
        self.assertTrue(flat_board_state.is_goal_state(path[-1].state))
        for index, node in enumerate(path):
            self.assertEqual(node.g, index)
            self.assertEqual(node.h, base_heuristic(node.state))
            self.assertEqual(node.f, node.g + node.h)
            if index:
                previous = path[index - 1]
                self.assertIs(node.prev, previous)
                legal_boards = [state.get_state_board()
                                for state, _ in previous.state.get_neighbors()]
                self.assertIn(node.state.get_state_board(), legal_boards)
        return path

    def test_already_solved(self):
        self.assert_solution([[1, 2], [1, 1]], 0)
        self.assertEqual(search_module.get_gen_exp_count(), (0, 0))

    def test_one_step_and_cube_disappears(self):
        path = self.assert_solution([[3, 0]], 1)
        self.assertEqual(path[-1].state.get_state_board(), [[1, 1]])

    def test_multiple_steps(self):
        path = self.assert_solution([[3, 1, 1, 0]], 3)
        self.assertEqual([node.state.get_state_board() for node in path],
                         [[[3, 1, 1, 0]], [[1, 3, 1, 0]],
                          [[1, 1, 3, 0]], [[1, 1, 1, 1]]])

    def test_adjacent_cubes_follow_into_holes(self):
        self.assert_solution([[3, 3, 0, 0]], 3)

    def test_multiple_cubes_fill_holes_simultaneously(self):
        self.assert_solution([[3, 0], [3, 0]], 1)

    def test_wall_requires_multiple_directions(self):
        # Down, right, right, up: four steps around the central wall.
        self.assert_solution([[3, 2, 0], [1, 1, 1]], 4)

    def test_blocked_cube_and_unsolvable_board(self):
        self.assertIsNone(self.run_search([[3, 3, 2, 0, 0]]))

    def test_unsolvable_board_with_cycles_terminates(self):
        self.assertIsNone(self.run_search([[3, 1, 2, 0]]))
        # Exactly two reachable states; going right then left revisits the start.
        self.assertEqual(search_module.get_gen_exp_count(), (1, 2))

    def test_converging_action_sequences(self):
        board = [[3, 1, 1], [1, 1, 1], [1, 1, 0]]
        self.assert_solution(board, 4)
        # Right/down and down/right both reach (1, 1).
        self.assertLessEqual(search_module.get_gen_exp_count()[1], 9)

    def test_astar_matches_independent_bfs(self):
        boards = [
            [[1]], [[3, 0]], [[0, 1, 3]], [[3, 1, 1, 0]],
            [[3, 3, 0, 0]], [[0, 0, 3, 3]], [[3, 0], [3, 0]],
            [[3, 2, 0], [1, 1, 1]],
            [[3, 1, 1], [1, 1, 1], [1, 1, 0]],
            [[3, 1, 2, 0]], [[3, 3, 2, 0, 0]],
        ]
        for board in boards:
            with self.subTest(board=board):
                cells = [cell for row in board for cell in row]
                self.assertEqual(cells.count(0), cells.count(3))
                expected = bfs_distance(board)
                if expected is None:
                    self.assertIsNone(self.run_search(board))
                else:
                    self.assert_solution(board, expected)

    def test_counters_reset_between_searches(self):
        self.assert_solution([[3, 1, 1, 0]], 3)
        first_counts = search_module.get_gen_exp_count()
        for count in first_counts:
            self.assertIsInstance(count, int)
            self.assertGreaterEqual(count, 0)
        self.assertGreater(first_counts[1], 0)
        self.assert_solution([[3, 0]], 1)
        self.assertEqual(search_module.get_gen_exp_count(), (1, 1))
        self.assert_solution([[1]], 0)
        self.assertEqual(search_module.get_gen_exp_count(), (0, 0))


if __name__ == '__main__':
    unittest.main(verbosity=2)
