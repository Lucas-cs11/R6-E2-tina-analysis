#!/usr/bin/env python3
"""Run R6-12 maintenance/reconfiguration switch cases and source mutations."""

import copy
import csv
import difflib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'runs/g2_r612'
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / 'implementations/subject'))
import r612 as subject  # noqa: E402
sys.path.insert(0, str(ROOT / 'oracles/independent'))
import r612_reference as oracle  # noqa: E402


def model(switch, configs):
    return {'switch_time': switch, 'configurations': configs}


cases = [
    ('CLEAN_SWITCH', model('2', [{'id': 'c0', 'start': '0', 'end': '2'}, {'id': 'c1', 'start': '2', 'end': '4'}]), 'OK'),
    ('SPANS_SWITCH', model('2', [{'id': 'c0', 'start': '0', 'end': '3'}, {'id': 'c1', 'start': '3', 'end': '4'}]), 'SPANS_SWITCH'),
    ('MISSING_BEFORE', model('2', [{'id': 'c1', 'start': '2', 'end': '4'}]), 'MISSING_CONFIG'),
    ('MISSING_AFTER', model('2', [{'id': 'c0', 'start': '0', 'end': '2'}]), 'MISSING_CONFIG'),
    ('AT_ENDPOINT', model('2', [{'id': 'c0', 'start': '0', 'end': '2'}, {'id': 'c1', 'start': '2', 'end': '4'}]), 'OK'),
]
rows = []
for name, data, expected in cases:
    s = subject.classify(copy.deepcopy(data)); o = oracle.classify(copy.deepcopy(data))
    errors = []
    if s['category'] != expected or o['category'] != expected: errors.append('expected_category')
    if s['category'] != o['category']: errors.append('oracle_mismatch')
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
    original = (ROOT / 'implementations/subject/r612.py').read_text(encoding='utf-8')
    if original.count(old) != 1: raise SystemExit('anchor ' + name)
    changed = original.replace(old, new); (folder / 'r612.py').write_text(changed, encoding='utf-8')
    (folder / 'mutation.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True), changed.splitlines(True))), encoding='utf-8')
    mod = load_module(folder / 'r612.py', 'mut_' + name)
    data, expected = next((d, e) for n, d, e in cases if n == target)
    got = mod.classify(copy.deepcopy(data)); ref = oracle.classify(copy.deepcopy(data))
    detected = got['category'] != ref['category']
    (folder / 'subject.json').write_text(json.dumps(got, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (folder / 'oracle.json').write_text(json.dumps(ref, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'mutation': name, 'target': target, 'detected': detected, 'observed': got['category'], 'expected': expected}


mutations = [
    mutate('M_ALLOW_SPAN', 'SPANS_SWITCH',
           "    if overlap:\n        return {'status': 'INVALID_EVIDENCE', 'contract': C, 'tex_sha256': TEX,\n                'reason': 'configuration spans switch time', 'category': 'SPANS_SWITCH'}",
           "    if False:\n        pass"),
    mutate('M_REQUIRE_BOTH_SIDES', 'MISSING_BEFORE',
           "    if not before or not after:\n        return {'status': 'UNRESOLVED', 'contract': C, 'tex_sha256': TEX,\n                'reason': 'missing configuration on one side of switch', 'category': 'MISSING_CONFIG'}",
           "    if not before and not after:\n        return {'status': 'UNRESOLVED', 'contract': C, 'tex_sha256': TEX,\n                'reason': 'missing configuration on one side of switch', 'category': 'MISSING_CONFIG'}"),
    mutate('M_IGNORE_ENDPOINT', 'AT_ENDPOINT',
           "    before = [c for c in config if F(c['end']) <= switch_time]",
           "    before = [c for c in config if F(c['end']) < switch_time]"),
]
with (OUT / 'results.csv').open('w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
summary = {'status': 'PASS' if all(r['status'] == 'PASS' for r in rows) and all(m['detected'] for m in mutations) else 'FAIL',
           'phase_gate': 'PROVISIONAL_R6_12_PARTIAL_NOT_PHASE_GATE', 'cases': len(rows),
           'passed': sum(r['status'] == 'PASS' for r in rows), 'mutations': mutations,
           'not_covered': ['general reconfiguration semantics', 'full R6-12 suite']}
(OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
raise SystemExit(0 if summary['status'] == 'PASS' else 1)
