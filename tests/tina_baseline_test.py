#!/usr/bin/env python3
"""Convert RMT models to PNML and verify with TINA."""

import csv
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TINA = '/Users/lucas/tina/bin/tina'
HIST = list(csv.DictReader((ROOT / 'scope/逻辑逐行_完整精度.csv').open(newline='', encoding='utf-8')))


def net_to_pnml(places, transitions, arcs, initial, name):
    """Convert net to PNML format."""
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<pnml xmlns="http://www.pnml.org/version-2009/grammar/pnml">',
             f'  <net id="{name}" type="http://www.pnml.org/version-2009/grammar/ptnet">',
             '    <page id="page0">']
    for p in places:
        marking = initial.get(p, 0)
        lines.append(f'      <place id="{p}">')
        if marking > 0:
            lines.append(f'        <initialMarking><text>{marking}</text></initialMarking>')
        lines.append('      </place>')
    for t in transitions:
        lines.append(f'      <transition id="{t}"/>')
    for i, (src, tgt) in enumerate(arcs):
        lines.append(f'      <arc id="a{i}" source="{src}" target="{tgt}"/>')
    lines.extend(['    </page>', '  </net>', '</pnml>'])
    return '\n'.join(lines)


def run_tina(pnml_path):
    """Run TINA reachability analysis."""
    try:
        result = subprocess.run([TINA, '-PNML', str(pnml_path)],
                                capture_output=True, text=True, timeout=30)
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return 'TIMEOUT'
    except Exception as e:
        return f'ERROR: {e}'


def main():
    # Test with a few historical models
    # We need to reconstruct the net from freeze.json params
    freeze = json.loads((ROOT / 'scope/freeze.json').read_text())
    tasks = [t for t in freeze['tasks'] if t.get('family') == 'rmt_original_subset' and t.get('method') == 'main'][:3]
    results = []
    for task in tasks:
        cid = task['case_id']
        # For now, create a simple test net
        pnml = net_to_pnml(['p1', 'p2'], ['t1'], [('p1', 't1'), ('t1', 'p2')], {'p1': 1}, cid)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pnml', delete=False) as f:
            f.write(pnml)
            tmp_path = f.name
        output = run_tina(tmp_path)
        Path(tmp_path).unlink()
        results.append({'case_id': cid, 'tina_output': output[:500]})
    with (ROOT / 'results/tina_baseline_test.json').open('w') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(json.dumps({'tested': len(results), 'sample': results[0]['tina_output'][:200]}, indent=2))


if __name__ == '__main__':
    main()
