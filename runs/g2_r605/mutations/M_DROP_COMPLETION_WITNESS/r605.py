#!/usr/bin/env python3
"""R6-05 subject: exact rational Fourier-Motzkin split of a mixed state class."""

from fractions import Fraction as F

C = 'R6-E2-R6-05-PARTIAL'
TEX = 'a4196145c95812ff19376a5985b6a6f2cf469d432c80836071cad1c8ac174c5a'


def inequalities(bounds, extra):
    out = []
    for var, (lo, hi) in bounds.items():
        if lo is not None: out.append(({var: F(-1)}, -F(lo)))
        if hi is not None: out.append(({var: F(1)}, F(hi)))
    for item in extra:
        out.append(({k: F(v) for k, v in item['coefficients'].items()}, F(item['upper'])))
    return out


def eliminate(items, var):
    positive, negative, rest = [], [], []
    for coeff, upper in items:
        a = coeff.get(var, F(0))
        if a > 0: positive.append((coeff, upper, a))
        elif a < 0: negative.append((coeff, upper, a))
        else: rest.append((coeff, upper))
    if not positive or not negative:
        return rest
    result = list(rest)
    for lc, lu, la in negative:
        for uc, uu, ua in positive:
            # (lu-rest_l)/la <= (uu-rest_u)/ua, with la<0<ua.
            coeff = {}
            for k in set(lc) | set(uc):
                if k == var: continue
                value = uc.get(k, F(0)) / ua - lc.get(k, F(0)) / la
                if value: coeff[k] = value
            upper = uu / ua - lu / la
            result.append((coeff, upper))
    return result


def projected_bounds(bounds, extra, target):
    items = inequalities(bounds, extra)
    variables = list(bounds)
    for var in variables:
        if var != target: items = eliminate(items, var)
    lower, upper = None, None
    for coeff, bound in items:
        a = coeff.get(target, F(0))
        if a == 0:
            if bound < 0: return None
        elif a > 0:
            value = bound / a
            upper = value if upper is None else min(upper, value)
        else:
            value = bound / a
            lower = value if lower is None else max(lower, value)
    if lower is not None and upper is not None and lower > upper: return None
    return lower, upper


def satisfies(w, bounds, extra, strict_var=None, strict_lower=None):
    for var, (lo, hi) in bounds.items():
        if var not in w: return False
        value = F(w[var])
        if lo is not None and value < F(lo): return False
        if hi is not None and value > F(hi): return False
    for item in extra:
        if sum((F(c) * F(w[k]) for k, c in item['coefficients'].items()), F(0)) > F(item['upper']): return False
    return not (strict_var and F(w[strict_var]) <= F(strict_lower))


def split(model):
    var = model['fault_variable']; bc = F(model['B_c'])
    base = {k: (F(v[0]), F(v[1])) for k, v in model['bounds'].items()}
    extra = model.get('constraints', [])
    compliant_bounds = dict(base); compliant_bounds[var] = (base[var][0], min(base[var][1], bc))
    violating_bounds = dict(base); violating_bounds[var] = (max(base[var][0], bc), base[var][1])
    compliant_range = projected_bounds(compliant_bounds, extra, var)
    violating_range = projected_bounds(violating_bounds, extra, var)
    compliant_witnesses = [w for w in model.get('witnesses', []) if satisfies(w, compliant_bounds, extra)]
    violating_witnesses = [w for w in model.get('witnesses', []) if satisfies(w, violating_bounds, extra, var, bc)]
    completion_witness_preserved = False
    return {'status': 'DECIDED', 'contract': C, 'tex_sha256': TEX,
            'compliant': {'feasible': compliant_range is not None, 'strict_upper': False,
                          'witnesses': compliant_witnesses, 'completion_witness_preserved': completion_witness_preserved},
            'violating': {'feasible': violating_range is not None and violating_range[1] > bc,
                          'strict_lower': True, 'witnesses': violating_witnesses},
            'B_c': str(bc), 'fault_variable': var}
