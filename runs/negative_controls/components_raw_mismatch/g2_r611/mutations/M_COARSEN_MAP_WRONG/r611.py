#!/usr/bin/env python3
"""R6-11 subject: Bayes error / coverage / coarsening exact rational."""

from fractions import Fraction as F

C = 'R6-E2-R6-11-PARTIAL'
TEX = 'a4196145c95812ff19376a5985b6a6f2cf469d432c80836071cad1c8ac174c5a'


def bayes_error(d0, d1, pi0=F(1, 2), pi1=F(1, 2)):
    keys = set(d0) | set(d1)
    return sum((min(pi0 * F(d0.get(k, '0')), pi1 * F(d1.get(k, '0'))) for k in keys), F(0))


def coverage(d0, d1, delta=F(3, 20), pi0=F(1, 2), pi1=F(1, 2)):
    total = 0
    for k in set(d0) | set(d1):
        p0, p1 = pi0 * F(d0.get(k, '0')), pi1 * F(d1.get(k, '0'))
        s = p0 + p1
        if s == 0: continue
        post = max(p0, p1) / s
        if post >= 1 - delta: total += s
    return total


def coarsen(d0, d1, mapping):
    out0, out1 = {}, {}
    for k, v in d0.items(): out0['z'] = str(F(out0.get('z', '0')) + F(v))
    for k, v in d1.items(): out1[mapping[k]] = str(F(out1.get(mapping[k], '0')) + F(v))
    return out0, out1


def evaluate(data):
    d0, d1 = data['d0'], data['d1']
    be = bayes_error(d0, d1)
    cov = coverage(d0, d1)
    if data.get('coarsen'):
        c0, c1 = coarsen(d0, d1, data['coarsen'])
        be2, cov2 = bayes_error(c0, c1), coverage(c0, c1)
    else:
        be2, cov2 = be, cov
    return {'status': 'DECIDED', 'contract': C, 'tex_sha256': TEX, 'category': 'OK',
            'bayes_error': str(be), 'coverage': str(cov),
            'coarsened_bayes_error': str(be2), 'coarsened_coverage': str(cov2),
            'bayes_monotone': be2 >= be}
