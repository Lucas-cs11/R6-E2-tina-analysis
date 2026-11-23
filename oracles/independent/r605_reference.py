#!/usr/bin/env python3
"""Independent R6-05 reference: exact 2-D boundary-intersection enumeration."""

from fractions import Fraction as Q
from itertools import combinations

C = 'R6-E2-R6-05-PARTIAL'
TEX = 'a4196145c95812ff19376a5985b6a6f2cf469d432c80836071cad1c8ac174c5a'


def lines(model, region):
    bounds = {k: (Q(v[0]), Q(v[1])) for k, v in model['bounds'].items()}
    var = model['fault_variable']; bc = Q(model['B_c'])
    if region == 'compliant': bounds[var] = (bounds[var][0], min(bounds[var][1], bc))
    else: bounds[var] = (max(bounds[var][0], bc), bounds[var][1])
    variables = sorted(bounds)
    if len(variables) != 2: raise ValueError('independent reference supports exactly two variables')
    out = []
    for k, (lo, hi) in bounds.items():
        out += [({k: Q(1)}, hi), ({k: Q(-1)}, -lo)]
    for x in model.get('constraints', []):
        out.append(({k: Q(v) for k, v in x['coefficients'].items()}, Q(x['upper'])))
    return variables, out


def vertices(model, region):
    variables, boundary = lines(model, region)
    candidates = []
    for (a, b), (c, d) in combinations(boundary, 2):
        det = a.get(variables[0], Q(0)) * c.get(variables[1], Q(0)) - a.get(variables[1], Q(0)) * c.get(variables[0], Q(0))
        if det == 0: continue
        x = (b * c.get(variables[1], Q(0)) - a.get(variables[1], Q(0)) * d) / det
        y = (a.get(variables[0], Q(0)) * d - b * c.get(variables[0], Q(0))) / det
        point = {variables[0]: x, variables[1]: y}
        if all(sum((v * point[k] for k, v in coeff.items()), Q(0)) <= upper for coeff, upper in boundary):
            if point not in candidates: candidates.append(point)
    return candidates


def split(model):
    compliant_points = vertices(model, 'compliant')
    violating_points = vertices(model, 'violating')
    var = model['fault_variable']; bc = Q(model['B_c'])
    violating_points = [p for p in violating_points if p[var] > bc]
    compliant_witnesses = []
    violating_witnesses = []
    _, compliant_boundary = lines(model, 'compliant')
    _, violating_boundary = lines(model, 'violating')
    for w in model.get('witnesses', []):
        if all(sum((v * Q(w[k]) for k, v in coeff.items()), Q(0)) <= upper for coeff, upper in compliant_boundary):
            compliant_witnesses.append(w)
        if all(sum((v * Q(w[k]) for k, v in coeff.items()), Q(0)) <= upper for coeff, upper in violating_boundary) and Q(w[var]) > bc:
            violating_witnesses.append(w)
    return {'status': 'DECIDED', 'contract': C, 'tex_sha256': TEX,
            'compliant': {'feasible': bool(compliant_points), 'strict_upper': False,
                          'witnesses': compliant_witnesses,
                          'completion_witness_preserved': any(w.get('first_completion') for w in compliant_witnesses)},
            'violating': {'feasible': bool(violating_points), 'strict_lower': True, 'witnesses': violating_witnesses},
            'B_c': str(bc), 'fault_variable': var}
