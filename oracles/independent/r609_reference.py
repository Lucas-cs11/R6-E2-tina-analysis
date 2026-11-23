#!/usr/bin/env python3
"""Independent R6-09 reference: log-domain summation."""

from fractions import Fraction as Q
from math import log, exp

C = 'R6-E2-R6-09-PARTIAL'
TEX = 'a4196145c95812ff19376a5985b6a6f2cf469d432c80836071cad1c8ac174c5a'


def posterior(model):
    seq = model['sequence']; prior = {k: Q(v) for k, v in model['prior'].items()}
    log_like = {}
    for hyp in ('H0', 'H1'):
        ll = 0.0
        dist = model['emission'][hyp]
        for obs in seq:
            p = Q(dist.get(obs, '0'))
            if p == 0: ll = float('-inf'); break
            ll += log(float(p))
        log_like[hyp] = ll
    if log_like['H0'] == float('-inf') and log_like['H1'] == float('-inf'):
        return {'category': 'ZERO_LIKELIHOOD'}
    if sum(prior.values()) != 1:
        return {'category': 'NORMALIZATION_MISMATCH'}
    m = max(log_like.values())
    if m == float('-inf'):
        return {'category': 'ZERO_LIKELIHOOD'}
    w = {k: exp(log_like[k] - m) * float(prior[k]) for k in log_like}
    z = sum(w.values())
    post = {k: w[k] / z for k in w}
    evidence = m + log(z)
    if model.get('evidence_lower_bound') is not None and evidence < float(model['evidence_lower_bound']):
        return {'category': 'EVIDENCE_BELOW_BOUND'}
    return {'category': 'OK', 'posterior': {k: str(Q(str(v)).limit_denominator(10**9)) for k, v in post.items()},
            'evidence_log': evidence}
