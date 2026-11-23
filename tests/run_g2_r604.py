#!/usr/bin/env python3
"""Provisional R6-04 deadline/endpoint tests with real mutations."""

import copy
import csv
import importlib.util
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'implementations/subject'))
sys.path.insert(0, str(ROOT / 'oracles/independent'))
import r604 as subject  # noqa: E402
import r604_reference as oracle  # noqa: E402
RUNS = ROOT / 'runs/g2_r604'
RUNS.mkdir(parents=True, exist_ok=True)


def run(tf, Bc, Ha, tc=None):
    d = {'first_fault_time': tf, 'B_c': Bc, 'H_A': Ha}
    if tc is not None: d['completion_time'] = tc
    return d


cases = [
    ('POST_FAULT_EQ_Bc', run('2', '1', '5', '3'), 'COMPLETED_IN_TIME'),
    ('POST_FAULT_LT_Bc', run('2', '1', '5', '5/2'), 'COMPLETED_IN_TIME'),
    ('POST_FAULT_GT_Bc', run('2', '1', '5', '7/2'), 'VIOLATION'),
    ('INCOMPLETE_PAST_DEADLINE', run('2', '1', '4'), 'VIOLATION'),
    ('SHORT_PREFIX_NOT_DUE', run('2', '1', '5/2'), 'PENDING'),
    ('ENDPOINT_DEADLINE_EQ_HA_COMPLETE', run('2', '1', '3', '3'), 'COMPLETED_IN_TIME'),
]


def core(r):
    return r['outcome'], r['endpoint_exact_pass']


rows = []
for name, data, expected in cases:
    s = subject.classify(copy.deepcopy(data)); o = oracle.classify(copy.deepcopy(data))
    ok = s['outcome'] == expected and s == o
    rows.append({'test_id': name, 'expected': expected, 'subject_outcome': s['outcome'],
                 'subject_deadline': s['post_fault_deadline'], 'endpoint_exact': s['endpoint_exact_pass'],
                 'oracle_outcome': o['outcome'], 'status': 'PASS' if ok else 'FAIL'})
with (RUNS / 'results.csv').open('w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def mutate(name, target, old, new):
    folder = RUNS / 'mutations' / name
    if folder.exists(): shutil.rmtree(folder)
    (folder / 'subject').mkdir(parents=True)
    t = folder / 'subject' / 'r604.py'; shutil.copy2(ROOT / 'implementations/subject/r604.py', t)
    text = t.read_text(encoding='utf-8')
    if text.count(old) != 1: raise SystemExit('anchor ' + name)
    changed = text.replace(old, new); t.write_text(changed, encoding='utf-8')
    (folder / 'mutation.patch').write_text(''.join(__import__('difflib').unified_diff(text.splitlines(True), changed.splitlines(True))), encoding='utf-8')
    mod = load_module(t, 'mut_' + name)
    data, expected = next((d, e) for n, d, e in cases if n == target)
    got = mod.classify(copy.deepcopy(data))
    detected = got['outcome'] != expected
    (folder / 'observed.json').write_text(json.dumps(got, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'mutation': name, 'target': target, 'detected': detected, 'observed_outcome': got['outcome'], 'expected': expected}


mutations = [
    mutate('M_EQ_Bc_TREATED_VIOLATION', 'POST_FAULT_EQ_Bc',
           '        if duration <= Bc:', '        if duration < Bc:'),
    mutate('M_SHORT_PREFIX_VIOLATION', 'SHORT_PREFIX_NOT_DUE',
           "        if Ha < deadline:\n            outcome = 'PENDING'  # short prefix not yet due\n        else:\n            outcome = 'VIOLATION'",
           "        outcome = 'VIOLATION'"),
    mutate('M_ENDPOINT_NOT_FIRST', 'ENDPOINT_DEADLINE_EQ_HA_COMPLETE',
           "        if duration <= Bc:\n            outcome = 'COMPLETED_IN_TIME'\n        else:\n            outcome = 'VIOLATION'",
           "        if tc == Ha and deadline == Ha:\n            outcome = 'PENDING'  # MUTATION: process truncation before legal completion\n        elif duration <= Bc:\n            outcome = 'COMPLETED_IN_TIME'\n        else:\n            outcome = 'VIOLATION'"),
]
summary = {'status': 'PASS' if all(r['status'] == 'PASS' for r in rows) and all(m['detected'] for m in mutations) else 'FAIL',
           'phase_gate': 'PROVISIONAL_R6_04_PARTIAL_NOT_PHASE_GATE', 'cases': len(rows),
           'passed': sum(r['status'] == 'PASS' for r in rows), 'mutations': mutations,
           'not_covered': ['general H_A truncation sweep', 'mixed-state split']}
(RUNS / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
raise SystemExit(0 if summary['status'] == 'PASS' else 1)
