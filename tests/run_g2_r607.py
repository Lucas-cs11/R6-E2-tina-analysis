#!/usr/bin/env python3
"""Run R6-07 implicit/explicit reset cases and source mutations."""

import copy
import csv
import difflib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'runs/g2_r607'
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / 'implementations/subject'))
import r607 as subject  # noqa: E402
sys.path.insert(0, str(ROOT / 'oracles/independent'))
import r607_reference as oracle  # noqa: E402


def model(initial, transitions, steps):
    return {'initial_marking': initial, 'transitions': transitions, 'steps': steps}


cases = [
    ('IMPLICIT_RESET', model({'p1': 2, 'p2': 1},
        [{'id': 't1', 'pre': {'p1': 1, 'p2': 1}, 'post': {'p3': 1}}],
        [{'transition': 't1'}]), 'OK'),
    ('EXPLICIT_RESET', model({'p1': 2, 'p2': 1},
        [{'id': 't1', 'pre': {'p1': 1, 'p2': 1}, 'post': {'p3': 1}}],
        [{'transition': 't1', 'explicit_reset': ['p2']}]), 'OK'),
    ('RESET_NOT_CONSUMED', model({'p1': 2, 'p2': 1},
        [{'id': 't1', 'pre': {'p1': 1}, 'post': {'p3': 1}}],
        [{'transition': 't1', 'explicit_reset': ['p2']}]), 'RESET_NOT_CONSUMED'),
    ('NOT_ENABLED', model({'p1': 1},
        [{'id': 't1', 'pre': {'p1': 2}, 'post': {'p3': 1}}],
        [{'transition': 't1'}]), 'NOT_ENABLED'),
    ('UNKNOWN_TRANSITION', model({'p1': 1}, [], [{'transition': 'tX'}]), 'UNKNOWN_TRANSITION'),
]
rows = []
for name, data, expected in cases:
    s = subject.execute(copy.deepcopy(data)); o = oracle.execute(copy.deepcopy(data))
    errors = []
    if s['category'] != expected or o['category'] != expected: errors.append('expected_category')
    if s['category'] != o['category']: errors.append('oracle_mismatch')
    if s['category'] == 'OK':
        if s['final_marking'] != o['final_marking']: errors.append('final_marking_mismatch')
        if [r['implicit_reset'] for r in s['resets']] != [r['implicit_reset'] for r in o['resets']]: errors.append('reset_mismatch')
    (OUT / f'{name}.subject.json').write_text(json.dumps(s, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / f'{name}.oracle.json').write_text(json.dumps(o, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    rows.append({'test_id': name, 'expected': expected, 'subject_category': s['category'], 'oracle_category': o['category'],
                 'status': 'PASS' if not errors else 'FAIL', 'errors': ';'.join(errors)})


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def mutate(name, target, old, new):
    folder = OUT / 'mutations' / name
    folder.mkdir(parents=True, exist_ok=True)
    original = (ROOT / 'implementations/subject/r607.py').read_text(encoding='utf-8')
    if original.count(old) != 1: raise SystemExit('anchor ' + name)
    changed = original.replace(old, new); (folder / 'r607.py').write_text(changed, encoding='utf-8')
    (folder / 'mutation.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True), changed.splitlines(True))), encoding='utf-8')
    mod = load_module(folder / 'r607.py', 'mut_' + name)
    data, expected = next((d, e) for n, d, e in cases if n == target)
    got = mod.execute(copy.deepcopy(data)); ref = oracle.execute(copy.deepcopy(data))
    detected = got['category'] != ref['category'] or (got['category'] == 'OK' and got['final_marking'] != ref['final_marking'])
    (folder / 'subject.json').write_text(json.dumps(got, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (folder / 'oracle.json').write_text(json.dumps(ref, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'mutation': name, 'target': target, 'detected': detected, 'observed': got['category'], 'expected': expected}


mutations = [
    mutate('M_RESET_ALL_CONSUMED', 'IMPLICIT_RESET',
           "        implicit = consumed - explicit",
           "        implicit = set()"),
    mutate('M_IGNORE_EXPLICIT', 'EXPLICIT_RESET',
           "        for p in implicit:\n            marking[p] = 0",
           "        for p in consumed:\n            marking[p] = 0"),
    mutate('M_ALLOW_UNCONSUMED_RESET', 'RESET_NOT_CONSUMED',
           "        for p in explicit:\n            if p not in consumed: return {'status': 'INVALID_EVIDENCE', 'contract': C, 'tex_sha256': TEX, 'category': 'RESET_NOT_CONSUMED'}",
           "        pass"),
]
with (OUT / 'results.csv').open('w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
summary = {'status': 'PASS' if all(r['status'] == 'PASS' for r in rows) and all(m['detected'] for m in mutations) else 'FAIL',
           'phase_gate': 'PROVISIONAL_R6_07_PARTIAL_NOT_PHASE_GATE', 'cases': len(rows),
           'passed': sum(r['status'] == 'PASS' for r in rows), 'mutations': mutations,
           'not_covered': ['general reset arc semantics', 'full R6-07 suite']}
(OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
raise SystemExit(0 if summary['status'] == 'PASS' else 1)
