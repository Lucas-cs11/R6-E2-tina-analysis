#!/usr/bin/env python3
"""Run TINA on a batch of candidates for GitHub Actions."""

import argparse
import csv
import gzip
import json
import os
import re
import shutil
from collections import Counter
from hashlib import sha256
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TINA = 'tina'  # assume in PATH
sys.path.insert(0, str(ROOT / 'implementations/generator_compat'))
from src.benchmarks.rmt_fms_generator import generate_rmt_fms  # noqa: E402


def net_to_pnml(net, name):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<pnml xmlns="http://www.pnml.org/version-2009/grammar/pnml">',
             f'  <net id="{name}" type="http://www.pnml.org/version-2009/grammar/ptnet">',
             '    <page id="page0">']
    for p in sorted(net.places):
        marking = net.initial_marking.get(p, 0)
        lines.append(f'      <place id="{p}">')
        if marking > 0:
            lines.append(f'        <initialMarking><text>{marking}</text></initialMarking>')
        lines.append('      </place>')
    for t in sorted(net.transitions):
        lines.append(f'      <transition id="{t}"/>')
    for i, a in enumerate(net.arcs):
        lines.append(f'      <arc id="a{i}" source="{a.from_node}" target="{a.to_node}"/>')
    lines.extend(['    </page>', '  </net>', '</pnml>'])
    return '\n'.join(lines)


def classify(returncode, stdout, stderr):
    if returncode != 0 or stderr.strip():
        return 'TOOL_ERROR'
    if not re.search(r'^Tina version 4\.0\.0\b', stdout, re.M):
        return 'INDETERMINATE'
    if not re.search(r'^mode -R\s*$', stdout, re.M):
        return 'INDETERMINATE'
    section = re.search(r'^REACHABILITY ANALYSIS -+[ \t]*\n(.*?)^LIVENESS ANALYSIS -+', stdout, re.M | re.S)
    if not section or not re.search(r'^ANALYSIS COMPLETED -+\s*$', stdout, re.M):
        return 'INDETERMINATE'
    labels = re.findall(r'^(bounded|net unbounded) *$', section.group(1), re.M)
    if labels == ['net unbounded']:
        return 'UNBOUNDED'
    if labels == ['bounded'] and re.search(r'^\d+ marking\(s\), \d+ transition\(s\) *$', section.group(1), re.M):
        return 'BOUNDED'
    return 'INDETERMINATE'


def run_tina(binary, pnml_path):
    try:
        result = subprocess.run([binary, '-PNML', '-R', '-q', str(pnml_path)],
                                capture_output=True, text=True, timeout=30)
        return classify(result.returncode, result.stdout, result.stderr), result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as exc:
        return 'TIMEOUT', None, (exc.stdout or b'').decode(errors='replace'), (exc.stderr or b'').decode(errors='replace')
    except OSError as exc:
        return 'TOOL_ERROR', None, '', str(exc)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--batch', type=int, required=True)
    ap.add_argument('--total-batches', type=int, default=10)
    ap.add_argument('--limit', type=int, help='Smoke test only; never use for full coverage')
    ap.add_argument('--output-dir', type=Path, required=True)
    args = ap.parse_args()
    binary = shutil.which(os.environ.get('TINA', TINA))
    if not binary:
        ap.error('TINA executable not found')
    if not 1 <= args.batch <= args.total_batches or (args.limit is not None and args.limit < 1):
        ap.error('Invalid shard or smoke limit')
    rows = list(csv.DictReader((ROOT / 'scope/generator_candidate_universe_full.csv').open(newline='', encoding='utf-8')))
    valid = [r for r in rows if r['static_validity'] == 'VALID_BY_FROZEN_RULE']
    batch_size = (len(valid) + args.total_batches - 1) // args.total_batches
    start = (args.batch - 1) * batch_size
    end = min(start + batch_size, len(valid))
    if len(valid) != 107520 or len({r['candidate_id'] for r in valid}) != len(valid) or start >= end:
        ap.error('Unexpected frozen population or empty shard')
    batch = valid[start:end][:args.limit]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.output_dir / f'tina_batch_{args.batch}.csv'
    raw_path = args.output_dir / f'tina_batch_{args.batch}.jsonl.gz'
    results = []
    evidence = gzip.open(raw_path, 'wt', encoding='utf-8')
    for r in batch:
        params = {'n_machines': int(r['machine_counts']), 'n_parts': int(r['part_type_counts']),
                  'ops_per_part': int(r['operations_per_part']), 'wip_bound': int(r['wip_bounds']),
                  'unobservable_ratio': float(r['unobservable_ratios']),
                  'fault_locations': int(r['fault_locations']),
                  'interval_width_factor': float(r['interval_width_factors']),
                  'adjustable_ratio': float(r['adjustable_ratios']),
                  'seed': 0, 'machine_capacity': 1, 'n_configs': 2, 'repair_domain': 'standard'}
        try:
            net, L, H = generate_rmt_fms(**params)
            pnml = net_to_pnml(net, r['candidate_id'])
            with tempfile.NamedTemporaryFile(mode='w', suffix='.pnml', delete=False) as tf:
                tf.write(pnml); tmp = tf.name
            try:
                status, code, stdout, stderr = run_tina(binary, tmp)
            finally:
                Path(tmp).unlink()
            digest = sha256(pnml.encode('utf-8')).hexdigest()
            results.append({'candidate_id': r['candidate_id'], 'status': status, 'returncode': code, 'pnml_sha256': digest,
                            'places': len(net.places), 'transitions': len(net.transitions)})
        except Exception as e:
            stdout, stderr = '', repr(e)
            results.append({'candidate_id': r['candidate_id'], 'status': 'CASE_ERROR',
                            'returncode': None, 'pnml_sha256': None, 'places': None, 'transitions': None})
        evidence.write(json.dumps({**results[-1], 'stdout': stdout, 'stderr': stderr}) + '\n')
    evidence.close()
    with out_path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(results[0])); w.writeheader(); w.writerows(results)
    counts = Counter(row['status'] for row in results)
    print(json.dumps({'batch': args.batch, 'processed': len(results), 'statuses': counts,
                      'smoke': args.limit is not None}))
    return int(bool(set(counts) - {'BOUNDED', 'UNBOUNDED'}))


if __name__ == '__main__':
    sys.exit(main())
