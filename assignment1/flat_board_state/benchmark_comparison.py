"""Compare the existing heuristics on the unchanged baseline boards."""

import csv
import json
import platform
from pathlib import Path

from benchmark import BOARDS, benchmark
from heuristics import base_heuristic, advanced_heuristic


def main():
    if platform.python_version_tuple()[:2] != ('3', '10'):
        raise SystemExit('Run this comparison with Python 3.10')
    rows = []
    print(f'Python {platform.python_version()}; one warm-up + 30 timed runs per heuristic/board',
          flush=True)
    print('| Board | Base avg ms | Advanced avg ms | Improvement % | Generated B/A | Expanded B/A | Steps |',
          flush=True)
    print('|---|---:|---:|---:|---:|---:|---:|', flush=True)
    for index, (name, board) in enumerate(BOARDS):
        # Alternate which heuristic is measured first to reduce fixed-order bias.
        functions = [base_heuristic, advanced_heuristic]
        if index % 2:
            functions.reverse()
        results = {}
        for heuristic in functions:
            results[heuristic.__name__] = benchmark(board, heuristic, repetitions=30)
        base = results['base_heuristic']
        advanced = results['advanced_heuristic']
        valid = (base['consistent'] and advanced['consistent']
                 and base['status'] == advanced['status'] == 'solved'
                 and base['steps'] == advanced['steps'])
        improvement = None
        if valid:
            improvement = (base['avg_ms'] - advanced['avg_ms']) / base['avg_ms'] * 100
        row = dict(board_name=name, board_json=json.dumps(board),
                   python=platform.python_version(), platform=platform.platform(),
                   time_improvement_percent=improvement,
                   same_solution_length=base['steps'] == advanced['steps'],
                   comparison_valid=valid)
        for prefix, result in (('base', base), ('advanced', advanced)):
            for field, value in result.items():
                row[f'{prefix}_{field}'] = value
        rows.append(row)
        if valid:
            print(f"| {name} | {base['avg_ms']:.4f} | {advanced['avg_ms']:.4f} "
                  f"| {improvement:+.2f} | {base['generated']}/{advanced['generated']} "
                  f"| {base['expanded']}/{advanced['expanded']} | {base['steps']} |", flush=True)
            print(f"  Median ms: base={base['median_ms']:.4f}, advanced={advanced['median_ms']:.4f}",
                  flush=True)
        else:
            print(f'| {name} | comparison failed; see CSV for details |', flush=True)
    output = Path(__file__).with_name('benchmark_comparison.csv')
    with output.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f'Saved {output.name}', flush=True)
    if not all(row['comparison_valid'] for row in rows):
        raise SystemExit('Some boards could not be compared successfully')


if __name__ == '__main__':
    main()
