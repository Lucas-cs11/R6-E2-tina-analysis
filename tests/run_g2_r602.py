#!/usr/bin/env python3
"""Provisional R6-02 same-firing/completion window tests with mutations."""

import copy
import csv
import importlib.util
import json
import shutil
import sys
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'implementations/subject'))
sys.path.insert(0, str(ROOT / 'oracles/independent'))
import r602 as subject  # noqa: E402
import r602_reference as oracle  # noqa: E402
RUNS = ROOT / 'runs/g2_r602'
RUNS.mkdir(parents=True, exist_ok=True)


def case(events, completion, H):
    return {'H_psi': H, 'events': events, 'first_completion_time': completion}


cases = [
    ('SAME_FAULT_COMPLETION_ZERO_DURATION', case([{'id': 't', 'time': '2', 'fault': True, 'completion': True}], '2', '3'), {'classification': 'H1', 'duration': '0', 'same_firing': True}),
    ('FIRST_FAULT_BEFORE_HPSI', case([{'id': 't', 'time': '2', 'fault': True, 'completion': False}, {'id': 'c', 'time': '5', 'fault': False, 'completion': True}], '5', '3'), {'classification': 'H1', 'duration': '3', 'same_firing': False}),
    ('FIRST_FAULT_AT_HPSI', case([{'id': 't', 'time': '3', 'fault': True, 'completion': False}, {'id': 'c', 'time': '5', 'fault': False, 'completion': True}], '5', '3'), {'classification': 'H1', 'duration': '2', 'same_firing': False}),
    ('FIRST_FAULT_AFTER_HPSI', case([{'id': 't', 'time': '4', 'fault': True, 'completion': False}, {'id': 'c', 'time': '5', 'fault': False, 'completion': True}], '5', '3'), {'classification': 'H0', 'duration': '1', 'same_firing': False}),
    ('COMPLETION_THEN_NEW_FAULT_IGNORED', case([{'id': 'c', 'time': '2', 'fault': False, 'completion': True}, {'id': 'u', 'time': '5/2', 'fault': True, 'completion': False}], '2', '3'), {'classification': 'H0', 'duration': None, 'same_firing': False}),
]


def core(r):
    return r['classification'], r['post_fault_duration'], r['same_firing_fault_and_completion']


rows = []
for name, data, expected in cases:
    s = subject.classify(copy.deepcopy(data)); o = oracle.classify(copy.deepcopy(data))
    ok = s['classification'] == expected['classification'] and s['post_fault_duration'] == expected['duration'] and s['same_firing_fault_and_completion'] == expected['same_firing'] and s == {k: v for k, v in o.items() if k in s}
    rows.append({'test_id': name, 'expected_class': expected['classification'], 'subject_class': s['classification'],
                 'subject_duration': s['post_fault_duration'], 'subject_same_firing': s['same_firing_fault_and_completion'],
                 'oracle_class': o['classification'], 'status': 'PASS' if ok else 'FAIL'})
with (RUNS / 'results.csv').open('w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def mutate(name, target, old, new):
    folder = RUNS / 'mutations' / name
    if folder.exists(): shutil.rmtree(folder)
    (folder / 'subject').mkdir(parents=True)
    t = folder / 'subject' / 'r602.py'; shutil.copy2(ROOT / 'implementations/subject/r602.py', t)
    text = t.read_text(encoding='utf-8')
    if text.count(old) != 1: raise SystemExit('anchor ' + name)
    changed = text.replace(old, new); t.write_text(changed, encoding='utf-8')
    (folder / 'mutation.patch').write_text(''.join(__import__('difflib').unified_diff(text.splitlines(True), changed.splitlines(True))), encoding='utf-8')
    mod = load_module(t, 'mut_' + name)
    data, expected = next((d, e) for n, d, e in cases if n == target)
    got = mod.classify(copy.deepcopy(data))
    detected = got['classification'] != expected['classification'] or got['post_fault_duration'] != expected['duration'] or got['same_firing_fault_and_completion'] != expected['same_firing']
    (folder / 'observed.json').write_text(json.dumps(got, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'mutation': name, 'target': target, 'detected': detected, 'observed': {k: got[k] for k in ('classification', 'post_fault_duration', 'same_firing_fault_and_completion')}}


mutations = [
    mutate('M_ENDPOINT_EXCLUSIVE', 'FIRST_FAULT_AT_HPSI',
           "    classification = 'H1' if (first_fault is not None and first_fault <= H) else 'H0'",
           "    classification = 'H1' if (first_fault is not None and first_fault < H) else 'H0'"),
    mutate('M_POST_COMPLETION_FAULT_COUNTED', 'COMPLETION_THEN_NEW_FAULT_IGNORED',
           "        if e.get('fault') and F(e['time']) <= first_completion:",
           "        if e.get('fault'):"),
    mutate('M_ZERO_DURATION_FLAGGED', 'SAME_FAULT_COMPLETION_ZERO_DURATION',
           "    post_fault_duration = (first_completion - first_fault) if first_fault is not None else None",
           "    post_fault_duration = (F(1) if first_completion - first_fault == F(0) else first_completion - first_fault) if first_fault is not None else None"),
]
summary = {'status': 'PASS' if all(r['status'] == 'PASS' for r in rows) and all(m['detected'] for m in mutations) else 'FAIL',
           'phase_gate': 'PROVISIONAL_R6_02_PARTIAL_NOT_PHASE_GATE', 'cases': len(rows),
           'passed': sum(r['status'] == 'PASS' for r in rows), 'mutations': mutations,
           'not_covered': ['full SCG engine', 'mixed-state R6-05', 'general window B_c sweep']}
(RUNS / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
raise SystemExit(0 if summary['status'] == 'PASS' else 1)
