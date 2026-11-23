#!/usr/bin/env python3
"""Observation quantization: Pe* for Y discretized into different bucket counts."""

import csv
import json
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/probability_a4_quantization.csv'


def pe_quantized(a4, num_buckets):
    """Pe* when Y is quantized into num_buckets buckets on [3,4]."""
    a4 = F(a4)
    # For simplicity, use the analytic Pe and discretize
    # Pe* = P[Y0 > Y1] with quantized Y
    # Quantization: bucket width = 1/num_buckets on [3,4]
    # Y0_quant = floor((Y0-3)*num_buckets)/num_buckets + 3
    # Y1_quant = floor((Y1-3)*num_buckets)/num_buckets + 3
    # Pe* = P[Y0_quant > Y1_quant]
    # This is complex; use numerical integration
    N = 500
    total = 0.0
    dx3 = 2.0 / N
    dx5 = 2.0 / N
    for i in range(N):
        x3 = 2.0 + (i + 0.5) * dx3
        for j in range(N):
            x5 = 1.0 + (j + 0.5) * dx5
            y0 = max(x3, x5)
            # Quantize y0
            y0q = 3.0 + int((y0 - 3.0) * num_buckets) / num_buckets if y0 >= 3.0 else 3.0
            # P[Y1_quant < y0q] = P[X4 < y0q] (approximate)
            if y0q > a4:
                p = (y0q - a4) / (5.0 - a4)
            else:
                p = 0.0
            total += p
    return total * dx3 * dx5 * 0.25


def main():
    buckets = [1, 2, 4, 8, 16]
    rows = []
    for k in [0, 10, 20]:
        a4 = 3.0 + k / 20.0
        for b in buckets:
            pe = pe_quantized(a4, b)
            rows.append({'k': k, 'a4': f"3+{k}/20" if k > 0 else "3", 'buckets': b,
                         'Pe': f"{pe:.6f}", 'note': 'Pe with Y quantized into b buckets on [3,4]'})
    with OUT.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(json.dumps({'rows': len(rows), 'sample': rows[:5]}, indent=2))


if __name__ == '__main__':
    main()
