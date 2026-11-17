"""Reproducible A* baseline. Run: py -3.10 -B benchmark.py

Each board runs in a child process. Timing includes search() only, excluding
state construction, process startup, result checking, and communication.
"""

import argparse
import csv
import json
import multiprocessing
import platform
import statistics
import time
import traceback
from pathlib import Path

from flat_board_state import flat_board_state
from heuristics import base_heuristic
from search import search, get_gen_exp_count


BOARDS = [
    ('Very easy', [[3, 0]]),
    ('Easy', [[3, 3, 0, 0]]),
    ('Medium', [[3, 3, 3, 1], [1, 1, 1, 1], [0, 1, 0, 0]]),
    ('Hard', [[3, 3, 0], [2, 2, 1], [0, 1, 1]]),
    ('Challenging', [
        [3, 1, 3, 1, 1, 0],
        [1, 2, 1, 2, 1, 1],
        [1, 1, 1, 1, 1, 1],
        [3, 2, 1, 2, 1, 0],
        [1, 1, 0, 1, 1, 1],
    ]),
]


def validate_board(board):
    if not board or not board[0]:
        raise ValueError('Board must be nonempty')
    if any(len(row) != len(board[0]) for row in board):
        raise ValueError('Board must be rectangular')
    cells = [cell for row in board for cell in row]
    if any(cell not in (0, 1, 2, 3) for cell in cells):
        raise ValueError('Unknown cell value')
    if cells.count(0) != cells.count(3):
        raise ValueError('Cube and hole counts must match')


def validate_path(path, board):
    if path is None:
        return None
    if not path or path[0].state.get_state_board() != board:
        raise ValueError('Solution does not start at the input board')
    if not flat_board_state.is_goal_state(path[-1].state):
        raise ValueError('Solution does not end at a goal')
    for index in range(1, len(path)):
        previous = path[index - 1]
        current = path[index]
        legal = [state.get_state_board() for state, cost in previous.state.get_neighbors()
                 if cost == 1]
        if current.state.get_state_board() not in legal:
            raise ValueError('Solution contains an illegal transition')
        if current.prev is not previous or current.g != index:
            raise ValueError('Invalid solution cost or parent reference')
    return len(path) - 1


def benchmark_worker(connection, board, heuristic, repetitions):
    try:
        # Index 0 is a warm-up: no timer is read and it is not averaged.
        for index in range(repetitions + 1):
            state = flat_board_state(board)
            if index == 0:
                path = search(state, heuristic)
                elapsed_ms = None
            else:
                start = time.perf_counter()
                path = search(state, heuristic)
                elapsed_ms = (time.perf_counter() - start) * 1000
            generated, expanded = get_gen_exp_count()
            steps = validate_path(path, board)
            connection.send(('run', elapsed_ms, generated, expanded, steps, path is not None))
            # Release each path before the next timed search.
            del path
    except Exception:
        connection.send(('error', traceback.format_exc()))
    finally:
        connection.close()


def benchmark(board, heuristic, repetitions=30, timeout_seconds=10):
    """One warm-up plus repetitions; timeout applies to each worker response.

    Windows spawn requires an importable, module-level heuristic function and
    callers to invoke this function under an if __name__ == '__main__' guard.
    The first timeout also includes process startup; others include validation.
    """
    validate_board(board)
    if repetitions < 1 or timeout_seconds <= 0:
        raise ValueError('Repetitions and timeout must be positive')
    result = dict(avg_ms=None, median_ms=None, generated=None, expanded=None,
                  steps=None, solved=None, status='error', consistent=False,
                  repetitions=repetitions, completed_runs=0, error='')
    context = multiprocessing.get_context('spawn')
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(target=benchmark_worker,
                              args=(sender, board, heuristic, repetitions))
    process.start()
    sender.close()
    times = []
    baseline = None
    try:
        for index in range(repetitions + 1):
            if not receiver.poll(timeout_seconds):
                result.update(status='timeout', error=f'No result within {timeout_seconds}s')
                return result
            message = receiver.recv()
            if message[0] == 'error':
                result['error'] = message[1]
                return result
            _, elapsed, generated, expanded, steps, solved = message
            signature = (generated, expanded, steps, solved)
            if index == 0:
                baseline = signature
            elif signature != baseline:
                result.update(status='inconsistent', error='Counters or solution length changed')
                return result
            else:
                times.append(elapsed)
                result['completed_runs'] += 1
        result.update(avg_ms=statistics.mean(times), median_ms=statistics.median(times),
                      generated=baseline[0], expanded=baseline[1], steps=baseline[2],
                      solved=baseline[3], consistent=True,
                      status='solved' if baseline[3] else 'unsolvable')
        return result
    except EOFError:
        result['error'] = 'Worker exited without a result'
        return result
    finally:
        receiver.close()
        process.join(timeout=1)
        if process.is_alive():
            process.terminate()
            process.join(timeout=2)
        process.close()


def format_time(value):
    return '-' if value is None else f'{value:.4f}'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repetitions', type=int, default=30)
    parser.add_argument('--timeout', type=float, default=10)
    parser.add_argument('--output', type=Path,
                        default=Path(__file__).with_name('benchmark_base_results.csv'))
    args = parser.parse_args()
    rows = []
    print(f'Python {platform.python_version()}; {args.repetitions} timed runs + 1 warm-up per board', flush=True)
    print('| Board | Avg Time (ms) | Median (ms) | Generated | Expanded | Solution Steps | Solved |', flush=True)
    print('|---|---:|---:|---:|---:|---:|---|', flush=True)
    for name, board in BOARDS:
        result = benchmark(board, base_heuristic, args.repetitions, args.timeout)
        row = dict(board_name=name, heuristic=base_heuristic.__name__,
                   board_json=json.dumps(board), python=platform.python_version(),
                   platform=platform.platform(), timeout_seconds=args.timeout, **result)
        rows.append(row)
        print(f"| {name} | {format_time(result['avg_ms'])} | {format_time(result['median_ms'])} "
              f"| {result['generated']} | {result['expanded']} | {result['steps']} "
              f"| {result['solved']} ({result['status']}) |", flush=True)
        if result['error']:
            print(result['error'], flush=True)
    with args.output.open('w', newline='', encoding='utf-8') as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f'Saved {args.output}', flush=True)


if __name__ == '__main__':
    main()
