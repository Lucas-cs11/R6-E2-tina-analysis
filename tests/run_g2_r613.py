#!/usr/bin/env python3
"""Run R6-13 sensor delay cases and source mutations."""

import copy
import csv
import difflib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'runs/g2_r613'
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / 'implementations/subject'))
import r613 as subject  # noqa: E402
sys.path.insert(0, str(ROOT / 'oracles/independent'))
import r613_reference as oracle  # noqa: E402


def model(delay, true_times, obs_times, window=('0', '10')):
    return {'delay': delay, 'true_events': [{'time': t} for t in true_times],
            'observed_events': [{'time': t} for t in obs_times], 'window': list(window)}


cases = [
    ('EXACT_DELAY', model('1/2', ['1', '2'], ['3/2', '5/2']), 'OK'),
    ('DELAY_MISMATCH', model('1/2', ['1', '2'], ['3/2', '3'], ), 'DELAY_MISMATCH'),
    ('COUNT_MISMATCH', model('1/2', ['1', '2'], ['3/2']), 'COUNT_MISMATCH'),
    ('ZERO_DELAY', model('0', ['1', '2'], ['1', '2']), 'OK'),
    ('NEGATIVE_DELAY', model('-1/2', ['1', '2'], ['1/2', '3/2']), 'OK'),
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
    original = (ROOT / 'implementations/subject/r613.py').read_text(encoding='utf-8')
    if original.count(old) != 1: raise SystemExit('anchor ' + name)
    changed = original.replace(old, new); (folder / 'r613.py').write_text(changed, encoding='utf-8')
    (folder / 'mutation.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True), changed.splitlines(True))), encoding='utf-8')
    mod = load_module(folder / 'r613.py', 'mut_' + name)
    data, expected = next((d, e) for n, d, e in cases if n == target)
    got = mod.classify(copy.deepcopy(data)); ref = oracle.classify(copy.deepcopy(data))
    detected = got['category'] != ref['category']
    (folder / 'subject.json').write_text(json.dumps(got, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (folder / 'oracle.json').write_text(json.dumps(ref, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'mutation': name, 'target': target, 'detected': detected, 'observed': got['category'], 'expected': expected}


mutations = [
    mutate('M_IGNORE_DELAY', 'EXACT_DELAY',
           "    shifted = [t + delay for t in true_events]\n    if shifted != observed:",
           "    shifted = true_events\n    if shifted != observed:"),
    mutate('M_ALLOW_COUNT_MISMATCH', 'COUNT_MISMATCH',
           "    if len(true_events) != len(observed):",
           "    if False:"),
    mutate('M_DROP_NEGATIVE_DELAY', 'NEGATIVE_DELAY',
           "    shifted = [t + delay for t in true_events]",
           "    shifted = [t + abs(delay) for t in true_events]"),
]
with (OUT / 'results.csv').open('w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
summary = {'status': 'PASS' if all(r['status'] == 'PASS' for r in rows) and all(m['detected'] for m in mutations) else 'FAIL',
           'phase_gate': 'PROVISIONAL_R6_13_PARTIAL_NOT_PHASE_GATE', 'cases': len(rows),
           'passed': sum(r['status'] == 'PASS' for r in rows), 'mutations': mutations,
           'not_covered': ['general sensor fusion', 'full R6-13 suite']}
(OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
raise SystemExit(0 if summary['status'] == 'PASS' else 1)
