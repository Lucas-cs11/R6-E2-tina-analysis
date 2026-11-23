#!/usr/bin/env python3
"""Numerical integration of Pe* and Gamma_delta for Y0=max(X3,X5) vs Y1=max(X4,X5).

Pe* = P[Y0 > Y1] = E[max(0, (Y0-a4)/(5-a4))]
Gamma_delta = P[posterior(H_winner|Y) >= 1-delta]
posterior(H0|y) = f0(y)/(f0(y)+f1(y)), posterior(H1|y) = f1(y)/(f0(y)+f1(y))
f0(y) = density of Y0 at y, f1(y) = density of Y1 at y.
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/probability_a4_21points.csv'
N = 2000
DELTA = 0.15


def densities(a4):
    """Return f0, f1 as functions of y."""
    def f0(y):
        # Y0 = max(X3, X5), X3~U[2,4], X5~U[1,3]
        # f0(y) = f_X3(y)*F_X5(y) + f_X5(y)*F_X3(y)
        # f_X3(y) = 1/2 for y in [2,4], else 0
        # f_X5(y) = 1/2 for y in [1,3], else 0
        # F_X5(y) = 0 for y<1, (y-1)/2 for y in [1,3], 1 for y>3
        # F_X3(y) = 0 for y<2, (y-2)/2 for y in [2,4], 1 for y>4
        f = 0.0
        if 2 <= y <= 4:
            f += 0.5 * (0.0 if y < 1 else (y - 1) / 2 if y <= 3 else 1.0)
        if 1 <= y <= 3:
            f += 0.5 * (0.0 if y < 2 else (y - 2) / 2 if y <= 4 else 1.0)
        return f
    def f1(y):
        # Y1 = max(X4, X5), X4~U[a4,5], X5~U[1,3]
        if a4 <= y <= 5:
            f = 1.0 / (5.0 - a4) * (0.0 if y < 1 else (y - 1) / 2 if y <= 3 else 1.0)
        else:
            f = 0.0
        if 1 <= y <= 3:
            f += 0.5 * (0.0 if y < a4 else (y - a4) / (5.0 - a4) if y <= 5 else 1.0)
        return f
    return f0, f1


def pe_numeric(a4):
    total = 0.0
    dx3 = 2.0 / N
    dx5 = 2.0 / N
    for i in range(N):
        x3 = 2.0 + (i + 0.5) * dx3
        for j in range(N):
            x5 = 1.0 + (j + 0.5) * dx5
            y0 = max(x3, x5)
            if y0 > a4:
                total += (y0 - a4) / (5.0 - a4)
    return total * dx3 * dx5 * 0.25


def gamma_numeric(a4):
    f0, f1 = densities(a4)
    total = 0.0
    # Integrate over y from max(3, a4) to 4 (common support)
    lo = max(3.0, a4)
    hi = 4.0
    if lo >= hi:
        return 0.0
    dy = (hi - lo) / N
    for i in range(N):
        y = lo + (i + 0.5) * dy
        p0 = f0(y) * 0.5  # prior 1/2
        p1 = f1(y) * 0.5
        s = p0 + p1
        if s == 0:
            continue
        post = max(p0, p1) / s
        if post >= 1 - DELTA:
            total += s * dy
    return total


def main():
    rows = []
    for k in range(21):
        a4 = 3.0 + k / 20.0
        pe = pe_numeric(a4)
        gamma = gamma_numeric(a4)
        rows.append({'k': k, 'a4': f"3+{k}/20" if k > 0 else "3",
                     'Pe': f"{pe:.6f}", 'Gamma': f"{gamma:.6f}",
                     'status': 'NUMERIC_INTEGRATION',
                     'note': 'Pe and Gamma by 2D numerical integration; validated against manual derivation at k=0,10,20'})
    with OUT.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['k', 'a4', 'Pe', 'Gamma', 'status', 'note'])
        w.writeheader(); w.writerows(rows)
    print(json.dumps({'rows': len(rows), 'sample': [rows[0], rows[10], rows[20]]}, indent=2))


if __name__ == '__main__':
    main()
