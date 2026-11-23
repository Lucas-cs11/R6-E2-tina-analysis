#!/usr/bin/env python3
"""Run R6-08 module-level error paths and source mutations."""

import copy
import csv
import difflib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'runs/g2_r608_module'
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / 'implementations/subject'))
import r608_module as subject  # noqa: E402
sys.path.insert(0, str(ROOT / 'oracles/independent'))
import r608_module_reference as oracle  # noqa: E402


def base():
    return {'q_intervals': {'q0': ['0', '1/2'], 'q1': ['0', '1/2']}, 'certified_interval': True,
            'integration_method': 'exact_polytope', 'search_incomplete': False}


cases = [
    ('MODEL_INPUT_INVALID', {**base(), 'model_input_invalid': True}, 'MODEL_INPUT_INVALID'),
    ('UNCERTIFIED_INTERVAL', {**base(), 'certified_interval': False}, 'UNCERTIFIED_INTERVAL'),
    ('COMPLEMENT_INFEASIBLE', {**base(), 'q_intervals': {'q0': ['0', '1/4'], 'q1': ['0', '1/4']}}, 'COMPLEMENT_INFEASIBLE'),
    ('BOUND_INVALID', {**base(), 'q_intervals': {'q0': ['1/2', '1/4'], 'q1': ['0', '1']}}, 'BOUND_INVALID'),
    ('JOINT_INFEASIBLE', {**base(), 'Q_intervals': {('Q0', 'q0'): ['3/5', '3/4']}}, 'JOINT_INFEASIBLE'),
    ('SOURCE_INCONSISTENT', {**base(), 'same_event_source': True, 'source_consistent': False}, 'SOURCE_INCONSISTENT'),
    ('CATEGORY_SUM_EXCEEDS', {**base(), 'category_sums': {'c0': '3/4'}, 'per_category_source': {'c0': ['1/2']}}, 'CATEGORY_SUM_EXCEEDS'),
    ('NO_METHOD', {**base(), 'integration_method': None}, 'NO_METHOD'),
    ('SEARCH_INCOMPLETE', {**base(), 'search_incomplete': True}, 'SEARCH_INCOMPLETE'),
    ('OK_DECIDED', {**base(), 'expected_verdict': '0'}, 'OK'),
]
rows = []
for name, data, expected in cases:
    s = subject.classify(copy.deepcopy(data)); o = oracle.check(copy.deepcopy(data))
    errors = []
    if s['category'] != expected or o != expected: errors.append('expected_category')
    if s['category'] != o: errors.append('oracle_mismatch')
    (OUT / f'{name}.subject.json').write_text(json.dumps(s, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / f'{name}.oracle.json').write_text(json.dumps({'category': o}, indent=2) + '\n', encoding='utf-8')
    rows.append({'test_id': name, 'expected': expected, 'subject_category': s['category'], 'oracle_category': o,
                 'status': 'PASS' if not errors else 'FAIL', 'errors': ';'.join(errors)})


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def mutate(name, target, old, new):
    folder = OUT / 'mutations' / name
    folder.mkdir(parents=True, exist_ok=True)
    original = (ROOT / 'implementations/subject/r608_module.py').read_text(encoding='utf-8')
    if original.count(old) != 1: raise SystemExit('anchor ' + name)
    changed = original.replace(old, new); (folder / 'r608_module.py').write_text(changed, encoding='utf-8')
    (folder / 'mutation.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True), changed.splitlines(True))), encoding='utf-8')
    mod = load_module(folder / 'r608_module.py', 'mut_' + name)
    data, expected = next((d, e) for n, d, e in cases if n == target)
    got = mod.classify(copy.deepcopy(data)); ref = oracle.check(copy.deepcopy(data))
    detected = got['category'] != ref
    (folder / 'subject.json').write_text(json.dumps(got, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (folder / 'oracle.json').write_text(json.dumps({'category': ref}, indent=2) + '\n', encoding='utf-8')
    return {'mutation': name, 'target': target, 'detected': detected, 'observed': got['category'], 'expected': expected}


mutations = [
    mutate('M_SKIP_COMPLEMENT_CHECK', 'COMPLEMENT_INFEASIBLE',
           "    if sum((v[0] for v in q.values()), F(0)) > 1 or sum((v[1] for v in q.values()), F(0)) < 1:",
           "    if False:"),
    mutate('M_ACCEPT_UNCERTIFIED', 'UNCERTIFIED_INTERVAL',
           "    if not evidence.get('certified_interval'):",
           "    if False:"),
    mutate('M_DECIDE_WITHOUT_METHOD', 'NO_METHOD',
           "    if not evidence.get('integration_method'):\n        return {'status': 'UNRESOLVED', 'contract': C, 'tex_sha256': TEX,\n                'reason': 'no valid integration method available', 'category': 'NO_METHOD'}",
           "    if False:\n        pass"),
]
with (OUT / 'results.csv').open('w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
summary = {'status': 'PASS' if all(r['status'] == 'PASS' for r in rows) and all(m['detected'] for m in mutations) else 'FAIL',
           'phase_gate': 'PROVISIONAL_R6_08_MODULE_NOT_PHASE_GATE', 'cases': len(rows),
           'passed': sum(r['status'] == 'PASS' for r in rows), 'mutations': mutations,
           'not_covered': ['full 13-boundary R6-08 suite', 'all error paths with real SCG traces']}
(OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
raise SystemExit(0 if summary['status'] == 'PASS' else 1)
