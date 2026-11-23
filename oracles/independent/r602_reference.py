#!/usr/bin/env python3
"""R6-02 independent reference: enumerate events and compare times differently."""

from fractions import Fraction as F

C = 'R6-E2-R6-02-PARTIAL'
CS = 'a4196145c95812ff19376a5985b6a6f2cf469d432c80836071cad1c8ac174c5a'


def classify(run):
    H = F(run['H_psi'])
    completion = F(run['first_completion_time'])
    # independent path: collect only pre-completion fault firings
    fault_times = [F(e['time']) for e in run['events'] if e.get('fault') and F(e['time']) <= completion]
    first_fault = min(fault_times) if fault_times else None
    # independent endpoint handling: H1 iff exists fault time t with t <= H
    classification = 'H1' if (first_fault is not None and first_fault <= H) else 'H0'
    return {
        'status': 'DECIDED', 'contract': C, 'tex_sha256': CS,
        'first_fault_time': str(first_fault) if first_fault is not None else None,
        'first_completion_time': str(completion),
        'post_fault_duration': str(completion - first_fault) if first_fault is not None else None,
        'same_firing_fault_and_completion': any(e.get('fault') and e.get('completion') for e in run['events']),
        'endpoint_inclusive': True, 'classification': classification,
    }
