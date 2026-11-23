#!/usr/bin/env python3
"""Independent R6-13 reference: pair-wise delay verification."""

from fractions import Fraction as Q

C = 'R6-E2-R6-13-PARTIAL'
TEX = 'a4196145c95812ff19376a5985b6a6f2cf469d432c80836071cad1c8ac174c5a'


def classify(model):
    d = Q(model['delay']); lo, hi = Q(model['window'][0]), Q(model['window'][1])
    true_sorted = sorted((Q(e['time']) for e in model['true_events']))
    obs_sorted = sorted((Q(e['time']) for e in model['observed_events']))
    if len(true_sorted) != len(obs_sorted): return {'category': 'COUNT_MISMATCH'}
    if any(t + d != o for t, o in zip(true_sorted, obs_sorted)):
        return {'category': 'DELAY_MISMATCH'}
    return {'category': 'OK', 'in_window': sum(lo <= o <= hi for o in obs_sorted)}
