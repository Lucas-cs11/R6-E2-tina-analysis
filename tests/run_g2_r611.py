#!/usr/bin/env python3
"""Run R6-11 Bayes error / coverage / coarsening cases and source mutations."""

import copy
import csv
import difflib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'runs/g2_r611'
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / 'implementations/subject'))
import r611 as subject  # noqa: E402
sys.path.insert(0, str(ROOT / 'oracles/independent'))
import r611_reference as oracle  # noqa: E402


cases = [
    ('FINE_UNRELIABLE', {'d0': {'a': '9/20', 'b': '9/20', 'c': '2/20'}, 'd1': {'a': '1/20', 'b': '1/20', 'c': '18/20'}}, None),
    ('FINE_RELIABLE', {'d0': {'a': '9/10', 'b': '1/10'}, 'd1': {'a': '1/10', 'b': '9/10'}}, None),
    ('COARSENING_A', {'d0': {'a': '9/10', 'b': '1/10'}, 'd1': {'a': '1/10', 'b': '9/10'}, 'coarsen': {'a': 'x', 'b': 'x'}}, None),
    ('COARSENING_B', {'d0': {'a': '5/10', 'b': '4/10', 'c': '1/10', 'd': '0'}, 'd1': {'a': '0', 'b': '1/10', 'c': '4/10', 'd': '5/10'},
                       'coarsen': {'a': 'x', 'b': 'x', 'c': 'y', 'd': 'y'}}, None),
]
rows = []
for name, data, _ in cases:
    s = subject.evaluate(copy.deepcopy(data)); o = oracle.evaluate(copy.deepcopy(data))
    errors = []
    for field in ('bayes_error', 'coverage', 'coarsened_bayes_error', 'coarsened_coverage'):
        if s[field] != o[field]: errors.append(f'{field}_mismatch')
    if not s['bayes_monotone']: errors.append('bayes_not_monotone')
    (OUT / f'{name}.subject.json').write_text(json.dumps(s, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / f'{name}.oracle.json').write_text(json.dumps(o, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    rows.append({'test_id': name, 'subject_bayes': s['bayes_error'], 'oracle_bayes': o['bayes_error'],
                 'subject_coverage': s['coverage'], 'oracle_coverage': o['coverage'],
                 'coarse_bayes': s['coarsened_bayes_error'], 'coarse_coverage': s['coarsened_coverage'],
                 'status': 'PASS' if not errors else 'FAIL', 'errors': ';'.join(errors)})


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def mutate(name, target, old, new):
    folder = OUT / 'mutations' / name
    folder.mkdir(parents=True, exist_ok=True)
    original = (ROOT / 'implementations/subject/r611.py').read_text(encoding='utf-8')
    if original.count(old) != 1: raise SystemExit('anchor ' + name)
    changed = original.replace(old, new); (folder / 'r611.py').write_text(changed, encoding='utf-8')
    (folder / 'mutation.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True), changed.splitlines(True))), encoding='utf-8')
    mod = load_module(folder / 'r611.py', 'mut_' + name)
    data, _ = next((d, e) for n, d, e in cases if n == target)
    got = mod.evaluate(copy.deepcopy(data)); ref = oracle.evaluate(copy.deepcopy(data))
    detected = any(got[f] != ref[f] for f in ('bayes_error', 'coverage', 'coarsened_bayes_error', 'coarsened_coverage'))
    (folder / 'subject.json').write_text(json.dumps(got, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (folder / 'oracle.json').write_text(json.dumps(ref, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'mutation': name, 'target': target, 'detected': detected}


mutations = [
    mutate('M_BAYES_MAX', 'FINE_UNRELIABLE',
           "    return sum((min(pi0 * F(d0.get(k, '0')), pi1 * F(d1.get(k, '0'))) for k in keys), F(0))",
           "    return sum((max(pi0 * F(d0.get(k, '0')), pi1 * F(d1.get(k, '0'))) for k in keys), F(0))"),
    mutate('M_COVERAGE_WRONG_POSTERIOR', 'FINE_RELIABLE',
           "        post = max(p0, p1) / s",
           "        post = min(p0, p1) / s"),
    mutate('M_COARSEN_MAP_WRONG', 'COARSENING_B',
           "    for k, v in d0.items(): out0[mapping[k]] = str(F(out0.get(mapping[k], '0')) + F(v))",
           "    for k, v in d0.items(): out0['z'] = str(F(out0.get('z', '0')) + F(v))"),
]
with (OUT / 'results.csv').open('w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
summary = {'status': 'PASS' if all(r['status'] == 'PASS' for r in rows) and all(m['detected'] for m in mutations) else 'FAIL',
           'phase_gate': 'PROVISIONAL_R6_11_PARTIAL_NOT_PHASE_GATE', 'cases': len(rows),
           'passed': sum(r['status'] == 'PASS' for r in rows), 'mutations': mutations,
           'not_covered': ['continuous distributions', 'full R6-11 suite']}
(OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
raise SystemExit(0 if summary['status'] == 'PASS' else 1)
