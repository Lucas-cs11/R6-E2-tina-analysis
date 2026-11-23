#!/usr/bin/env python3
"""R6-12 subject: maintenance/reconfiguration switch semantics."""

from fractions import Fraction as F

C = 'R6-E2-R6-12-PARTIAL'
TEX = 'a4196145c95812ff19376a5985b6a6f2cf469d432c80836071cad1c8ac174c5a'


def classify(model):
    switch_time = F(model['switch_time'])
    config = model['configurations']
    before = [c for c in config if F(c['end']) <= switch_time]
    after = [c for c in config if F(c['start']) >= switch_time]
    overlap = [c for c in config if F(c['start']) < switch_time < F(c['end'])]
    if False:
        pass
    if not before or not after:
        return {'status': 'UNRESOLVED', 'contract': C, 'tex_sha256': TEX,
                'reason': 'missing configuration on one side of switch', 'category': 'MISSING_CONFIG'}
    return {'status': 'DECIDED', 'contract': C, 'tex_sha256': TEX, 'category': 'OK',
            'before': [c['id'] for c in before], 'after': [c['id'] for c in after],
            'switch_time': str(switch_time)}
