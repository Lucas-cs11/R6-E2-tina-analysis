#!/usr/bin/env python3
"""Execute R6-03 finite TPN models and mutation controls."""

import csv
import difflib
import importlib.util
import json
import shutil
import sys
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'runs/g2_r603'
LOG = OUT / 'raw'
OUT.mkdir(parents=True, exist_ok=True); LOG.mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT / 'implementations/subject'))
import r603 as subject  # noqa: E402
sys.path.insert(0, str(ROOT / 'oracles/independent'))
import r603_reference as oracle  # noqa: E402


def compare(s, o):
    errors = []
    for key in ('model_id', 'leaves', 'termination_mass', 'resolved_mass', 'frontier_mass', 'mass_total'):
        if s.get(key) != o.get(key): errors.append(key)
    if F(s['mass_total']) != 1: errors.append('mass_total_not_one')
    if F(s['resolved_mass']) + F(s['frontier_mass']) != F(s['mass_total']): errors.append('partition')
    if any(x['termination'] == 'unresolved_frontier' and x['sample_termination'] for x in s['leaves']):
        errors.append('frontier_as_sample_termination')
    return errors


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


cases = [
    ('five_outcomes', {'completed_first': '2/5', 'other_resolved': '1/5', 'unfinished_deadlock': '1/5',
                       'horizon_incomplete': '1/5', 'unresolved_frontier': '0'}, '1', '0'),
    ('budget_frontier', {'completed_first': '1/5', 'other_resolved': '1/5', 'unfinished_deadlock': '1/5',
                         'horizon_incomplete': '1/5', 'unresolved_frontier': '1/5'}, '4/5', '1/5'),
    ('endpoint', {'completed_first': '3/5', 'other_resolved': '1/5', 'unfinished_deadlock': '1/5',
                  'horizon_incomplete': '0', 'unresolved_frontier': '0'}, '1', '0'),
]
rows = []
for name, expected_terms, resolved, frontier in cases:
    model = json.loads((ROOT / 'models/r603' / f'{name}.json').read_text(encoding='utf-8'))
    s = subject.execute(model); o = oracle.run(model)
    all_terms = {'completed_first', 'other_resolved', 'unfinished_deadlock', 'horizon_incomplete', 'unresolved_frontier'}
    for term in all_terms:
        s['termination_mass'].setdefault(term, '0')
        o['termination_mass'].setdefault(term, '0')
    errors = compare(s, o)
    terms = s['termination_mass']
    if terms != expected_terms: errors.append('expected_termination_mass')
    if s['resolved_mass'] != resolved or s['frontier_mass'] != frontier: errors.append('expected_partition')
    (LOG / f'{name}.subject.json').write_text(json.dumps(s, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (LOG / f'{name}.oracle.json').write_text(json.dumps(o, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (LOG / f'{name}.comparison.json').write_text(json.dumps({'errors': errors}, indent=2) + '\n', encoding='utf-8')
    rows.append({'test_id': name, 'expected_terms': json.dumps(expected_terms, sort_keys=True),
                 'actual_terms': json.dumps(terms, sort_keys=True), 'resolved_mass': s['resolved_mass'],
                 'frontier_mass': s['frontier_mass'], 'mass_total': s['mass_total'],
                 'status': 'PASS' if not errors else 'FAIL', 'errors': ';'.join(errors)})


def mutate(name, old, new):
    folder = OUT / 'mutations' / name
    if folder.exists(): shutil.rmtree(folder)
    folder.mkdir(parents=True)
    target = folder / 'r603.py'; original = (ROOT / 'implementations/subject/r603.py').read_text(encoding='utf-8')
    if original.count(old) != 1: raise SystemExit('anchor ' + name)
    changed = original.replace(old, new); target.write_text(changed, encoding='utf-8')
    (folder / 'mutation.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True), changed.splitlines(True))), encoding='utf-8')
    mod = load_module(target, 'mut_' + name)
    model = json.loads((ROOT / 'models/r603' / ('endpoint.json' if name == 'M_TRUNCATE_BEFORE_DUE' else 'budget_frontier.json')).read_text(encoding='utf-8'))
    got = mod.execute(model); ref = oracle.run(model)
    errors = compare(got, ref)
    (folder / 'subject.json').write_text(json.dumps(got, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (folder / 'oracle.json').write_text(json.dumps(ref, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'mutation': name, 'detected': bool(errors), 'errors': errors,
            'observed_termination_mass': got['termination_mass'], 'observed_mass_total': got['mass_total']}


mutations = [
    mutate('M_DROP_DEADLOCK_FRONTIER_RENORMALIZE',
           "    resolved = sum((x['mass'] for x in leaves if x['resolved']), F(0))",
           "    leaves = [x for x in leaves if x['termination'] not in {'unfinished_deadlock', 'unresolved_frontier'}]\n    resolved = sum((x['mass'] for x in leaves if x['resolved']), F(0))\n    for x in leaves:\n        x['mass'] = x['mass'] / resolved"),
    mutate('M_LEGAL_END_AS_COMPLETION',
           "    if marking in model.get('legal_noncompletion_markings', []): return 'other_resolved'",
           "    if marking in model.get('legal_noncompletion_markings', []): return 'completed_first'"),
    mutate('M_TRUNCATE_BEFORE_DUE',
           "    if event_time > F(model['H_A']):", "    if event_time >= F(model['H_A']):"),
]
with (OUT / 'results.csv').open('w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
summary = {'status': 'PASS' if all(r['status'] == 'PASS' for r in rows) and all(m['detected'] for m in mutations) else 'FAIL',
           'phase_gate': 'PROVISIONAL_R6_03_PARTIAL_NOT_PHASE_GATE', 'cases': len(rows),
           'passed': sum(r['status'] == 'PASS' for r in rows), 'mutations': mutations,
           'supported_domain': 'finite exclusive immediate roots and one fixed-delay enabled timed transition per branch',
           'not_covered': ['general continuous propagation', 'H0/H1 fault-window split', 'unbounded immediate closure']}
(OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
raise SystemExit(0 if summary['status'] == 'PASS' else 1)
