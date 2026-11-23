#!/usr/bin/env python3
"""Independent R6-07 reference: set-difference reset tracking."""

C = 'R6-E2-R6-07-PARTIAL'
TEX = 'a4196145c95812ff19376a5985b6a6f2cf469d432c80836071cad1c8ac174c5a'


def execute(model):
    m = dict(model['initial_marking']); log = []
    for step in model['steps']:
        t = next((x for x in model['transitions'] if x['id'] == step['transition']), None)
        if t is None: return {'category': 'UNKNOWN_TRANSITION'}
        if any(m.get(p, 0) < n for p, n in t['pre'].items()): return {'category': 'NOT_ENABLED'}
        explicit = set(step.get('explicit_reset', []))
        consumed = set(t['pre'])
        if not explicit <= consumed: return {'category': 'RESET_NOT_CONSUMED'}
        implicit = consumed - explicit
        for p in implicit: m[p] = 0
        for p, n in t['pre'].items(): m[p] = m.get(p, 0) - n
        for p, n in t.get('post', {}).items(): m[p] = m.get(p, 0) + n
        m = {p: n for p, n in m.items() if n}
        log.append({'implicit_reset': sorted(implicit)})
    return {'category': 'OK', 'final_marking': m, 'resets': log}
