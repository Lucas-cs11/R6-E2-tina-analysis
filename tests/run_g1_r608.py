#!/usr/bin/env python3
"""G1 R6-08 corrected joint-feasibility tests with real source mutations."""

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
import ap41_r6 as subject  # noqa: E402
import ap41_reference as oracle  # noqa: E402
RUNS = ROOT / 'runs/g1_r608'
RUNS.mkdir(parents=True, exist_ok=True)


def base():
    return {'q0': {'low': '0', 'high': '1/2'}, 'q1': {'low': '0', 'high': '1/2'},
            'v_c': '1', 'Pe': {'low': '0', 'high': '1/4'}, 'Gamma': {'low': '1/2', 'high': '3/4'},
            'pi0': '1/2', 'pi1': '1/2', 'epsilon': '1/4', 'delta': '1/4', 'gamma': '1/2',
            'evidence_valid': True}


def d(**kw):
    x = base(); x.update(kw); return x


cases = [
    ('COMPLEMENT_SYMMETRIC_TIGHTEN', d(), ('DECIDED', '1', '1')),
    ('JOINT_INCOMPATIBLE_INVALID', d(q0={'low': '0', 'high': '1/4'}, q1={'low': '0', 'high': '1/4'}), ('INVALID_EVIDENCE', None, None)),
    ('ONE_SIDED_COMPLEMENT', d(q0={'low': '0', 'high': '1/2'}, q1={'low': '1/2', 'high': '1/2'}, v_c='0'), ('DECIDED', '1', '0')),
    ('ZERO_Q0', d(q0={'low': '0', 'high': '0'}, q1={'low': '1', 'high': '1'}), ('DECIDED', '0', 'NULL')),
    ('ZERO_Q1', d(q0={'low': '1', 'high': '1'}, q1={'low': '0', 'high': '0'}), ('DECIDED', '0', 'NULL')),
    ('POSITIVE_UNPROVEN', d(q0={'low': '0', 'high': '1'}, q1={'low': '0', 'high': '1'}), ('DECIDED', 'PERP', 'NULL')),
    ('VC0_PRIORITY', d(q0={'low': '1/2', 'high': '1/2'}, q1={'low': '1/2', 'high': '1/2'}, v_c='0'), ('DECIDED', '1', '0')),
    ('VC1_ALL_POSITIVE', d(q0={'low': '1/2', 'high': '1/2'}, q1={'low': '1/2', 'high': '1/2'}), ('DECIDED', '1', '1')),
    ('VC1_INCOMPLETE', d(q0={'low': '1/2', 'high': '1/2'}, q1={'low': '1/2', 'high': '1/2'}, Pe={'low': '1/8', 'high': '3/8'}), ('DECIDED', '1', 'PERP')),
    ('PE_LOWER_STRICT', d(q0={'low': '1/2', 'high': '1/2'}, q1={'low': '1/2', 'high': '1/2'}, v_c='PERP', Pe={'low': '3/8', 'high': '1/2'}), ('DECIDED', '1', '0')),
    ('GAMMA_UPPER_STRICT', d(q0={'low': '1/2', 'high': '1/2'}, q1={'low': '1/2', 'high': '1/2'}, v_c='PERP', Gamma={'low': '0', 'high': '1/4'}), ('DECIDED', '1', '0')),
    ('PE_EQUALITY_NOT_NEG', d(q0={'low': '1/2', 'high': '1/2'}, q1={'low': '1/2', 'high': '1/2'}, v_c='PERP', Pe={'low': '1/4', 'high': '1/4'}), ('DECIDED', '1', 'PERP')),
    ('GAMMA_EQUALITY_NOT_NEG', d(q0={'low': '1/2', 'high': '1/2'}, q1={'low': '1/2', 'high': '1/2'}, v_c='PERP', Gamma={'low': '0', 'high': '1/2'}), ('DECIDED', '1', 'PERP')),
    ('PE_ABOVE_MIN_PI', d(q0={'low': '1/2', 'high': '1/2'}, q1={'low': '1/2', 'high': '1/2'}, Pe={'low': '3/4', 'high': '4/5'}), ('INVALID_EVIDENCE', None, None)),
    ('Q0_REVERSED', d(q0={'low': '1/2', 'high': '1/4'}), ('INVALID_EVIDENCE', None, None)),
    ('EXTERNAL_FLAG_NO_BYPASS', d(q0={'low': '0', 'high': '1/4'}, q1={'low': '0', 'high': '1/4'}, evidence_valid=True), ('INVALID_EVIDENCE', None, None)),
    # Audit counterexamples: loose upper must be clamped, not rejected.
    ('QY_LOOSE_UPPER_CLAMP', d(q0={'low': '1/2', 'high': '1/2'}, q1={'low': '1/2', 'high': '1/2'}, Q0_Y={'low': '0', 'high': '3/4'}), ('DECIDED', '1', '1')),
    ('QY_LOWER_ABOVE_Q', d(q0={'low': '1/2', 'high': '1/2'}, q1={'low': '1/2', 'high': '1/2'}, Q0_Y={'low': '3/5', 'high': '3/4'}), ('INVALID_EVIDENCE', None, None)),
    ('QY_EXACT_AT_Q', d(q0={'low': '1/2', 'high': '1/2'}, q1={'low': '1/2', 'high': '1/2'}, Q0_Y={'low': '1/2', 'high': '1/2'}), ('DECIDED', '1', '1')),
    ('QY_NEGATIVE_LOWER', d(q0={'low': '1/2', 'high': '1/2'}, q1={'low': '1/2', 'high': '1/2'}, Q0_Y={'low': '-1/4', 'high': '1/2'}), ('INVALID_EVIDENCE', None, None)),
]


