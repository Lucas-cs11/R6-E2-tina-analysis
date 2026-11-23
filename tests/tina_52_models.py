#!/usr/bin/env python3
"""Convert historical RMT models to PNML and verify with TINA."""

import csv
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TINA = '/Users/lucas/tina/bin/tina'
sys.path.insert(0, str(ROOT / 'implementations/generator_compat'))
from src.benchmarks.rmt_fms_generator import generate_rmt_fms  # noqa: E402

FREEZE = json.loads((ROOT / 'scope/freeze.json').read_text())
HIST = list(csv.DictReader((ROOT / 'scope/逻辑逐行_完整精度.csv').open(newline='', encoding='utf-8')))
FIXED = {'seed': 0, 'machine_capacity': 1, 'n_configs': 2, 'repair_domain': 'standard'}


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
                                capture_output=True, text=True, timeout=60)
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return 'TIMEOUT'
    except Exception as e:
        return f'ERROR: {e}'


def main():
    results = []
    for task in FREEZE['tasks']:
        if task.get('family') != 'rmt_original_subset' or task.get('method') != 'main':
            continue
        cid = task['case_id']
        params = dict(task['params']); params.update(FIXED)
        net, L, H = generate_rmt_fms(**params)
        pnml = net_to_pnml(net, cid)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pnml', delete=False) as f:
            f.write(pnml); tmp = f.name
        output = run_tina(tmp)
        Path(tmp).unlink()
        hist = next((r for r in HIST if r['case_id'] == cid and r['method'] == 'main'), None)
        tina_bounded = 'bounded' in output.lower()
        tina_places = output.count('pl ')
        tina_transitions = output.count('tr ')
        match = (hist and str(len(net.places)) == hist['places'] and str(len(net.transitions)) == hist['transitions'])
        results.append({'case_id': cid, 'places': len(net.places), 'transitions': len(net.transitions),
                        'arcs': len(net.arcs), 'tina_bounded': tina_bounded,
                        'tina_places_count': tina_places, 'tina_transitions_count': tina_transitions,
                        'hist_match': match, 'status': 'TINA_VERIFIED' if match and tina_bounded else 'MISMATCH'})
    with (ROOT / 'results/tina_52_models.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(results[0])); w.writeheader(); w.writerows(results)
    from collections import Counter
    c = Counter(r['status'] for r in results)
    print(json.dumps({'total': len(results), 'statuses': dict(c)}, indent=2))


if __name__ == '__main__':
    main()
