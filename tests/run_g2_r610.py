#!/usr/bin/env python3
"""Run R6-10 aligned pair and seven negative alignment variants."""

import copy
import csv
import difflib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'runs/g2_r610'
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / 'implementations/subject'))
import r610 as subject  # noqa: E402
sys.path.insert(0, str(ROOT / 'oracles/independent'))
import r610_reference as oracle  # noqa: E402


def aligned():
    logical = [
        {'id': 'n', 'fault': False, 'completion': True, 'completion_marking': 'M_c', 'support': ['1', '2'], 'enabling_signature': 'persistent'},
        {'id': 'f', 'fault': True, 'completion': True, 'completion_marking': 'M_c', 'support': ['3', '4'], 'enabling_signature': 'persistent'},
    ]
    probability = [
        {'id': 'n', 'fault': False, 'completion': True, 'completion_marking': 'M_c', 'support': ['1', '2'],
         'enabling_signature': 'persistent', 'observation': 'y0', 'external_completion': 'done', 'measurable': True},
        {'id': 'f', 'fault': True, 'completion': True, 'completion_marking': 'M_c', 'support': ['3', '4'],
         'enabling_signature': 'persistent', 'observation': 'y1', 'external_completion': 'done', 'measurable': True},
    ]
    return {'logical_paths': logical, 'probability_paths': probability,
            'logical_H_psi': '0', 'probability_H_psi': '0',
            'observation_map': {'n': 'y0', 'f': 'y1'},
            'post_completion_observed': False, 'internal_unobservable_deadlock': False}


variants = [('ALIGNED', lambda p: None, 'THEOREM_APPLICABLE', None)]
for name, field in [
    ('NO_EXTERNAL_COMPLETION', 'external_completion'),
    ('FAULT_WINDOW_MISMATCH', 'fault_domain'),
    ('COMPLETION_DOMAIN_MISMATCH', 'completion_domain'),
    ('OBSERVATION_NOT_INJECTIVE', 'observation_injective'),
    ('POST_COMPLETION_EXTRA_INFO', 'no_post_completion_information'),
    ('SUPPORT_MISMATCH', 'support_alignment'),
    ('HIDDEN_INTERNAL_DEADLOCK', 'no_hidden_internal_deadlock'),
]:
    def change(p, field=field, name=name):
        if name == 'NO_EXTERNAL_COMPLETION': p['probability_paths'][0]['external_completion'] = ''
        elif name == 'FAULT_WINDOW_MISMATCH': p['probability_H_psi'] = '1'
        elif name == 'COMPLETION_DOMAIN_MISMATCH': p['probability_paths'][0]['completion_marking'] = 'other'
        elif name == 'OBSERVATION_NOT_INJECTIVE': p['observation_map']['f'] = 'y0'
        elif name == 'POST_COMPLETION_EXTRA_INFO': p['post_completion_observed'] = True
        elif name == 'SUPPORT_MISMATCH': p['probability_paths'][0]['support'] = ['0', '2']
        elif name == 'HIDDEN_INTERNAL_DEADLOCK': p['internal_unobservable_deadlock'] = True
    variants.append((name, change, 'THEOREM_NOT_APPLICABLE', field))

rows = []
for name, change, expected, failed_check in variants:
    pair = aligned(); change(pair)
    s = subject.check(copy.deepcopy(pair)); o = oracle.check(copy.deepcopy(pair))
    errors = []
    if s['status'] != expected or o['status'] != expected: errors.append('status')
    if s['alignment_checks'] != o['alignment_checks']: errors.append('oracle_alignment_mismatch')
    if failed_check and s['alignment_checks'].get(failed_check) is not False: errors.append('specific_alignment_not_detected')
    if s['counterexample_claimed'] or o['counterexample_claimed']: errors.append('mislabeled_counterexample')
    (OUT / f'{name}.subject.json').write_text(json.dumps(s, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / f'{name}.oracle.json').write_text(json.dumps(o, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    rows.append({'test_id': name, 'expected': expected, 'subject': s['status'], 'oracle': o['status'],
                 'failed_check': failed_check or '', 'status_test': 'PASS' if not errors else 'FAIL', 'errors': ';'.join(errors)})


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def mutate(name, target, old, new):
    folder = OUT / 'mutations' / name
    if folder.exists(): shutil.rmtree(folder)
    folder.mkdir(parents=True)
    original = (ROOT / 'implementations/subject/r610.py').read_text(encoding='utf-8')
    if original.count(old) != 1: raise SystemExit('anchor ' + name)
    changed = original.replace(old, new); (folder / 'r610.py').write_text(changed, encoding='utf-8')
    (folder / 'mutation.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True), changed.splitlines(True))), encoding='utf-8')
    mod = load_module(folder / 'r610.py', 'mut_' + name)
    pair = aligned()
    if target == 'NO_EXTERNAL_COMPLETION': pair['probability_paths'][0]['external_completion'] = ''
    if target == 'SUPPORT_MISMATCH': pair['probability_paths'][0]['support'] = ['0', '2']
    got = mod.check(pair)
    detected = got['status'] != 'THEOREM_NOT_APPLICABLE'
    (folder / 'observed.json').write_text(json.dumps(got, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'mutation': name, 'target': target, 'detected': detected, 'observed_status': got['status']}


mutations = [
    mutate('M_THEOREM_WITHOUT_EXTERNAL', 'NO_EXTERNAL_COMPLETION',
           '    applicable = all(checks.values())',
           "    applicable = all(v for k, v in checks.items() if k != 'external_completion')"),
    mutate('M_THEOREM_WITHOUT_SUPPORT', 'SUPPORT_MISMATCH',
           '    applicable = all(checks.values())',
           "    applicable = all(v for k, v in checks.items() if k != 'support_alignment')"),
]
with (OUT / 'results.csv').open('w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
summary = {'status': 'PASS' if all(r['status_test'] == 'PASS' for r in rows) and all(m['detected'] for m in mutations) else 'FAIL',
           'phase_gate': 'PROVISIONAL_R6_10_PARTIAL_NOT_PHASE_GATE', 'cases': len(rows),
           'passed': sum(r['status_test'] == 'PASS' for r in rows), 'mutations': mutations,
           'not_covered': ['general measurable-support proof', 'automatic LSTPN extraction', 'theorem counterexample search']}
(OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
raise SystemExit(0 if summary['status'] == 'PASS' else 1)
