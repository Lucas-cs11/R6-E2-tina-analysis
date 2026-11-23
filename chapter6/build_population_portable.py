#!/usr/bin/env python3
"""Portable PyScrew source manifest builder.

Usage:
  python3 chapter6/build_population_portable.py --raw-root /path/to/pyscrew
No host-specific absolute path is embedded. Without raw files, output status is
SOURCE_MANIFEST_AUDITED_NOT_RAW_VERIFIED (never FULL_RAW_REPRODUCIBLE).
"""

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''): h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--raw-root', required=True, help='directory containing labels.csv, split_plan.csv and raw_json/')
    ap.add_argument('--out-manifest', default=str(ROOT / 'scope/pyscrew_raw_manifest.csv'))
    ap.add_argument('--out-summary', default=str(ROOT / 'scope/pyscrew_raw_summary.json'))
    args = ap.parse_args()
    src = Path(args.raw_root).resolve()
    labels_path = src / 'labels.csv'
    split_path = src / 'split_plan.csv'
    raw_dir = src / 'raw_json'
    if not labels_path.is_file() or not split_path.is_file():
        raise SystemExit('MISSING_DEPENDENCY: raw-root must contain labels.csv and split_plan.csv')
    labels = list(csv.DictReader(labels_path.open(newline='', encoding='utf-8')))
    split = {r['run_id']: r for r in csv.DictReader(split_path.open(newline='', encoding='utf-8'))}
    raw_available = raw_dir.is_dir()
    rows = []
    for r in labels:
        path = raw_dir / r['class_value'] / r['file_name'] if raw_available else None
        file_sha = sha(path) if path and path.is_file() else 'RAW_NOT_PROVIDED'
        raw_result = ''
        step_count = 0
        if path and path.is_file():
            data = json.loads(path.read_text(encoding='utf-8'))
            raw_result = data.get('result', '')
            step_count = len(data.get('tightening steps', []))
        sp = split.get(r['run_id'], {})
        rows.append({
            'run_id': r['run_id'], 'file_name': r['file_name'], 'physical_class': r['class_value'],
            'workpiece_id': r['workpiece_id'], 'location': r['workpiece_location'],
            'workpiece_result': r['workpiece_result'], 'scenario_condition': r['scenario_condition'],
            'split': sp.get('split', 'UNKNOWN'), 'raw_result': raw_result,
            'tightening_step_count': step_count, 'file_sha256': file_sha,
            'source_group': f"{r['class_value']}|{r['workpiece_location']}",
        })
    with Path(args.out_manifest).open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    by_wp = defaultdict(list)
    for r in rows: by_wp[r['workpiece_id']].append(r)
    summary = {
        'status': 'PASS' if len(rows) == 5000 and len(by_wp) == 2500 else 'FAIL',
        'raw_files_available': raw_available,
        'verification_level': 'SOURCE_MANIFEST_AUDITED' if raw_available else 'SOURCE_MANIFEST_AUDITED_NOT_RAW_VERIFIED',
        'raw_rows': len(rows), 'workpieces': len(by_wp),
        'classes': len({r['physical_class'] for r in rows}),
        'source_groups': len({r['source_group'] for r in rows}),
        'pair_failures': sum(sorted(x['location'] for x in v) != ['left', 'right'] for v in by_wp.values()),
        'raw_sha256_provided': sum(r['file_sha256'] != 'RAW_NOT_PROVIDED' for r in rows),
        'note': 'never claims FULL_RAW_REPRODUCIBLE unless every raw JSON SHA is recomputed from provided files',
    }
    Path(args.out_summary).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    raise SystemExit(0 if summary['status'] == 'PASS' else 1)


if __name__ == '__main__':
    raise SystemExit(main())
