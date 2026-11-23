#!/usr/bin/env python3
"""Root weight as X4 interval width factor: Pe sensitivity.

X4 ~ U[a4, 5*w] where w is interval width factor.
Pe* = P[max(X3,X5) > max(X4,X5)] computed by numerical integration.
"""

import csv
import json
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/probability_a4_width_sensitivity.csv'
N = 1000


def pe_numeric(a4, w):
    total = 0.0
    hi_x4 = 5.0 * w
    dx3 = 2.0 / N
    dx5 = 2.0 / N
    for i in range(N):
        x3 = 2.0 + (i + 0.5) * dx3
        for j in range(N):
            x5 = 1.0 + (j + 0.5) * dx5
            y0 = max(x3, x5)
            if y0 > a4:
                total += (y0 - a4) / (hi_x4 - a4)
    return total * dx3 * dx5 * 0.25


def main():
    weights = {'W1': 1.0, 'W1.5': 1.5, 'W0.5': 0.5}
    rows = []
    for k in [0, 5, 10, 15, 20]:  # subset for speed
        a4 = 3.0 + k / 20.0
        for wname, w in weights.items():
            pe = pe_numeric(a4, w)
            rows.append({'k': k, 'a4': f"3+{k}/20" if k > 0 else "3", 'weight': wname, 'width_factor': w,
                         'Pe': f"{pe:.6f}", 'note': 'Pe by numerical integration with X4~U[a4,5w]'})
    with OUT.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(json.dumps({'rows': len(rows), 'sample': rows[:3]}, indent=2))


if __name__ == '__main__':
    main()
