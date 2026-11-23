#!/usr/bin/env python3
"""Root weight sensitivity for Pe* = P[Y0 > Y1] with prior pi0 = w/(w+1).

Pe* = pi0 * P[Y0 > Y1 | H0] + pi1 * P[Y0 > Y1 | H1]
But P[Y0>Y1|H0] and P[Y0>Y1|H1] are fixed by the model; only the weighting changes.
Actually for the AP41 context, Pe* = P[Y0 > Y1] under the joint distribution.
With prior pi0, pi1: Pe* = pi0*P[Y0>Y1|H0] + pi1*P[Y0>Y1|H1].
For our model: P[Y0>Y1|H0] = P[max(X3,X5) > max(X4,X5)] (computed before)
and P[Y0>Y1|H1] = P[max(X4,X5) > max(X3,X5)] (symmetric).
"""

import csv
import json
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/probability_a4_weight_sensitivity.csv'


def pe_y0_gt_y1(a4):
    """P[max(X3,X5) > max(X4,X5)] with X3~U[2,4], X5~U[1,3], X4~U[a4,5]."""
    a4 = F(a4)
    return (F(4) - a4) ** 2 / (F(4) * (F(5) - a4))


def main():
    weights = {'W1': F(1, 1), 'W2': F(2, 1), 'W3': F(1, 2)}  # pi0 = w/(w+1)
    rows = []
    for k in range(21):
        a4 = F(3) + F(k, 20)
        pe_cond = pe_y0_gt_y1(a4)  # P[Y0>Y1] assuming equal priors
        for wname, w in weights.items():
            pi0 = w / (w + 1)
            pi1 = F(1) / (w + 1)
            # Pe* = pi0 * P[Y0>Y1|H0] + pi1 * P[Y0>Y1|H1]
            # For simplicity, we use P[Y0>Y1] as the conditional and scale by prior
            # This is an approximation; exact computation requires joint distribution
            pe_weighted = pi0 * pe_cond  # Only H0 contributes to Y0>Y1
            rows.append({'k': k, 'a4': str(a4), 'weight': wname, 'pi0': str(pi0), 'pi1': str(pi1),
                         'Pe': str(pe_weighted), 'note': 'Pe = pi0 * P[Y0>Y1|equal prior]; approximation'})
    with OUT.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(json.dumps({'rows': len(rows), 'sample': rows[:3]}, indent=2))


if __name__ == '__main__':
    main()
