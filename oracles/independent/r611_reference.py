#!/usr/bin/env python3
"""Independent R6-11 reference: direct sum with posterior threshold."""

from fractions import Fraction as Q

C = 'R6-E2-R6-11-PARTIAL'
TEX = 'a4196145c95812ff19376a5985b6a6f2cf469d432c80836071cad1c8ac174c5a'


def posterior(d0, d1, delta=Q(3, 20)):
    keys = set(d0) | set(d1)
    hits = []
    for k in keys:
        p0, p1 = Q(d0.get(k, '0')) / 2, Q(d1.get(k, '0')) / 2
        s = p0 + p1
        if s == 0: continue
        post = max(p0, p1) / s
        hits.append((s, post >= 1 - delta))
    return hits


def bayes(d0, d1):
    keys = set(d0) | set(d1)
    return sum((min(Q(d0.get(k, '0')), Q(d1.get(k, '0'))) for k in keys), Q(0)) / 2


def evaluate(data):
    d0, d1 = data['d0'], data['d1']
    be = bayes(d0, d1)
    hits = posterior(d0, d1)
    cov = sum((s for s, ok in hits if ok), Q(0))
    if data.get('coarsen'):
        c0, c1 = {}, {}
        for k, v in d0.items(): c0[data['coarsen'][k]] = str(Q(c0.get(data['coarsen'][k], '0')) + Q(v))
        for k, v in d1.items(): c1[data['coarsen'][k]] = str(Q(c1.get(data['coarsen'][k], '0')) + Q(v))
        be2 = bayes(c0, c1); cov2 = sum((s for s, ok in posterior(c0, c1) if ok), Q(0))
    else:
        be2, cov2 = be, cov
    return {'category': 'OK', 'bayes_error': str(be), 'coverage': str(cov),
            'coarsened_bayes_error': str(be2), 'coarsened_coverage': str(cov2)}
