#!/usr/bin/env python3
"""Run R6-01 distinguishing-subdomain cases and source mutations."""

import copy
import csv
import difflib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'runs/g2_r601'
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / 'implementations/subject'))
import r601 as subject  # noqa: E402
sys.path.insert(0, str(ROOT / 'oracles/independent'))
import r601_reference as oracle  # noqa: E402


def base():
    return {'locations': {'a': ['0', '1'], 'b': ['0', '1']}, 'edges': [
        {'from': 'a', 'to': 'b', 'urgent': True, 'delay': '0'},
        {'from': 'a', 'to': 'a', 'urgent': False, 'delay': '1'},
    ], 'depth': 2}


cases = [
    ('NONURGENT_ENDPOINT_DISTINGUISHED', {**base(), 'endpoint_grid': True}, False),
    ('URGENT_DELAYED_PRIORITY', {**base(), 'endpoint_grid': False}, False),
    ('URGENT_FIRES_BEFORE_DELAYED', {**base(), 'endpoint_grid': False}, False),
]
rows = []
for name, model, expected_undistinguished in cases:
    s = subject.distinguish(copy.deepcopy(model)); o = oracle.distinguish(copy.deepcopy(model))
    errors = []
    if s['relation'] != o['relation']: errors.append('oracle_mismatch')
    if s['undistinguished_pairs'] != expected_undistinguished: errors.append('expected_undistinguished')
    (OUT / f'{name}.subject.json').write_text(json.dumps(s, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / f'{name}.oracle.json').write_text(json.dumps(o, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    rows.append({'test_id': name, 'expected_undistinguished': expected_undistinguished,
                 'subject_undistinguished': s['undistinguished_pairs'], 'oracle_undistinguished': o['undistinguished_pairs'],
                 'relation_size': len(s['relation']), 'status': 'PASS' if not errors else 'FAIL', 'errors': ';'.join(errors)})


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def mutate(name, target, old, new):
    folder = OUT / 'mutations' / name
    folder.mkdir(parents=True, exist_ok=True)
    original = (ROOT / 'implementations/subject/r601.py').read_text(encoding='utf-8')
    if original.count(old) != 1: raise SystemExit('anchor ' + name)
    changed = original.replace(old, new); (folder / 'r601.py').write_text(changed, encoding='utf-8')
    (folder / 'mutation.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True), changed.splitlines(True))), encoding='utf-8')
    mod = load_module(folder / 'r601.py', 'mut_' + name)
    model, expected = next((m, e) for n, m, e in cases if n == target)
    got = mod.distinguish(copy.deepcopy(model))
    original = subject.distinguish(copy.deepcopy(model))
    ref = oracle.distinguish(copy.deepcopy(model))
    detected = set(got['trace_records']) != set(map(str, ref.get('signatures', []))) or got['relation'] != original['relation']
    (folder / 'subject.json').write_text(json.dumps(got, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (folder / 'oracle.json').write_text(json.dumps(ref, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'mutation': name, 'target': target, 'detected': detected, 'observed': got['undistinguished_pairs'], 'expected': expected}


mutations = [
    mutate('M_DELAYED_BEFORE_URGENT', 'URGENT_DELAYED_PRIORITY',
           "            urgent = enabled(model, s, 'urgent')\n            if urgent:",
           "            urgent = []\n            if urgent:"),
    mutate('M_ENDPOINT_OPEN', 'NONURGENT_ENDPOINT_DISTINGUISHED',
           "        steps = 1 if model.get('endpoint_grid', False) else 2",
           "        steps = 2"),
    mutate('M_URGENT_NEVER_FIRES', 'URGENT_FIRES_BEFORE_DELAYED',
           "    states = closure(model)",
           "    model['edges'] = [e for e in model['edges'] if not e.get('urgent')]\n    states = closure(model)"),
]
with (OUT / 'results.csv').open('w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
summary = {'status': 'PASS' if all(r['status'] == 'PASS' for r in rows) and all(m['detected'] for m in mutations) else 'FAIL',
           'phase_gate': 'PROVISIONAL_R6_01_PARTIAL_NOT_PHASE_GATE', 'cases': len(rows),
           'passed': sum(r['status'] == 'PASS' for r in rows), 'mutations': mutations,
           'subdomains': ['endpoint equality', 'urgent priority over delayed'],
           'not_covered': ['unbounded closure', 'general timed automata', 'full R6-01 13-boundary suite']}
(OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
raise SystemExit(0 if summary['status'] == 'PASS' else 1)
