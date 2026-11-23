#!/usr/bin/env python3
"""Run TINA on 54-cell paper minimum subdomain."""

import csv
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TINA = '/Users/lucas/tina/bin/tina'
OUT = ROOT / 'results/tina_54_cells.csv'
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
    cells = list(csv.DictReader((ROOT / 'scope/generator_parameter_universe.csv').open(newline='', encoding='utf-8')))
    results = []
    for cell in cells:
        params = {'n_machines': int(cell['m']), 'n_parts': int(cell['j']), 'ops_per_part': 2,
                  'wip_bound': 1, 'unobservable_ratio': float(cell['u']),
                  'fault_locations': 1, 'interval_width_factor': float(cell['w']),
                  'adjustable_ratio': 0.1, 'seed': 0, 'machine_capacity': 1, 'n_configs': 2,
                  'repair_domain': 'standard'}
        net, L, H = generate_rmt_fms(**params)
        pnml = net_to_pnml(net, cell['cell_id'])
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pnml', delete=False) as tf:
            tf.write(pnml); tmp = tf.name
        import time; t0 = time.time()
        output = run_tina(tmp)
        t = time.time() - t0
        Path(tmp).unlink()
        bounded = 'bounded' in output.lower()
        results.append({'cell_id': cell['cell_id'], 'm': cell['m'], 'j': cell['j'],
                        'u': cell['u'], 'w': cell['w'], 'places': len(net.places),
                        'transitions': len(net.transitions), 'tina_bounded': bounded, 'tina_time': f"{t:.3f}"})
    with OUT.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(results[0])); w.writeheader(); w.writerows(results)
    all_bounded = sum(1 for r in results if r['tina_bounded'])
    print(json.dumps({'total': len(results), 'bounded': all_bounded, 'all_bounded': all_bounded == len(results)}, indent=2))


if __name__ == '__main__':
    main()
