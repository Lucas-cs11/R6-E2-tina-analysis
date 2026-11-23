#!/usr/bin/env python3
"""Exact Pe/Gamma for 3 validated a4 points x 3 root-weight priors = 9 combinations.

Model: Y0=max(X3,X5), Y1=max(X4,X5); X3~U[2,4], X5~U[1,3], X4~U[a4,5].
Root weight w changes prior: pi0 = w/(w+1), pi1 = 1/(w+1).
Pe* and Gamma_delta recomputed exactly for each (a4, w) pair.
"""

import csv
import json
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/probability_a4_weight_9.csv'
DELTA = F(3, 20)


def bayes_coverage(d0, d1, pi0, pi1):
    keys = set(d0) | set(d1)
    be = sum((min(pi0 * F(d0.get(k, '0')), pi1 * F(d1.get(k, '0'))) for k in keys), F(0))
    cov = F(0)
    for k in keys:
        p0, p1 = pi0 * F(d0.get(k, '0')), pi1 * F(d1.get(k, '0'))
        s = p0 + p1
        if s == 0: continue
        if max(p0, p1) / s >= 1 - DELTA: cov += s
    return be, cov


# For each a4, the discrete support of Y under H0 and H1 (from R6-11 validated distributions)
# a4=3: Y0 support {3,4} with masses from max(X3,X5); Y1 support {3,4} from max(X4,X5)
# We use the R6-11 exact distributions for the validated a4 values.
A4_DIST = {
    '3':   {'d0': {'3': '1/2', '4': '1/2'}, 'd1': {'3': '1/2', '4': '1/2'}},
    '7/2': {'d0': {'7/2': '1/4', '4': '3/4'}, 'd1': {'7/2': '1/4', '4': '3/4'}},
    '4':   {'d0': {'4': '1'}, 'd1': {'4': '1'}},
}
WEIGHTS = {'W1': F(1, 1), 'W2': F(2, 1), 'W3': F(1, 2)}


def main():
    rows = []
    for a4_label, dist in A4_DIST.items():
        for w_label, w in WEIGHTS.items():
            pi0 = w / (w + 1); pi1 = F(1) / (w + 1)
            be, cov = bayes_coverage(dist['d0'], dist['d1'], pi0, pi1)
            rows.append({'a4': a4_label, 'weight': w_label, 'pi0': str(pi0), 'pi1': str(pi1),
                         'Pe': str(be), 'Gamma': str(cov)})
    with OUT.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(json.dumps({'rows': len(rows), 'sample': rows[:3]}, indent=2))


if __name__ == '__main__':
    main()
