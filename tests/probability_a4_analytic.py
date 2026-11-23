#!/usr/bin/env python3
"""Exact analytic Pe* for Y0=max(X3,X5) vs Y1=max(X4,X5), a4 in [3,4].

Pe* = (4-a4)^2 / (4*(5-a4))
Validated against symbolic integration at a4=3 (1/8), a4=3.5 (1/24), a4=4 (0).
Gamma_delta = 0 for all a4 (posterior = 0.5 on common support < 1-delta = 0.85).
"""

import csv
import json
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/probability_a4_21points.csv'


def pe_exact(a4_frac):
    a4 = F(a4_frac)
    return (F(4) - a4) ** 2 / (F(4) * (F(5) - a4))


def main():
    rows = []
    for k in range(21):
        a4 = F(3) + F(k, 20)
        pe = pe_exact(a4)
        rows.append({'k': k, 'a4': str(a4), 'Pe': str(pe), 'Gamma': '0',
                     'status': 'EXACT_ANALYTIC',
                     'note': 'Pe=(4-a4)^2/(4*(5-a4)); Gamma=0 (posterior=0.5<0.85); validated at k=0,10,20'})
    with OUT.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['k', 'a4', 'Pe', 'Gamma', 'status', 'note'])
        w.writeheader(); w.writerows(rows)
    print(json.dumps({'rows': len(rows), 'sample': [rows[0], rows[10], rows[20]]}, indent=2))


if __name__ == '__main__':
    main()
