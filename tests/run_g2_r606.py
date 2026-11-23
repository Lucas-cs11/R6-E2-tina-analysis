#!/usr/bin/env python3
"""Run R6-06 observation/coarsening cases and source mutations."""

import copy
import csv
import difflib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'runs/g2_r606'
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / 'implementations/subject'))
import r606 as subject  # noqa: E402
sys.path.insert(0, str(ROOT / 'oracles/independent'))
import r606_reference as oracle  # noqa: E402


def path(pid, fault, labels, time, intermediate=None):
    return {'id': pid, 'fault': fault, 'labels': labels, 'completion_time': time,
            'intermediate_labels': intermediate or [], 'intermediate_times': ['1'],
            'external_completion': 'done', 'sample_termination': True}


def data(paths, fields, complete=True, prefix=True, quantum=None):
    return {'paths': paths, 'search_complete': complete,
            'psi': {'fields': fields, 'prefix_compatible': prefix, 'quantum': quantum}}


cases = [
    ('COMPLETION_ONLY_IGNORES_INTERMEDIATE', data([path('n', False, ['a'], '2', ['n1']), path('f', True, ['b'], '2', ['f1'])], ['completion_time']), '0'),
    ('FULL_WORD_DIFFERENT', data([path('n', False, ['a'], '2'), path('f', True, ['b'], '2')], ['word', 'completion_time']), 'PERP'),
    ('QUANTIZED_TIMES_MATCH', data([path('n', False, ['a'], '21/10'), path('f', True, ['a'], '24/10')], ['word', 'completion_time'], quantum='1'), '0'),
    ('INCOMPLETE_SEARCH_UNRESOLVED', data([path('n', False, ['a'], '2'), path('f', True, ['a'], '3')], ['word', 'completion_time'], complete=False), 'PERP'),
    ('NON_PREFIX_UNSUPPORTED', data([path('n', False, ['a'], '2'), path('f', True, ['a'], '2')], ['completion_time'], prefix=False), 'PERP'),
]
rows = []
for name, d, expected in cases:
    s = subject.evaluate(copy.deepcopy(d)); o = oracle.evaluate(copy.deepcopy(d))
    errors = []
    if s['verdict'] != expected or o['verdict'] != expected: errors.append('expected_verdict')
    if s['status'] != o['status'] or s['verdict'] != o['verdict']: errors.append('oracle_mismatch')
    sw = {(x['normal_path'], x['fault_path']) for x in s['witnesses']}
    ow = {(x['normal_path'], x['fault_path']) for x in o['witnesses']}
    if sw != ow: errors.append('witness_mismatch')
    (OUT / f'{name}.subject.json').write_text(json.dumps(s, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / f'{name}.oracle.json').write_text(json.dumps(o, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    rows.append({'test_id': name, 'expected': expected, 'subject_verdict': s['verdict'], 'oracle_verdict': o['verdict'],
                 'witnesses': len(sw), 'status': 'PASS' if not errors else 'FAIL', 'errors': ';'.join(errors)})

# Coarsening must produce a new ambiguity witness here.
coarse_data = data([path('n', False, ['a'], '2'), path('f', True, ['b'], '2')], ['word', 'completion_time'])
fine_s = subject.evaluate(copy.deepcopy(coarse_data)); fine_o = oracle.evaluate(copy.deepcopy(coarse_data))
coarse_s = subject.evaluate(copy.deepcopy(coarse_data), {'fields': ['completion_time'], 'prefix_compatible': True, 'quantum': None})
coarse_o = oracle.evaluate(copy.deepcopy(coarse_data), {'fields': ['completion_time'], 'prefix_compatible': True, 'quantum': None})
coarse_ok = fine_s['verdict'] == fine_o['verdict'] == 'PERP' and coarse_s['verdict'] == coarse_o['verdict'] == '0' and len(coarse_s['witnesses']) == 1
(OUT / 'COARSENING_NEW_AMBIGUITY.subject.json').write_text(json.dumps({'fine': fine_s, 'coarse': coarse_s}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(OUT / 'COARSENING_NEW_AMBIGUITY.oracle.json').write_text(json.dumps({'fine': fine_o, 'coarse': coarse_o}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
rows.append({'test_id': 'COARSENING_NEW_AMBIGUITY', 'expected': '1->0', 'subject_verdict': fine_s['verdict'] + '->' + coarse_s['verdict'],
             'oracle_verdict': fine_o['verdict'] + '->' + coarse_o['verdict'], 'witnesses': len(coarse_s['witnesses']),
             'status': 'PASS' if coarse_ok else 'FAIL', 'errors': '' if coarse_ok else 'coarsening'})


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def mutate(name, target_case, old, new):
    folder = OUT / 'mutations' / name
    folder.mkdir(parents=True, exist_ok=True)
    original = (ROOT / 'implementations/subject/r606.py').read_text(encoding='utf-8')
    if original.count(old) != 1: raise SystemExit('anchor ' + name)
    changed = original.replace(old, new); (folder / 'r606.py').write_text(changed, encoding='utf-8')
    (folder / 'mutation.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True), changed.splitlines(True))), encoding='utf-8')
    mod = load_module(folder / 'r606.py', 'mut_' + name)
    d, expected = next((d, e) for n, d, e in cases if n == target_case)
    got = mod.evaluate(copy.deepcopy(d)); detected = got['verdict'] != expected
    (folder / 'observed.json').write_text(json.dumps(got, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'mutation': name, 'target': target_case, 'detected': detected, 'observed': got['verdict'], 'expected': expected}


mutations = [
    mutate('M_READD_DROPPED_INTERMEDIATE_LABELS', 'COMPLETION_ONLY_IGNORES_INTERMEDIATE',
           "    if 'external_completion' in fields: out['external_completion'] = path.get('external_completion')\n    return out",
           "    if 'external_completion' in fields: out['external_completion'] = path.get('external_completion')\n    out['intermediate_labels'] = list(path.get('intermediate_labels', []))\n    return out"),
    mutate('M_INCOMPLETE_SEARCH_NO_AMBIGUITY', 'INCOMPLETE_SEARCH_UNRESOLVED',
           "    else:\n        # Absence of a witness is not proved by a self-declared boolean flag.\n        # This component only decides positive ambiguity from concrete paths.\n        verdict = 'PERP'",
           "    else:\n        verdict = '1'"),
]
with (OUT / 'results.csv').open('w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
summary = {'status': 'PASS' if all(r['status'] == 'PASS' for r in rows) and all(m['detected'] for m in mutations) else 'FAIL',
           'phase_gate': 'PROVISIONAL_R6_06_PARTIAL_NOT_PHASE_GATE', 'cases': len(rows),
           'passed': sum(r['status'] == 'PASS' for r in rows), 'mutations': mutations,
           'not_covered': ['complete SCG construction', 'general non-prefix-compatible psi', 'deadline sweep']}
(OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
raise SystemExit(0 if summary['status'] == 'PASS' else 1)
