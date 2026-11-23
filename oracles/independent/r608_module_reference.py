#!/usr/bin/env python3
"""Independent R6-08 module error-path reference."""

from fractions import Fraction as Q

C = 'R6-E2-R6-08-MODULE-PARTIAL'
TEX = 'a4196145c95812ff19376a5985b6a6f2cf469d432c80836071cad1c8ac174c5a'


def check(evidence):
    if evidence.get('model_input_invalid'): return 'MODEL_INPUT_INVALID'
    if not evidence.get('certified_interval'): return 'UNCERTIFIED_INTERVAL'
    q = {k: (Q(v[0]), Q(v[1])) for k, v in evidence['q_intervals'].items()}
    if sum((x[0] for x in q.values()), Q(0)) > 1 or sum((x[1] for x in q.values()), Q(0)) < 1:
        return 'COMPLEMENT_INFEASIBLE'
    for k, (lo, hi) in q.items():
        if lo > hi or lo < 0 or hi > 1: return 'BOUND_INVALID'
    for k, v in evidence.get('Q_intervals', {}).items():
        lo, hi = Q(v[0]), Q(v[1])
        base = q.get(k[1], (Q(0), Q(1))) if isinstance(k, tuple) and len(k) == 2 else q.get(k, (Q(0), Q(1)))
        if lo > base[1]: return 'JOINT_INFEASIBLE'
        if hi < 0: return 'BOUND_INVALID'
    if evidence.get('same_event_source') and not evidence.get('source_consistent'):
        return 'SOURCE_INCONSISTENT'
    if evidence.get('category_sums') is not None:
        for cls, total in evidence['category_sums'].items():
            src = sum((Q(x) for x in evidence.get('per_category_source', {}).get(cls, [])), Q(0))
            if Q(total) > src: return 'CATEGORY_SUM_EXCEEDS'
    if not evidence.get('integration_method'): return 'NO_METHOD'
    if evidence.get('search_incomplete'): return 'SEARCH_INCOMPLETE'
    return 'OK'