def core(r):
    return r.get('status'), r.get('a_P'), r.get('v_P')


rows = []
for name, data, expected in cases:
    s = subject.decide(copy.deepcopy(data)); o = oracle.decide(copy.deepcopy(data))
    ok = core(s) == expected == core(o)
    rows.append({'test_id': name, 'expected': json.dumps(expected), 'subject_status': s.get('status'),
                 'subject_a': s.get('a_P') or 'NULL', 'subject_v': s.get('v_P') or 'NULL',
                 'oracle_status': o.get('status'), 'oracle_a': o.get('a_P') or 'NULL',
                 'oracle_v': o.get('v_P') or 'NULL', 'status': 'PASS' if ok else 'FAIL'})
with (RUNS / 'results.csv').open('w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def mutate(name, target_case, old, new):
    folder = RUNS / 'mutations' / name
    if folder.exists(): shutil.rmtree(folder)
    (folder / 'subject').mkdir(parents=True)
    t = folder / 'subject' / 'ap41_r6.py'; shutil.copy2(ROOT / 'implementations/subject/ap41_r6.py', t)
    text = t.read_text(encoding='utf-8')
    if text.count(old) != 1: raise SystemExit('anchor ' + name)
    changed = text.replace(old, new); t.write_text(changed, encoding='utf-8')
    (folder / 'mutation.patch').write_text(''.join(__import__('difflib').unified_diff(text.splitlines(True), changed.splitlines(True))), encoding='utf-8')
    mod = load_module(t, 'mut_' + name)
    data, expected = next((d, e) for n, d, e in cases if n == target_case)
    got = mod.decide(copy.deepcopy(data)); detected = core(got) != expected
    (folder / 'observed.json').write_text(json.dumps(got, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'mutation': name, 'target': target_case, 'detected': detected, 'expected': list(expected), 'observed': list(core(got))}


mutations = [
    mutate('M_NO_COMPLEMENT', 'COMPLEMENT_SYMMETRIC_TIGHTEN',
           't0 = (max(q0[0], 1 - q1[1]), min(q0[1], 1 - q1[0]))\n        t1 = (max(q1[0], 1 - q0[1]), min(q1[1], 1 - q0[0]))', 't0 = q0\n        t1 = q1'),
    mutate('M_ACCEPT_INCOMPATIBLE', 'JOINT_INCOMPATIBLE_INVALID',
           "        if q0[0] + q1[0] > 1 or q0[1] + q1[1] < 1:\n            raise EvidenceError('q0+q1=1 jointly infeasible (INVALID_EVIDENCE)')\n        t0 = (max(q0[0], 1 - q1[1]), min(q0[1], 1 - q1[0]))\n        t1 = (max(q1[0], 1 - q0[1]), min(q1[1], 1 - q0[0]))\n        if t0[0] > t0[1] or t1[0] > t1[1]:\n            raise EvidenceError('complement tightening empty (INVALID_EVIDENCE)')",
           "        if False:\n            pass\n        t0 = q0\n        t1 = q1"),
    mutate('M_LOOSE_UPPER_REJECT', 'QY_LOOSE_UPPER_CLAMP',
           "if qy[0] > q[1]:\n                    raise EvidenceError(name + ' lower bound exceeds q_i upper bound (infeasible)')",
           "if qy[1] > q[1]:\n                    raise EvidenceError(name + ' exceeds q_i upper bound (old wrong rule)')"),
    mutate('M_LOWER_ABOVE_ACCEPT', 'QY_LOWER_ABOVE_Q',
           "if qy[0] > q[1]:\n                    raise EvidenceError(name + ' lower bound exceeds q_i upper bound (infeasible)')",
           "if False:\n                    pass"),
    mutate('M_EQUALITY_STRICT', 'PE_EQUALITY_NOT_NEG', 'if pe[0] > eps:', 'if pe[0] >= eps:'),
]
summary = {'status': 'PASS' if all(r['status'] == 'PASS' for r in rows) and all(m['detected'] for m in mutations) else 'FAIL',
           'cases': len(rows), 'passed': sum(r['status'] == 'PASS' for r in rows), 'mutations': mutations,
           'p0_audit_fix': 'loose upper Q clamped via intersection; only lower>q upper is infeasible',
           'note': 'independent oracle uses separate linear feasibility path'}
(RUNS / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
raise SystemExit(0 if summary['status'] == 'PASS' else 1)
