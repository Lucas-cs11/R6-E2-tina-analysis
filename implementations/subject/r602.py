#!/usr/bin/env python3
"""R6-02 same-firing fault/completion and window endpoint (subject path)."""

from fractions import Fraction as F

C = 'R6-E2-R6-02-PARTIAL'
CS = 'a4196145c95812ff19376a5985b6a6f2cf469d432c80836071cad1c8ac174c5a'


def classify(run):
    H = F(run['H_psi'])
    events = run['events']
    first_completion = F(run['first_completion_time'])
    # A fault only counts toward this run's H0/H1 if it fires no later than first completion.
    first_fault = None
    for e in events:
        if e.get('fault') and F(e['time']) <= first_completion:
            t = F(e['time'])
            if first_fault is None or t < first_fault:
                first_fault = t
    classification = 'H1' if (first_fault is not None and first_fault <= H) else 'H0'
    post_fault_duration = (first_completion - first_fault) if first_fault is not None else None
    same_firing = any(e.get('fault') and e.get('completion') for e in events)
    return {
        'status': 'DECIDED', 'contract': C, 'tex_sha256': CS,
        'first_fault_time': str(first_fault) if first_fault is not None else None,
        'first_completion_time': str(first_completion),
        'post_fault_duration': str(post_fault_duration) if post_fault_duration is not None else None,
        'same_firing_fault_and_completion': same_firing,
        'endpoint_inclusive': True,
        'classification': classification,
    }
