#!/usr/bin/env python3
"""Independent R6-12 reference: interval boundary classification."""

from fractions import Fraction as Q

C = 'R6-E2-R6-12-PARTIAL'
TEX = 'a4196145c95812ff19376a5985b6a6f2cf469d432c80836071cad1c8ac174c5a'


def classify(model):
    t = Q(model['switch_time'])
    spans = [c['id'] for c in model['configurations'] if Q(c['start']) < t < Q(c['end'])]
    if spans: return {'category': 'SPANS_SWITCH'}
    before = [c['id'] for c in model['configurations'] if Q(c['end']) <= t]
    after = [c['id'] for c in model['configurations'] if Q(c['start']) >= t]
    if not before or not after: return {'category': 'MISSING_CONFIG'}
    return {'category': 'OK', 'before': before, 'after': after}
