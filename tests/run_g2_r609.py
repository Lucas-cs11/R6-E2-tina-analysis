#!/usr/bin/env python3
"""Run R6-09 discrete-support sequence likelihood cases and source mutations."""

import copy
import csv
import difflib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'runs/g2_r609'
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / 'implementations/subject'))
import r609 as subject  # noqa: E402
sys.path.insert(0, str(ROOT / 'oracles/independent'))
import r609_reference as oracle  # noqa: E402


def model(seq, e0, e1, prior=('1/2', '1/2'), bound=None):
    d = {'sequence': seq, 'emission': {'H0': e0, 'H1': e1}, 'prior': {'H0': prior[0], 'H1': prior[1]}}
    if bound is not None: d['evidence_lower_bound'] = bound
    return d


cases = [
    ('LIKE_POSTERIOR', model(['a', 'b'], {'a': '1/2', 'b': '1/2'}, {'a': '1/4', 'b': '3/4'}), 'OK'),
    ('ZERO_LIKELIHOOD', model(['c'], {'a': '1'}, {'a': '1'}), 'ZERO_LIKELIHOOD'),
    ('EVIDENCE_BELOW_BOUND', model(['a'], {'a': '1/100'}, {'a': '1/100'}, bound='-1'), 'EVIDENCE_BELOW_BOUND'),
    ('NORMALIZATION_MISMATCH', model(['a'], {'a': '1'}, {'a': '1'}, prior=('2/3', '2/3')), 'NORMALIZATION_MISMATCH'),
    ('BIASED_POSTERIOR', model(['a', 'a'], {'a': '1/4', 'b': '3/4'}, {'a': '3/4', 'b': '1/4'}), 'OK'),
]
rows = []
for name, data, expected in cases:
    s = subject.posterior(copy.deepcopy(data)); o = oracle.posterior(copy.deepcopy(data))
    errors = []
    if s['category'] != expected or o['category'] != expected: errors.append('expected_category')
    if s['category'] != o['category']: errors.append('oracle_mismatch')
    if s['category'] == 'OK' and o['category'] == 'OK':
        for hyp in ('H0', 'H1'):
            from fractions import Fraction as F
            if abs(F(s['posterior'][hyp]) - F(o['posterior'][hyp])) > F(1, 10**9): errors.append(f'posterior_mismatch_{hyp}')
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
    original = (ROOT / 'implementations/subject/r609.py').read_text(encoding='utf-8')
    if original.count(old) != 1: raise SystemExit('anchor ' + name)
    changed = original.replace(old, new); (folder / 'r609.py').write_text(changed, encoding='utf-8')
    (folder / 'mutation.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True), changed.splitlines(True))), encoding='utf-8')
    mod = load_module(folder / 'r609.py', 'mut_' + name)
    data, expected = next((d, e) for n, d, e in cases if n == target)
    ref = oracle.posterior(copy.deepcopy(data))
    try:
        got = mod.posterior(copy.deepcopy(data))
        detected = got['category'] != ref['category']
    except Exception:
        got = {'status': 'EXCEPTION', 'category': 'EXCEPTION'}; detected = True
    (folder / 'subject.json').write_text(json.dumps(got, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (folder / 'oracle.json').write_text(json.dumps(ref, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'mutation': name, 'target': target, 'detected': detected, 'observed': got['category'], 'expected': expected}


mutations = [
    mutate('M_SKIP_ZERO_CHECK', 'ZERO_LIKELIHOOD',
           "    if total == 0:",
           "    if False:"),
    mutate('M_ACCEPT_BAD_PRIOR', 'NORMALIZATION_MISMATCH',
           "    if prior0 + prior1 != 1:",
           "    if False:"),
    mutate('M_IGNORE_EVIDENCE_BOUND', 'EVIDENCE_BELOW_BOUND',
           "    if model.get('evidence_lower_bound') is not None and evidence < float(model['evidence_lower_bound']):",
           "    if False:"),
]
with (OUT / 'results.csv').open('w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
summary = {'status': 'PASS' if all(r['status'] == 'PASS' for r in rows) and all(m['detected'] for m in mutations) else 'FAIL',
           'phase_gate': 'PROVISIONAL_R6_09_PARTIAL_NOT_PHASE_GATE', 'cases': len(rows),
           'passed': sum(r['status'] == 'PASS' for r in rows), 'mutations': mutations,
           'not_covered': ['continuous emission', 'full R6-09 suite', 'general Bayes with continuous support']}
(OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
raise SystemExit(0 if summary['status'] == 'PASS' else 1)
