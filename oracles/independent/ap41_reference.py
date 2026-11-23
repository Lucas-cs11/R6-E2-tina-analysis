#!/usr/bin/env python3
"""Independent R6-08 exact reference; does not import the subject module."""

from fractions import Fraction

C = 'AP41-R6-E1-R6-08-PROVISIONAL'
CS = 'e0f38ecac74cd250e53a7618193089d33063a405f933b750e052b4166eaa9c8b'
T = 'a4196145c95812ff19376a5985b6a6f2cf469d432c80836071cad1c8ac174c5a'


class Bad(Exception):
    pass


def rat(x, name):
    if isinstance(x, bool) or isinstance(x, float):
        raise Bad(name + ' not exact')
    try:
        return Fraction(x)
    except Exception:
        raise Bad(name + ' not rational')


def bd(x, name):
    try:
        a, b = rat(x['low'], name + '.lo'), rat(x['high'], name + '.hi')
    except Exception:
        raise Bad(name + ' bad interval')
    if a > b:
        raise Bad(name + ' reversed')
    return a, b


def decide(x):
    try:
        a0, b0 = bd(x['q0'], 'q0')
        a1, b1 = bd(x['q1'], 'q1')
        p0, p1 = rat(x['pi0'], 'pi0'), rat(x['pi1'], 'pi1')
        e = rat(x['epsilon'], 'epsilon')
        d = rat(x['delta'], 'delta')
        g = rat(x['gamma'], 'gamma')
        pe = bd(x['Pe'], 'Pe')
        ga = bd(x['Gamma'], 'Gamma')
        vc = str(x['v_c'])
        if not (p0 > 0 and p1 > 0 and p0 + p1 == 1) or not (0 < d < Fraction(1, 2)) or not (0 <= e <= Fraction(1, 2)) or not (0 <= g <= 1) or vc not in {'0', '1', 'PERP'}:
            raise Bad('basic domain')
        # Feasible complementary pair: lower sums <=1 and upper sums >=1.
        if a0 + a1 > 1 or b0 + b1 < 1:
            raise Bad('complement infeasible')
        lo0 = max(a0, 1 - b1); hi0 = min(b0, 1 - a1)
        lo1 = max(a1, 1 - b0); hi1 = min(b1, 1 - a0)
        if lo0 > hi0 or lo1 > hi1:
            raise Bad('empty complement')
        for qy_name, q_hi in (('Q0_Y', hi0), ('Q1_Y', hi1)):
            if qy_name in x:
                qy = bd(x[qy_name], qy_name)
                # Independent linear feasibility: exists t with
                #   qy.low <= t <= qy.high AND 0 <= t <= q_hi
                feasible = (qy[0] <= q_hi) and (qy[1] >= 0)
                if not feasible:
                    raise Bad(qy_name + ' infeasible under 0<=Q_i^Y<=q_i')
                if qy[0] < 0:
                    raise Bad(qy_name + ' negative lower bound')
        if pe[0] > min(p0, p1):
            raise Bad('Pe lower > min pi')
        if pe[1] < pe[0] or ga[0] > ga[1]:
            raise Bad('reversed Pe/Gamma')
        if hi0 == 0 or hi1 == 0:
            return {'status': 'DECIDED', 'contract': C, 'contract_sha256': CS, 'tex_sha256': T,
                    'a_P': '0', 'v_P': 'NULL', 'branch': 'APPLICABILITY_ZERO'}
        if lo0 == 0 or lo1 == 0:
            return {'status': 'DECIDED', 'contract': C, 'contract_sha256': CS, 'tex_sha256': T,
                    'a_P': 'PERP', 'v_P': 'NULL', 'branch': 'APPLICABILITY_UNRESOLVED'}
        if vc == '0' or pe[0] > e or ga[1] < g:
            return {'status': 'DECIDED', 'contract': C, 'contract_sha256': CS, 'tex_sha256': T,
                    'a_P': '1', 'v_P': '0', 'branch': 'NEGATIVE_EVIDENCE_PRIORITY'}
        if vc == '1' and pe[1] <= e and ga[0] >= g:
            return {'status': 'DECIDED', 'contract': C, 'contract_sha256': CS, 'tex_sha256': T,
                    'a_P': '1', 'v_P': '1', 'branch': 'ALL_POSITIVE_CONDITIONS_CERTIFIED'}
        return {'status': 'DECIDED', 'contract': C, 'contract_sha256': CS, 'tex_sha256': T,
                'a_P': '1', 'v_P': 'PERP', 'branch': 'PROPERTY_UNRESOLVED'}
    except Bad as exc:
        return {'status': 'INVALID_EVIDENCE', 'contract': C, 'contract_sha256': CS,
                'tex_sha256': T, 'reason': str(exc), 'a_P': None, 'v_P': None}
