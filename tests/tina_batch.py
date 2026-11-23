#!/usr/bin/env python3
"""Run TINA on a batch of candidates for GitHub Actions."""

import argparse
import csv
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TINA = 'tina'  # assume in PATH
sys.path.insert(0, str(ROOT / 'implementations/generator_compat'))
from src.benchmarks.rmt_fms_generator import generate_rmt_fms  # noqa: E402


def net_to_pnml(net, name):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<pnml xmlns="http://www.pnml.org/version-2009/grammar/pnml">',
             f'  <net id="{name}" type="http://www.pnml.org/version-2009/grammar/ptnet">',
             '    <page id="page0">']
    for p in sorted(net.places):
        marking = net.initial_marking.get(p, 0)
        lines.append(f'      <place id="{p}">')
        if marking > 0:
            lines.append(f'        <initialMarking><text>{marking}</text></initialMarking>')
        lines.append('      </place>')
    for t in sorted(net.transitions):
        lines.append(f'      <transition id="{t}"/>')
    for i, a in enumerate(net.arcs):
        lines.append(f'      <arc id="a{i}" source="{a.from_node}" target="{a.to_node}"/>')
    lines.extend(['    </page>', '  </net>', '</pnml>'])
    return '\n'.join(lines)


def run_tina(pnml_path):
    try:
        result = subprocess.run([TINA, '-PNML', str(pnml_path), '-R'],
                                capture_output=True, text=True, timeout=30)
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return 'TIMEOUT'
    except Exception as e:
        return f'ERROR: {e}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--batch', type=int, required=True)
    ap.add_argument('--total-batches', type=int, default=10)
    args = ap.parse_args()
    rows = list(csv.DictReader((ROOT / 'scope/generator_candidate_universe_full.csv').open(newline='', encoding='utf-8')))
    valid = [r for r in rows if r['static_validity'] == 'VALID_BY_FROZEN_RULE']
    batch_size = (len(valid) + args.total_batches - 1) // args.total_batches
    start = (args.batch - 1) * batch_size
    end = min(start + batch_size, len(valid))
    batch = valid[start:end]
    out_path = ROOT / f'results/tina_batch_{args.batch}.csv'
    results = []
    for r in batch:
        params = {'n_machines': int(r['machine_counts']), 'n_parts': int(r['part_type_counts']),
                  'ops_per_part': int(r['operations_per_part']), 'wip_bound': int(r['wip_bounds']),
                  'unobservable_ratio': float(r['unobservable_ratios']),
                  'fault_locations': int(r['fault_locations']),
                  'interval_width_factor': float(r['interval_width_factors']),
                  'adjustable_ratio': float(r['adjustable_ratios']),
                  'seed': 0, 'machine_capacity': 1, 'n_configs': 2, 'repair_domain': 'standard'}
        try:
            net, L, H = generate_rmt_fms(**params)
            pnml = net_to_pnml(net, r['candidate_id'])
            with tempfile.NamedTemporaryFile(mode='w', suffix='.pnml', delete=False) as tf:
                tf.write(pnml); tmp = tf.name
            output = run_tina(tmp)
            Path(tmp).unlink()
            bounded = 'bounded' in output.lower()
            results.append({'candidate_id': r['candidate_id'], 'tina_bounded': bounded,
                            'places': len(net.places), 'transitions': len(net.transitions)})
        except Exception as e:
            results.append({'candidate_id': r['candidate_id'], 'tina_bounded': False,
                            'places': 0, 'transitions': 0, 'error': str(e)})
    with out_path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(results[0])); w.writeheader(); w.writerows(results)
    print(json.dumps({'batch': args.batch, 'processed': len(results)}, indent=2))


if __name__ == '__main__':
    main()
