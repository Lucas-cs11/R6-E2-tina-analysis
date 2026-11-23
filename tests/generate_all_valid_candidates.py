#!/usr/bin/env python3
"""Actually generate and structurally validate every VALID 8-axis candidate (streaming, resumable)."""

import csv
import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'implementations/generator_compat'))
from src.benchmarks.rmt_fms_generator import generate_rmt_fms  # noqa: E402

UNIVERSE = ROOT / 'scope/generator_candidate_universe_full.csv'
OUT = ROOT / 'results/all_population_results.csv'
FIXED = {'seed': 0, 'machine_capacity': 1, 'n_configs': 2, 'repair_domain': 'standard'}


def canonical(net, params, L, H):
    return {
        'parameters': params, 'places': sorted(net.places),
        'transitions': {n: {'label': t.label, 'is_fault': t.is_fault, 'is_adjustable': t.is_adjustable,
                            'interval': [str(t.interval.earliest), str(t.interval.latest)],
                            'admissible': [[str(x.earliest), str(x.latest)] for x in t.admissible_intervals],
                            'authorized': None if t.authorized_range is None else [
                                str(t.authorized_range.l_min), str(t.authorized_range.l_max),
                                str(t.authorized_range.u_min), str(t.authorized_range.u_max),
                                str(t.authorized_range.resolution)]}
                         for n, t in sorted(net.transitions.items())},
        'arcs': sorted([a.from_node, a.to_node] for a in net.arcs),
        'initial_marking': dict(sorted(net.initial_marking.items())),
        'completion_markings': [dict(sorted(m.items())) for m in net.completion_markings],
        'L': L, 'H': H,
    }


def validate(net, params, L, H):
    issues = []
    ps, ts = net.places, net.transitions
    if len(ps) != len(set(ps)): issues.append('dup_place')
    if len(ts) != len(set(ts)): issues.append('dup_transition')
    pset, tset = set(ps), set(ts)
    incoming = {t: [] for t in ts}; outgoing = {t: [] for t in ts}
    for a in net.arcs:
        if a.from_node not in pset and a.from_node not in tset: issues.append('bad_arc_from')
        if a.to_node not in pset and a.to_node not in tset: issues.append('bad_arc_to')
        if a.from_node in tset and a.to_node in pset: outgoing[a.from_node].append(a.to_node)
        elif a.from_node in pset and a.to_node in tset: incoming[a.to_node].append(a.from_node)
        else: issues.append('arc_orientation')
    for name, tr in ts.items():
        if not incoming[name] or not outgoing[name]: issues.append('no_pre_post_' + name)
        if tr.interval.earliest < 0 or tr.interval.earliest > tr.interval.latest: issues.append('bad_interval_' + name)
        for iv in tr.admissible_intervals:
            if iv.earliest < 0 or iv.earliest > iv.latest: issues.append('bad_admissible_' + name)
        if tr.authorized_range is not None:
            ar = tr.authorized_range
            if not (0 <= ar.l_min <= ar.l_max and 0 <= ar.u_min <= ar.u_max and ar.resolution > 0):
                issues.append('bad_authorized_' + name)
    for p, n in net.initial_marking.items():
        if p not in pset or n < 0: issues.append('bad_initial')
    if not net.completion_markings: issues.append('no_completion')
    for m in net.completion_markings:
        for p, n in m.items():
            if p not in pset or n < 0: issues.append('bad_completion')
    if L != 2 * (params['ops_per_part'] * params['n_parts']) + 2: issues.append('L_formula')
    return issues


def main():
    rows = list(csv.DictReader(UNIVERSE.open(newline='', encoding='utf-8')))
    valid = [r for r in rows if r['static_validity'] == 'VALID_BY_FROZEN_RULE']
    # resume: skip already recorded ids
    done = set()
    if OUT.exists():
        for r in csv.DictReader(OUT.open(newline='', encoding='utf-8')):
            done.add(r['candidate_id'])
    fieldnames = ['candidate_id', 'status', 'model_sha256', 'places', 'transitions', 'arcs', 'L', 'H', 'structural_issues']
    write_header = not OUT.exists()
    with OUT.open('a', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header: w.writeheader()
        for r in valid:
            if r['candidate_id'] in done: continue
            params = {'n_machines': int(r['machine_counts']), 'n_parts': int(r['part_type_counts']),
                      'ops_per_part': int(r['operations_per_part']), 'wip_bound': int(r['wip_bounds']),
                      'unobservable_ratio': float(r['unobservable_ratios']),
                      'fault_locations': int(r['fault_locations']),
                      'interval_width_factor': float(r['interval_width_factors']),
                      'adjustable_ratio': float(r['adjustable_ratios']),
                      'seed': FIXED['seed'], 'machine_capacity': FIXED['machine_capacity'],
                      'n_configs': FIXED['n_configs'], 'repair_domain': FIXED['repair_domain']}
            try:
                net, L, H = generate_rmt_fms(**params)
                issues = validate(net, params, L, H)
                payload = canonical(net, params, L, H)
                digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
                status = 'GENERATED_STRUCTURE_PASS' if not issues else 'GENERATED_STRUCTURE_ISSUES'
            except Exception as exc:
                status = 'GENERATOR_ERROR'
                L = H = digest = ''
                issues = [f'{type(exc).__name__}: {exc}']
                net = type('N', (), {'places': {}, 'transitions': {}, 'arcs': []})()
            w.writerow({'candidate_id': r['candidate_id'], 'status': status, 'model_sha256': digest,
                        'places': len(net.places), 'transitions': len(net.transitions),
                        'arcs': len(net.arcs), 'L': L, 'H': H, 'structural_issues': ';'.join(issues)})
            f.flush()
    print('processed window done')


if __name__ == '__main__':
    main()
