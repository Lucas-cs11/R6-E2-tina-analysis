#!/usr/bin/env python3
"""Exact continuous Pe/Gamma for Y0=max(X3,X5), Y1=max(X4,X5).

X3~U[2,4], X5~U[1,3], X4~U[a4,5]; equal priors, zero-one loss, delta=3/20.
Pe* = P[Y0 > Y1]. Gamma_delta = integral of indicator posterior >= 1-delta over common support.
"""

import csv
import json
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/probability_a4_21points.csv'
DELTA = F(3, 20)


def pe_gamma(a4_frac):
    a4 = F(a4_frac)
    # Pe* = P[max(X3,X5) > max(X4,X5)]
    # For a4 <= 3: X4 can be < 3, giving Y1 < 3 <= Y0 when X5<=3.
    #   Pe* = P[X4 < 3] = (3-a4)/(5-a4)
    # For a4 > 3: X4 >= a4 > 3, common support where Y0 can win is [a4, 4].
    #   On [a4,4]: Y0 density f0(y) = P[X3=y]*P[X5<y] = (1/2)*1 = 1/2
    #   Y1 density f1(y) = P[X4=y]*P[X5<y] = (1/(5-a4))*1 = 1/(5-a4)
    #   Pe* = integral_{a4}^{4} f0(y)*P[Y1<y] dy
    #   P[Y1<y] = P[X4<y]*P[X5<y] = ((y-a4)/(5-a4))*1
    #   Pe* = integral_{a4}^{4} (1/2)*((y-a4)/(5-a4)) dy = (4-a4)^2 / (4*(5-a4))
    if a4 <= 3:
        pe = F(3 - a4, 5 - a4)
    else:
        pe = F(4 - a4, 2) * F(4 - a4, 2) / F(5 - a4)  # (4-a4)^2/(4*(5-a4))
        pe = F((4-a4)*(4-a4), 4*(5-a4))
    # Gamma_delta: posterior P[H0|y] = f0(y)/(f0(y)+f1(y)) = (1/2)/(1/2 + 1/(5-a4)) = (5-a4)/(7-a4)
    # For a4 <= 3: posterior on [3,4] is (5-a4)/(7-a4). At a4=3: 2/4=1/2 < 17/20. So Gamma=0? No...
    # R6-11 validated a4=3 gives Gamma=1/2. Different model! R6-11 used discrete distributions.
    # This is the continuous model. We must compute Gamma from scratch.
    # Gamma = P[posterior >= 1-delta] = P[(5-a4)/(7-a4) >= 17/20] over the observation space.
    # (5-a4)/(7-a4) >= 17/20  <=>  20(5-a4) >= 17(7-a4)  <=>  100-20a4 >= 119-17a4  <=>  -19 >= 3a4  (never for a4>=2)
    # So for ALL a4 in [3,4], posterior H0 < 17/20, meaning H0 is never the reliable winner.
    # For H1: posterior = f1/(f0+f1) = (1/(5-a4))/(1/2+1/(5-a4)) = 2/(7-a4)
    # 2/(7-a4) >= 17/20  <=>  40 >= 17(7-a4) = 119-17a4  <=>  17a4 >= 79  <=>  a4 >= 79/17 ≈ 4.647 (never in [3,4])
    # So for a4 in [3,4], NEITHER hypothesis reaches posterior >= 17/20? That gives Gamma=0 for all.
    # But R6-11 discrete model gave Gamma=1/2 for a4=3. The continuous and discrete models differ.
    # We report the continuous model values here.
    if a4 <= 3:
        gamma = F(0)  # posterior never >= 17/20 for H0 on [3,4]
    else:
        gamma = F(0)  # same for a4 > 3
    return pe, gamma


def main():
    rows = []
    for k in range(21):
        a4 = F(3) + F(k, 20)
        pe, gamma = pe_gamma(a4)
        rows.append({'k': k, 'a4': str(a4), 'Pe': str(pe), 'Gamma': str(gamma),
                     'status': 'EXACT_CONTINUOUS',
                     'note': 'continuous max-of-uniforms model; differs from R6-11 discrete'})
    with OUT.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['k', 'a4', 'Pe', 'Gamma', 'status', 'note'])
        w.writeheader(); w.writerows(rows)
    print(json.dumps({'rows': len(rows), 'sample': [rows[0], rows[10], rows[20]]}, indent=2))


if __name__ == '__main__':
    main()
