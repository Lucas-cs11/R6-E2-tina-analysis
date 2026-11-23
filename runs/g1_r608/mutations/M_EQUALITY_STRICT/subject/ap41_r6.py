#!/usr/bin/env python3
"""Provisional R6-08 exact AP41 evidence/decision evaluator.

This is a new isolated implementation for the R6-08 boundary contract, not the
lost original solver. It binds the sixth-round contract expectations explicitly
and is not a phase-gate S2 pass.
"""

from fractions import Fraction

CONTRACT = 'AP41-R6-E1-R6-08-PROVISIONAL'
CONTRACT_SHA256 = 'e0f38ecac74cd250e53a7618193089d33063a405f933b750e052b4166eaa9c8b'
TEX_SHA256 = 'a4196145c95812ff19376a5985b6a6f2cf469d432c80836071cad1c8ac174c5a'


class EvidenceError(Exception):
    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


def Q(value, name):
    if isinstance(value, bool) or isinstance(value, float):
        raise EvidenceError(f'{name}: exact rational required')
    try:
        return Fraction(value)
    except Exception as exc:
        raise EvidenceError(f'{name}: invalid rational: {exc}')


def interval(obj, name):
    if not isinstance(obj, dict) or 'low' not in obj or 'high' not in obj:
        raise EvidenceError(f'{name}: interval missing low/high')
    lo, hi = Q(obj['low'], name + '.low'), Q(obj['high'], name + '.high')
    if lo > hi:
        raise EvidenceError(f'{name}: reversed interval')
    return lo, hi


def result(a, v, branch, reasons=(), evidence=(), unresolved=()):
    return {'status': 'DECIDED', 'contract': CONTRACT, 'contract_sha256': CONTRACT_SHA256,
            'tex_sha256': TEX_SHA256, 'a_P': a, 'v_P': v, 'branch': branch,
            'E_P': list(evidence), 'U_P': list(unresolved), 'reasons': list(reasons)}


def decide(data):
    try:
        q0 = interval(data['q0'], 'q0')
        q1 = interval(data['q1'], 'q1')
        vc = str(data['v_c'])
        if vc not in {'0', '1', 'PERP'}:
            raise EvidenceError('v_c must be 0/1/PERP')
        pe = interval(data['Pe'], 'Pe')
        ga = interval(data['Gamma'], 'Gamma')
        pi0, pi1 = Q(data['pi0'], 'pi0'), Q(data['pi1'], 'pi1')
        eps, delta, gamma = (Q(data[k], k) for k in ('epsilon', 'delta', 'gamma'))
        if not (pi0 > 0 and pi1 > 0 and pi0 + pi1 == 1):
            raise EvidenceError('priors must be positive and sum to 1')
        if not (0 < delta < Fraction(1, 2)):
            raise EvidenceError('delta outside 0<delta<1/2')
        if not (0 <= eps <= Fraction(1, 2)):
            raise EvidenceError('epsilon outside safe scope')
        if not (0 <= gamma <= 1):
            raise EvidenceError('gamma outside safe scope')
        # R6-08 complement tightening q0+q1=1.
        if q0[0] + q1[0] > 1 or q0[1] + q1[1] < 1:
            raise EvidenceError('q0+q1=1 jointly infeasible (INVALID_EVIDENCE)')
        t0 = (max(q0[0], 1 - q1[1]), min(q0[1], 1 - q1[0]))
        t1 = (max(q1[0], 1 - q0[1]), min(q1[1], 1 - q0[0]))
        if t0[0] > t0[1] or t1[0] > t1[1]:
            raise EvidenceError('complement tightening empty (INVALID_EVIDENCE)')
        # Optional Q_i^Y(B) <= q_i check.
        for name, q in (('Q0_Y', t0), ('Q1_Y', t1)):
            if name in data:
                qy = interval(data[name], name)
                # Correct joint feasibility: Q_i^Y(B) is an enclosure of a true
                # joint mass that must satisfy 0 <= Q_i^Y(B) <= q_i. A loose upper
                # bound above q_i is a valid conservative enclosure and must be
                # intersected (clamped), not rejected. Contradiction only when the
                # lower bound exceeds the physical upper bound q_i.
                if qy[0] > q[1]:
                    raise EvidenceError(name + ' lower bound exceeds q_i upper bound (infeasible)')
                if qy[0] < 0:
                    raise EvidenceError(name + ' has negative lower bound outside physical domain')
        if pe[0] > min(pi0, pi1):
            raise EvidenceError('Pe lower bound exceeds min(pi)')
        if pe[1] < pe[0]:
            raise EvidenceError('Pe reversed')
        if ga[0] > ga[1]:
            raise EvidenceError('Gamma reversed')
        if t0[1] == 0 or t1[1] == 0:
            return result('0', 'NULL', 'APPLICABILITY_ZERO',
                          evidence=['ZERO_HYPOTHESIS_MASS'])
        if not (t0[0] > 0 and t1[0] > 0):
            return result('PERP', 'NULL', 'APPLICABILITY_UNRESOLVED',
                          unresolved=['POSITIVE_MASS_NOT_PROVEN'])
        # Already proven violation or independent negative bounds.
        if vc == '0':
            return result('1', '0', 'NEGATIVE_EVIDENCE_PRIORITY',
                          evidence=['COMPLETION_VIOLATION_WITNESS'])
        if pe[0] >= eps:
            return result('1', '0', 'NEGATIVE_EVIDENCE_PRIORITY',
                          evidence=['PE_LOWER_STRICTLY_ABOVE_EPSILON'])
        if ga[1] < gamma:
            return result('1', '0', 'NEGATIVE_EVIDENCE_PRIORITY',
                          evidence=['GAMMA_UPPER_STRICTLY_BELOW_THRESHOLD'])
        if vc == '1' and pe[1] <= eps and ga[0] >= gamma:
            return result('1', '1', 'ALL_POSITIVE_CONDITIONS_CERTIFIED',
                          evidence=['COMPLETE_SUPPORT_CHECK', 'PE_UPPER_AT_MOST_EPSILON',
                                    'GAMMA_LOWER_AT_LEAST_THRESHOLD'])
        unresolved = []
        if vc != '1':
            unresolved.append('COMPLETION_SUPPORT_UNRESOLVED')
        if pe[1] > eps:
            unresolved.append('BAYES_RISK_NOT_PROVEN_BELOW_THRESHOLD')
        if ga[0] < gamma:
            unresolved.append('RELIABLE_COVERAGE_NOT_PROVEN_ABOVE_THRESHOLD')
        return result('1', 'PERP', 'PROPERTY_UNRESOLVED', unresolved=unresolved)
    except EvidenceError as exc:
        return {'status': 'INVALID_EVIDENCE', 'contract': CONTRACT,
                'contract_sha256': CONTRACT_SHA256, 'tex_sha256': TEX_SHA256,
                'reason': exc.reason, 'a_P': None, 'v_P': None}
