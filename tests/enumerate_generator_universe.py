#!/usr/bin/env python3
"""Enumerate all 143,360 formal generator candidates with pre-run static validity rules."""

import csv
import hashlib
import json
import itertools
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCOPE = ROOT / 'scope'
OUT = SCOPE / 'generator_candidate_universe_full.csv'
RULES = SCOPE / 'model_validity_rules.json'

axes = {
    'machine_counts': [2, 3, 4, 5, 6, 8, 10],
    'part_type_counts': [1, 2, 3, 4, 6],
    'operations_per_part': [2, 4, 6, 8],
    'wip_bounds': [1, 2, 3, 4],
    'unobservable_ratios': [0.1, 0.3, 0.5, 0.7],
    'fault_locations': [1, 2, 4, 8],
    'interval_width_factors': [0.5, 1.0, 1.5, 2.0],
    'adjustable_ratios': [0.1, 0.25, 0.5, 0.75],
}
fixed = {
    'seed': 0, 'machine_capacity': 1, 'n_configs': 2, 'repair_domain': 'standard',
}
generator_sha = hashlib.sha256((SCOPE / 'rmt_fms_generator.py').read_bytes()).hexdigest()

rules = {
    'version': 'pre-run static only',
    'generator_sha256': generator_sha,
    'fixed_parameters': fixed,
    'rules': [
        {'id': 'R1', 'field': 'machine_counts', 'predicate': '>=1', 'note': 'at least one machine'},
        {'id': 'R2', 'field': 'part_type_counts', 'predicate': '>=1', 'note': 'at least one part type'},
        {'id': 'R3', 'field': 'operations_per_part', 'predicate': '>=1', 'note': 'at least one operation'},
        {'id': 'R4', 'field': 'wip_bounds', 'predicate': '>=1', 'note': 'positive work-in-process bound'},
        {'id': 'R5', 'field': 'unobservable_ratios', 'predicate': '0<=x<=1', 'note': 'valid ratio'},
        {'id': 'R6', 'field': 'fault_locations', 'predicate': '1<=x<=machine_counts', 'note': 'distinct fault machines must be realizable'},
        {'id': 'R7', 'field': 'interval_width_factors', 'predicate': '>0', 'note': 'positive width factor'},
        {'id': 'R8', 'field': 'adjustable_ratios', 'predicate': '0<=x<=1', 'note': 'valid ratio'},
    ],
    'status_labels': ['VALID_BY_FROZEN_RULE', 'INVALID_BY_FROZEN_RULE'],
    'note': 'validity is declared BEFORE any solver run; GENERATOR_ERROR may only be added by an actual generation attempt in a later phase',
}
RULES.write_text(json.dumps(rules, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def validity(m, j, ops, wip, u, fault, wf, adj):
    reasons = []
    if not (m >= 1): reasons.append('R1')
    if not (j >= 1): reasons.append('R2')
    if not (ops >= 1): reasons.append('R3')
    if not (wip >= 1): reasons.append('R4')
    if not (0 <= u <= 1): reasons.append('R5')
    if not (1 <= fault <= m): reasons.append('R6')
    if not (wf > 0): reasons.append('R7')
    if not (0 <= adj <= 1): reasons.append('R8')
    return ('VALID_BY_FROZEN_RULE' if not reasons else 'INVALID_BY_FROZEN_RULE'), ';'.join(reasons)

keys = list(axes)
with OUT.open('w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['candidate_id', 'machine_counts', 'part_type_counts', 'operations_per_part',
                'wip_bounds', 'unobservable_ratios', 'fault_locations', 'interval_width_factors',
                'adjustable_ratios', 'seed', 'machine_capacity', 'n_configs', 'repair_domain',
                'static_validity', 'invalid_reasons'])
    total = valid = invalid = 0
    for values in itertools.product(*(axes[k] for k in keys)):
        m, j, ops, wip, u, fault, wf, adj = values
        st, reason = validity(m, j, ops, wip, u, fault, wf, adj)
        total += 1
        if st == 'VALID_BY_FROZEN_RULE': valid += 1
        else: invalid += 1
        cid = f'RMT_m{m}_j{j}_ops{ops}_wip{wip}_u{u}_f{fault}_w{wf}_a{adj}'
        writer.writerow([cid, m, j, ops, wip, u, fault, wf, adj, fixed['seed'],
                    fixed['machine_capacity'], fixed['n_configs'], fixed['repair_domain'], st, reason])
summary = {
    'status': 'PASS' if total == 143360 else 'FAIL',
    'total_candidates': total, 'valid_by_frozen_rule': valid, 'invalid_by_frozen_rule': invalid,
    'axis_sizes': {k: len(v) for k, v in axes.items()},
    'cartesian_product': 7 * 5 * 4 * 4 * 4 * 4 * 4 * 4,
    'paper_minimum_subdomain': 54,
    'generator_sha256': generator_sha,
    'scope': 'static pre-run rules only; actual generation status is a later phase',
}
(SCOPE / 'generator_candidate_universe_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
raise SystemExit(0 if summary['status'] == 'PASS' else 1)
