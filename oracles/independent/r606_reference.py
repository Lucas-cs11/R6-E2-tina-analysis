#!/usr/bin/env python3
"""Independent R6-06 observation reference with tuple construction."""

from fractions import Fraction as Q

C = 'R6-E2-R6-06-PARTIAL'
TEX = 'a4196145c95812ff19376a5985b6a6f2cf469d432c80836071cad1c8ac174c5a'


def bucket(value, quantum):
    if quantum is None: return str(Q(value))
    scaled = Q(value) / Q(quantum)
    return str(scaled.numerator // scaled.denominator)


def tuple_view(path, psi):
    fields = set(psi['fields']); pieces = []
    if 'word' in fields: pieces.append(('word', tuple(path.get('labels', []))))
    if 'completion_time' in fields: pieces.append(('completion_time', bucket(path['completion_time'], psi.get('quantum'))))
    if 'intermediate_labels' in fields: pieces.append(('intermediate_labels', tuple(path.get('intermediate_labels', []))))
    if 'intermediate_times' in fields: pieces.append(('intermediate_times', tuple(bucket(x, psi.get('quantum')) for x in path.get('intermediate_times', []))))
    if 'external_completion' in fields: pieces.append(('external_completion', path.get('external_completion')))
    return tuple(pieces)


def evaluate(data, psi=None):
    psi = psi or data['psi']
    if not psi.get('prefix_compatible', True):
        return {'status': 'UNSUPPORTED', 'contract': C, 'tex_sha256': TEX, 'verdict': 'PERP', 'witnesses': []}
    views = [(p, tuple_view(p, psi)) for p in data['paths'] if p.get('sample_termination', True)]
    pairs = []
    for p, obs in views:
        if p['fault']: continue
        for other, other_obs in views:
            if other['fault'] and obs == other_obs:
                pairs.append((p['id'], other['id']))
    if pairs:
        verdict = '0'; status = 'DECIDED'
    else:
        verdict = 'PERP'; status = 'UNRESOLVED'
    return {'status': status, 'contract': C, 'tex_sha256': TEX, 'verdict': verdict,
            'witnesses': [{'normal_path': a, 'fault_path': b} for a, b in pairs]}
