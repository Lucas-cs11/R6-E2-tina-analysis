#!/usr/bin/env python3
"""R6-04 independent reference: deadline/endpoint classification via direct comparisons."""

from fractions import Fraction as F

C = 'R6-E2-R6-04-PARTIAL'
CS = 'a4196145c95812ff19376a5985b6a6f2cf469d432c80836071cad1c8ac174c5a'


def classify(run):
    tf, Bc, Ha = F(run['first_fault_time']), F(run['B_c']), F(run['H_A'])
    deadline = tf + Bc
    tc = F(run['completion_time']) if run.get('completion_time') is not None else None
    if tc is not None:
        outcome = 'COMPLETED_IN_TIME' if (tc - tf) <= Bc else 'VIOLATION'
    else:
        outcome = 'PENDING' if Ha < deadline else 'VIOLATION'
    return {'status': 'DECIDED', 'contract': C, 'tex_sha256': CS,
            'post_fault_deadline': str(deadline), 'outcome': outcome,
            'endpoint_exact_pass': (tc is not None and tc == Ha and deadline == Ha),
            'first_fault_time': str(tf), 'B_c': str(Bc), 'H_A': str(Ha),
            'completion_time': str(tc) if tc is not None else None}
