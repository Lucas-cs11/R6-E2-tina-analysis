#!/usr/bin/env python3
"""R6-07 subject: implicit vs explicit place reset semantics."""

from fractions import Fraction as F

C = 'R6-E2-R6-07-PARTIAL'
TEX = 'a4196145c95812ff19376a5985b6a6f2cf469d432c80836071cad1c8ac174c5a'


def execute(model):
    marking = dict(model['initial_marking'])
    resets = []
    for step in model['steps']:
        tid = step['transition']
        t = next((x for x in model['transitions'] if x['id'] == tid), None)
        if t is None: return {'status': 'INVALID_EVIDENCE', 'contract': C, 'tex_sha256': TEX, 'category': 'UNKNOWN_TRANSITION'}
        if not all(marking.get(p, 0) >= n for p, n in t['pre'].items()):
            return {'status': 'INVALID_EVIDENCE', 'contract': C, 'tex_sha256': TEX, 'category': 'NOT_ENABLED'}
        explicit = set(step.get('explicit_reset', []))
        consumed = set(t['pre'].keys())
        implicit = consumed - explicit
        for p in explicit:
            if p not in consumed: return {'status': 'INVALID_EVIDENCE', 'contract': C, 'tex_sha256': TEX, 'category': 'RESET_NOT_CONSUMED'}
        for p in consumed:
            marking[p] = 0
        for p, n in t['pre'].items(): marking[p] = marking.get(p, 0) - n
        for p, n in t.get('post', {}).items(): marking[p] = marking.get(p, 0) + n
        marking = {p: n for p, n in marking.items() if n}
        resets.append({'transition': tid, 'implicit_reset': sorted(implicit), 'explicit_reset': sorted(explicit)})
    return {'status': 'DECIDED', 'contract': C, 'tex_sha256': TEX, 'category': 'OK',
            'final_marking': marking, 'resets': resets}
