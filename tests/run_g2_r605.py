#!/usr/bin/env python3
"""Run R6-05 exact mixed/compliant/violating splits with source mutations."""

import copy
import csv
import difflib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'runs/g2_r605'
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / 'implementations/subject'))
import r605 as subject  # noqa: E402
sys.path.insert(0, str(ROOT / 'oracles/independent'))
import r605_reference as oracle  # noqa: E402


def model(lo, hi):
    return {'fault_variable': 'theta_f', 'B_c': '2',
            'bounds': {'theta_f': [lo, hi], 'theta_c': ['0', '5']},
            'constraints': [{'coefficients': {'theta_f': '1', 'theta_c': '-1'}, 'upper': '0'}],
            'witnesses': [
                {'theta_f': '1', 'theta_c': '2', 'path': ['f', 'c'], 'first_completion': True},
                {'theta_f': '3', 'theta_c': '4', 'path': ['f', 'c'], 'first_completion': True},
            ]}


cases = [('MIXED', model('1', '4'), (True, True, True)),
         ('ALL_COMPLIANT', model('1', '2'), (True, False, True)),
         ('ALL_VIOLATING', model('3', '4'), (False, True, False))]
rows = []
for name, data, expected in cases:
    s = subject.split(copy.deepcopy(data)); o = oracle.split(copy.deepcopy(data))
    actual = (s['compliant']['feasible'], s['violating']['feasible'], s['compliant']['completion_witness_preserved'])
    errors = []
    if actual != expected: errors.append('expected_split')
    if s != o: errors.append('oracle_mismatch')
    if s['violating']['feasible'] and not s['violating']['strict_lower']: errors.append('strictness_lost')
    (OUT / f'{name}.subject.json').write_text(json.dumps(s, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / f'{name}.oracle.json').write_text(json.dumps(o, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    rows.append({'test_id': name, 'expected': str(expected), 'actual': str(actual),
                 'compliant_witnesses': len(s['compliant']['witnesses']),
                 'violating_witnesses': len(s['violating']['witnesses']),
                 'status': 'PASS' if not errors else 'FAIL', 'errors': ';'.join(errors)})


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def mutate(name, old, new):
    folder = OUT / 'mutations' / name
    folder.mkdir(parents=True, exist_ok=True)
    original = (ROOT / 'implementations/subject/r605.py').read_text(encoding='utf-8')
    if original.count(old) != 1: raise SystemExit('anchor ' + name)
    changed = original.replace(old, new)
    target = folder / 'r605.py'; target.write_text(changed, encoding='utf-8')
    (folder / 'mutation.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True), changed.splitlines(True))), encoding='utf-8')
    mod = load_module(target, 'mut_' + name)
    got = mod.split(model('1', '4')); ref = oracle.split(model('1', '4'))
    detected = got != ref
    (folder / 'subject.json').write_text(json.dumps(got, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (folder / 'oracle.json').write_text(json.dumps(ref, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'mutation': name, 'detected': detected,
            'observed': {'compliant': got['compliant']['feasible'], 'violating': got['violating']['feasible'],
                         'completion_witness_preserved': got['compliant']['completion_witness_preserved']}}


mutations = [
    mutate('M_PRUNE_WHOLE_MIXED_CLASS',
           "    completion_witness_preserved = any(w.get('first_completion') for w in compliant_witnesses)\n    return",
           "    completion_witness_preserved = any(w.get('first_completion') for w in compliant_witnesses)\n    if violating_range is not None and violating_range[1] > bc:\n        compliant_range = None\n        compliant_witnesses = []\n        completion_witness_preserved = False\n    return"),
    mutate('M_DROP_COMPLETION_WITNESS',
           "    completion_witness_preserved = any(w.get('first_completion') for w in compliant_witnesses)",
           "    completion_witness_preserved = False"),
]
with (OUT / 'results.csv').open('w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
summary = {'status': 'PASS' if all(r['status'] == 'PASS' for r in rows) and all(m['detected'] for m in mutations) else 'FAIL',
           'phase_gate': 'PROVISIONAL_R6_05_PARTIAL_NOT_PHASE_GATE', 'cases': len(rows),
           'passed': sum(r['status'] == 'PASS' for r in rows), 'mutations': mutations,
           'not_covered': ['general dimension polytope enumeration in independent oracle', 'general SCG construction']}
(OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
raise SystemExit(0 if summary['status'] == 'PASS' else 1)
