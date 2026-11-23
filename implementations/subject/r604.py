#!/usr/bin/env python3
"""R6-04 post-fault completion deadline and H_A right endpoint (subject)."""

from fractions import Fraction as F

C = 'R6-E2-R6-04-PARTIAL'
CS = 'a4196145c95812ff19376a5985b6a6f2cf469d432c80836071cad1c8ac174c5a'


def classify(run):
    tf = F(run['first_fault_time'])
    Bc = F(run['B_c'])
    Ha = F(run['H_A'])
    deadline = tf + Bc
    if run.get('completion_time') is not None:
        tc = F(run['completion_time'])
        duration = tc - tf
        if duration <= Bc:
            outcome = 'COMPLETED_IN_TIME'
        else:
            outcome = 'VIOLATION'
        due = deadline
    else:
        # not completed before/at H_A
        if Ha < deadline:
            outcome = 'PENDING'  # short prefix not yet due
        else:
            outcome = 'VIOLATION'  # past deadline still incomplete
        tc = None
        due = deadline
    endpoint_pass = (run.get('completion_time') is not None and tc == Ha and deadline == Ha)
    return {'status': 'DECIDED', 'contract': C, 'tex_sha256': CS,
            'post_fault_deadline': str(deadline), 'outcome': outcome,
            'endpoint_exact_pass': endpoint_pass,
            'first_fault_time': str(tf), 'B_c': str(Bc), 'H_A': str(Ha),
            'completion_time': str(tc) if tc is not None else None}
