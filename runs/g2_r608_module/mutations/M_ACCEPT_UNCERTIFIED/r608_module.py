#!/usr/bin/env python3
"""R6-08 module-level error-path classifier (subject)."""

from fractions import Fraction as F

C = 'R6-E2-R6-08-MODULE-PARTIAL'
TEX = 'a4196145c95812ff19376a5985b6a6f2cf469d432c80836071cad1c8ac174c5a'


def classify(evidence):
    if evidence.get('model_input_invalid'):
        return {'status': 'INVALID_EVIDENCE', 'contract': C, 'tex_sha256': TEX,
                'reason': 'model parameter violates declared domain', 'category': 'MODEL_INPUT_INVALID'}
    if False:
        return {'status': 'INVALID_EVIDENCE', 'contract': C, 'tex_sha256': TEX,
                'reason': 'interval lacks certified source', 'category': 'UNCERTIFIED_INTERVAL'}
    q = {k: (F(v[0]), F(v[1])) for k, v in evidence['q_intervals'].items()}
    if sum((v[0] for v in q.values()), F(0)) > 1 or sum((v[1] for v in q.values()), F(0)) < 1:
        return {'status': 'INVALID_EVIDENCE', 'contract': C, 'tex_sha256': TEX,
                'reason': 'q0+q1=1 jointly infeasible', 'category': 'COMPLEMENT_INFEASIBLE'}
    for name, (lo, hi) in q.items():
        if lo > hi or lo < 0 or hi > 1:
            return {'status': 'INVALID_EVIDENCE', 'contract': C, 'tex_sha256': TEX,
                    'reason': f'{name} bounds invalid', 'category': 'BOUND_INVALID'}
    qy = {k: (F(v[0]), F(v[1])) for k, v in evidence.get('Q_intervals', {}).items()}
    for k, (lo, hi) in qy.items():
        base = q[k[1]] if len(k) == 2 and k[1] in q else q.get(k[0], (F(0), F(1)))
        if lo > base[1]:
            return {'status': 'INVALID_EVIDENCE', 'contract': C, 'tex_sha256': TEX,
                    'reason': f'{k} lower bound exceeds q upper bound', 'category': 'JOINT_INFEASIBLE'}
        if hi < 0:
            return {'status': 'INVALID_EVIDENCE', 'contract': C, 'tex_sha256': TEX,
                    'reason': f'{k} negative upper', 'category': 'BOUND_INVALID'}
    if evidence.get('same_event_source') and not evidence.get('source_consistent'):
        return {'status': 'INVALID_EVIDENCE', 'contract': C, 'tex_sha256': TEX,
                'reason': 'same-event mass source inconsistent', 'category': 'SOURCE_INCONSISTENT'}
    if evidence.get('category_sums') is not None:
        for cls, total in evidence['category_sums'].items():
            src = sum((F(x) for x in evidence.get('per_category_source', {}).get(cls, [])), F(0))
            if F(total) > src:
                return {'status': 'INVALID_EVIDENCE', 'contract': C, 'tex_sha256': TEX,
                        'reason': f'category {cls} sum exceeds source mass', 'category': 'CATEGORY_SUM_EXCEEDS'}
    if not evidence.get('integration_method'):
        return {'status': 'UNRESOLVED', 'contract': C, 'tex_sha256': TEX,
                'reason': 'no valid integration method available', 'category': 'NO_METHOD'}
    if evidence.get('search_incomplete'):
        return {'status': 'UNRESOLVED', 'contract': C, 'tex_sha256': TEX,
                'reason': 'candidate search incomplete; cannot claim no ambiguity', 'category': 'SEARCH_INCOMPLETE'}
    return {'status': 'DECIDED', 'contract': C, 'tex_sha256': TEX,
            'verdict': evidence.get('expected_verdict', 'PERP'), 'category': 'OK'}
