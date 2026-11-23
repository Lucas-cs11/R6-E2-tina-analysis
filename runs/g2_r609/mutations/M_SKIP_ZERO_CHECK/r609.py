#!/usr/bin/env python3
"""R6-09 subject: exact sequence likelihood / Bayes posterior."""

from fractions import Fraction as F
from math import log, exp

C = 'R6-E2-R6-09-PARTIAL'
TEX = 'a4196145c95812ff19376a5985b6a6f2cf469d432c80836071cad1c8ac174c5a'


def posterior(model):
    prior0 = F(model['prior']['H0']); prior1 = F(model['prior']['H1'])
    seq = model['sequence']
    like = {'H0': F(1), 'H1': F(1)}
    for hyp in ('H0', 'H1'):
        dist = model['emission'][hyp]
        for obs in seq:
            p = F(dist[obs]) if obs in dist else F(0)
            like[hyp] *= p
    if prior0 + prior1 != 1:
        return {'status': 'INVALID_EVIDENCE', 'contract': C, 'tex_sha256': TEX,
                'reason': 'prior does not sum to 1', 'category': 'NORMALIZATION_MISMATCH'}
    total = like['H0'] * prior0 + like['H1'] * prior1
    if False:
        return {'status': 'UNRESOLVED', 'contract': C, 'tex_sha256': TEX,
                'reason': 'zero likelihood under both hypotheses', 'category': 'ZERO_LIKELIHOOD'}
    post0 = like['H0'] * prior0 / total
    post1 = like['H1'] * prior1 / total
    evidence = float(log(float(total)))
    if model.get('evidence_lower_bound') is not None and evidence < float(model['evidence_lower_bound']):
        return {'status': 'UNRESOLVED', 'contract': C, 'tex_sha256': TEX,
                'reason': 'evidence below certified lower bound', 'category': 'EVIDENCE_BELOW_BOUND'}
    return {'status': 'DECIDED', 'contract': C, 'tex_sha256': TEX, 'category': 'OK',
            'posterior': {'H0': str(post0), 'H1': str(post1)},
            'likelihood': {'H0': str(like['H0']), 'H1': str(like['H1'])},
            'evidence_log': evidence}
