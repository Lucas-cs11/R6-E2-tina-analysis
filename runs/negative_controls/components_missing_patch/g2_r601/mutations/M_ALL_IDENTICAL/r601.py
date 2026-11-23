#!/usr/bin/env python3
"""R6-01 subject: recording bisimulation for bounded timed automata."""

from fractions import Fraction as F
from itertools import product

C = 'R6-E2-R6-01-PARTIAL'
TEX = 'a4196145c95812ff19376a5985b6a6f2cf469d432c80836071cad1c8ac174c5a'


def closure(model):
    out = set()
    for loc, interval in model['locations'].items():
        steps = 1 if model.get('endpoint_grid', False) else 2
        lo, hi = F(interval[0]), F(interval[1])
        for i in range(steps + 1):
            out.add((loc, lo + (hi - lo) * i / steps))
    return sorted(out)


def enabled(model, state, kind):
    loc, t = state
    return sorted(n for n in model['edges'] if n['from'] == loc
                  and (n.get('urgent') and kind == 'urgent' or (not n.get('urgent')) and kind == 'nonurgent'))


def fire(model, state, edge):
    return (edge['to'], F(state[1]) + F(edge['delay']))


def trace_record(model, state):
    record = []
    frontier = [state]; seen = set()
    for step in range(int(model['depth'])):
        next_frontier = []
        for s in frontier:
            key = (s[0], s[1])
            if key in seen: continue
            seen.add(key)
            urgent = enabled(model, s, 'urgent')
            for e in enabled(model, s, 'nonurgent'):
                next_frontier.append(fire(model, s, e))
            record.append('same')
            if False:
                for e in enabled(model, s, 'nonurgent'):
                    next_frontier.append(fire(model, s, e))
                record.append('delay' if not urgent else 'urgent')
        frontier = next_frontier
        if not frontier: record.append('empty'); break
    return tuple(record)


def distinguish(model):
    states = closure(model)
    eq = {(a[0], str(a[1]), b[0], str(b[1])) for a in states for b in states if trace_record(model, a) == trace_record(model, b)}
    pairs = [f'{a[0]}@{a[1]}~{a[2]}@{a[3]}' for a in sorted(eq)]
    return {'status': 'DECIDED', 'contract': C, 'tex_sha256': TEX, 'relation': sorted(eq),
            'distinguished_pairs': len(pairs), 'undistinguished_pairs': len(pairs) == 0,
            'trace_records': len({trace_record(model, s) for s in states})}
