#!/usr/bin/env python3
"""End-to-end negative controls for the R6-E2 evidence verifier."""

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'runs/negative_controls'
OUT.mkdir(parents=True, exist_ok=True)
PY = sys.executable
COMPONENTS = ('g2_r601', 'g2_r602', 'g2_r603', 'g2_r604', 'g2_r605', 'g2_r606', 'g2_r607', 'g2_r608_module', 'g2_r609', 'g2_r610', 'g2_r611', 'g2_r612', 'g2_r613')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--raw-root', default=os.environ.get('R6E2_RAW_ROOT', str(ROOT.parents[1] / 'pyscrew')))
    args = ap.parse_args()

    def verify(label, expected_fail=True, **kwargs):
        argv = [PY, 'tests/final_verify_r6_e2.py']
        for key, value in kwargs.items():
            if value is not None: argv += ['--' + key.replace('_', '-'), str(value)]
        proc = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, timeout=180)
        (OUT / f'{label}.stdout.json').write_text(proc.stdout, encoding='utf-8')
        (OUT / f'{label}.stderr.log').write_text(proc.stderr, encoding='utf-8')
        return {'id': label, 'exit_code': proc.returncode,
                'failed_as_expected': proc.returncode != 0 if expected_fail else proc.returncode == 0}

    def copy_components(name):
        target = OUT / name
        if target.exists(): shutil.rmtree(target)
        target.mkdir()
        for component in COMPONENTS: shutil.copytree(ROOT / 'runs' / component, target / component)
        return target

    controls = []
    raw = args.raw_root
    manifest_rows = list(csv.DictReader((ROOT / 'scope/pyscrew_raw_manifest.csv').open(newline='', encoding='utf-8')))
    manifest_fields = list(manifest_rows[0])

    def write_manifest(path, rows):
        with path.open('w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=manifest_fields); w.writeheader(); w.writerows(rows)

    tampered = [dict(r) for r in manifest_rows]; tampered[0]['file_sha256'] = '0' * 64
    p = OUT / 'tampered_manifest.csv'; write_manifest(p, tampered)
    controls.append(verify('TAMPER_RAW_SHA', manifest=p, raw_root=raw))

    aliased = [dict(r) for r in manifest_rows]
    sample = Path(raw) / 'raw_json' / manifest_rows[0]['physical_class'] / manifest_rows[0]['file_name']
    digest = hashlib.sha256(sample.read_bytes()).hexdigest()
    for r in aliased: r['file_name'] = str(sample); r['file_sha256'] = digest
    p = OUT / 'absolute_duplicate_manifest.csv'; write_manifest(p, aliased)
    controls.append(verify('ABSOLUTE_DUPLICATE_RAW', manifest=p, raw_root=raw))

    universe = list(csv.DictReader((ROOT / 'scope/generator_candidate_universe_full.csv').open(newline='', encoding='utf-8')))
    p = OUT / 'dropped_universe.csv'
    with p.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(universe[0])); w.writeheader(); w.writerows(universe[:-1])
    controls.append(verify('DROP_UNIVERSE_ROW', universe=p))

    generated = list(csv.DictReader((ROOT / 'results/all_population_results.csv').open(newline='', encoding='utf-8')))
    generated[0]['model_sha256'] = '0' * 64
    p = OUT / 'zero_model_sha.csv'
    with p.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(generated[0])); w.writeheader(); w.writerows(generated)
    controls.append(verify('ZERO_MODEL_SHA', generated=p))

    g1 = list(csv.DictReader((ROOT / 'runs/g1_r608/results.csv').open(newline='', encoding='utf-8')))
    g1[0]['status'] = 'FAIL'; p = OUT / 'flipped_g1.csv'
    with p.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(g1[0])); w.writeheader(); w.writerows(g1)
    controls.append(verify('FLIP_G1_STATUS', g1=p))

    comp = copy_components('components_flipped_r603')
    p = comp / 'g2_r603/results.csv'; rows = list(csv.DictReader(p.open(newline='', encoding='utf-8'))); rows[0]['status'] = 'FAIL'
    with p.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    controls.append(verify('FLIP_R603_LEDGER', raw_root=raw, components_root=comp))

    comp = copy_components('components_empty_r605')
    p = comp / 'g2_r605/results.csv'; rows = list(csv.DictReader(p.open(newline='', encoding='utf-8')))
    with p.open('w', newline='', encoding='utf-8') as f: csv.DictWriter(f, fieldnames=list(rows[0])).writeheader()
    summary_path = comp / 'g2_r605/summary.json'; summary = json.loads(summary_path.read_text())
    summary.update(cases=0, passed=0, mutations=[]); summary_path.write_text(json.dumps(summary))
    controls.append(verify('EMPTY_R605_COMPONENT', raw_root=raw, components_root=comp))

    comp = copy_components('components_missing_patch')
    for patch in (comp / 'g2_r606/mutations').rglob('mutation.patch'): patch.unlink()
    controls.append(verify('MISSING_R606_MUTATION_PATCH', raw_root=raw, components_root=comp))

    comp = copy_components('components_raw_mismatch')
    p = comp / 'g2_r606/FULL_WORD_DIFFERENT.subject.json'; evidence = json.loads(p.read_text())
    evidence['verdict'] = '1'; p.write_text(json.dumps(evidence))
    controls.append(verify('R606_RAW_SEMANTIC_MISMATCH', raw_root=raw, components_root=comp))

    tex_copy = OUT / 'tampered_theory.tex'
    tex_copy.write_bytes((ROOT / 'baseline_readonly/example_revised_theory_v2_theory_round6_candidate.tex').read_bytes() + b'% negative-control-only copy\n')
    controls.append(verify('TEX_HASH_MISMATCH', tex=tex_copy))

    controls.append(verify('BASELINE_UNMODIFIED', expected_fail=False, raw_root=raw))
    summary = {'status': 'PASS' if all(c['failed_as_expected'] for c in controls) else 'FAIL',
               'controls': controls, 'negative_controls': sum(c['id'] != 'BASELINE_UNMODIFIED' for c in controls),
               'note': 'raw paths, model replay, component raw evidence, mutation artifacts and TeX hash are bound'}
    (OUT / 'negative_controls.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    raise SystemExit(0 if summary['status'] == 'PASS' else 1)


if __name__ == '__main__':
    raise SystemExit(main())
