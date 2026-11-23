#!/usr/bin/env python3
"""R6-13 subject: sensor delay / observation timestamp shift."""

from fractions import Fraction as F

C = 'R6-E2-R6-13-PARTIAL'
TEX = 'a4196145c95812ff19376a5985b6a6f2cf469d432c80836071cad1c8ac174c5a'


def classify(model):
    delay = F(model['delay'])
    window = (F(model['window'][0]), F(model['window'][1]))
    true_events = sorted((F(e['time']) for e in model['true_events']))
    observed = sorted((F(e['time']) for e in model['observed_events']))
    if len(true_events) != len(observed):
        return {'status': 'UNRESOLVED', 'contract': C, 'tex_sha256': TEX,
                'reason': 'event count mismatch under delay', 'category': 'COUNT_MISMATCH'}
    shifted = [t + delay for t in true_events]
    if shifted != observed:
        return {'status': 'INVALID_EVIDENCE', 'contract': C, 'tex_sha256': TEX,
                'reason': 'observed times do not match true times + delay', 'category': 'DELAY_MISMATCH'}
    in_window = [t for t in observed if window[0] <= t <= window[1]]
    return {'status': 'DECIDED', 'contract': C, 'tex_sha256': TEX, 'category': 'OK',
            'observed_in_window': len(in_window), 'observed_total': len(observed),
            'delay': str(delay)}
