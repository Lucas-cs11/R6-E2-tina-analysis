#!/usr/bin/env python3
"""Independent R6-01 reference: interval-point product enumeration."""

from fractions import Fraction as Q

C = 'R6-E2-R6-01-PARTIAL'
TEX = 'a4196145c95812ff19376a5985b6a6f2cf469d432c80836071cad1c8ac174c5a'


def points(interval, endpoint_grid):
    lo, hi = Q(interval[0]), Q(interval[1])
    if endpoint_grid: return [lo, hi]
    mid = (lo + hi) / 2
    return [lo, mid, hi]


def successors(model, state, urgent):
    loc, t = state
    out = []
    for e in model['edges']:
        if e['from'] != loc or bool(e.get('urgent')) != urgent: continue
        out.append((e['to'], t + Q(e['delay'])))
    return out


def signature(model, state, depth):
    seq = []
    frontier = [state]
    for step in range(depth):
        bucket = []
        new_frontier = []
        for s in frontier:
            u = successors(model, s, True)
            if u:
                bucket.append('u'); new_frontier.extend(u)
            else:
                n = successors(model, s, False)
                bucket.append('d' if n else 'e')
                new_frontier.extend(n)
        seq.append(tuple(bucket))
        frontier = new_frontier
        if not frontier: break
    return tuple(seq)


def distinguish(model):
    states = [(loc, p) for loc, iv in model['locations'].items()
              for p in points(iv, model.get('endpoint_grid', False))]
    sig = {s: signature(model, s, int(model['depth'])) for s in states}
    eq = sorted({(a[0], str(a[1]), b[0], str(b[1])) for a in states for b in states if sig[a] == sig[b] and a[0] == b[0]})
    return {'status': 'ORACLE_COMPUTED', 'contract': C, 'tex_sha256': TEX, 'relation': eq,
            'distinguished_pairs': len(eq), 'undistinguished_pairs': len(eq) == 0,
            'signatures': sorted({str(v) for v in sig.values()})}
