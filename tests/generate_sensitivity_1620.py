#!/usr/bin/env python3
"""Actually generate all 1620 logical sensitivity models (54 cells x 10 seeds x 3 WIP)."""

import csv
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys_path_backup = list(__import__('sys').path)
spec = importlib.util.spec_from_file_location('r6e2_gen', ROOT / 'tests/generate_all_valid_candidates.py')
gen = importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)
__import__('sys').path[:] = sys_path_backup

OUT = ROOT / 'results/sensitivity_logical_1620_results.csv'
BASE = list(csv.DictReader((ROOT / 'scope/generator_parameter_universe.csv').open(newline='', encoding='utf-8')))


def cell_params(cell, seed, wip):
    return {'n_machines': int(cell['m']), 'n_parts': int(cell['j']), 'ops_per_part': 2,
            'wip_bound': wip, 'unobservable_ratio': float(cell['u']),
            'fault_locations': 1, 'interval_width_factor': float(cell['w']),
            'adjustable_ratio': 0.1, 'seed': seed, 'machine_capacity': 1, 'n_configs': 2,
            'repair_domain': 'standard'}


def main():
    rows = []
    for cell in BASE:
        for seed in range(10):
            for wip in (1, 2, 3):
                params = cell_params(cell, seed, wip)
                try:
                    net, L, H = gen.generate_rmt_fms(**params)
                    issues = gen.validate(net, params, L, H)
                    payload = gen.canonical(net, params, L, H)
                    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
                    status = 'GENERATED_STRUCTURE_PASS' if not issues else 'GENERATED_STRUCTURE_ISSUES'
                except Exception as exc:
                    status = 'GENERATOR_ERROR'; L = H = digest = ''; issues = [f'{type(exc).__name__}: {exc}']
                    net = type('N', (), {'places': {}, 'transitions': {}, 'arcs': []})()
                rows.append({'sensitivity_id': f"{cell['cell_id']}_s{seed}_wip{wip}", 'base_cell': cell['cell_id'],
                             'seed': seed, 'wip': wip, 'status': status, 'model_sha256': digest,
                             'places': len(net.places), 'transitions': len(net.transitions), 'arcs': len(net.arcs),
                             'L': L, 'H': H, 'structural_issues': ';'.join(issues)})
    with OUT.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    from collections import Counter
    c = Counter(r['status'] for r in rows)
    print(json.dumps({'total': len(rows), 'statuses': dict(c)}, indent=2))


if __name__ == '__main__':
    main()
