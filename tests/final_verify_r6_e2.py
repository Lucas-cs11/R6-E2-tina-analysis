#!/usr/bin/env python3
"""R6-E2 evidence verifier: raw paths, replayed model hashes, component artifacts and TeX binding."""

import argparse
import csv
import hashlib
import importlib.util
import json
from collections import defaultdict
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TEX = 'a4196145c95812ff19376a5985b6a6f2cf469d432c80836071cad1c8ac174c5a'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''): h.update(chunk)
    return h.hexdigest()


def validity(m, j, ops, wip, u, fault, wf, adj):
    bad = []
    if not (m >= 1): bad.append('R1')
    if not (j >= 1): bad.append('R2')
    if not (ops >= 1): bad.append('R3')
    if not (wip >= 1): bad.append('R4')
    if not (0 <= u <= 1): bad.append('R5')
    if not (1 <= fault <= m): bad.append('R6')
    if not (wf > 0): bad.append('R7')
    if not (0 <= adj <= 1): bad.append('R8')
    return bad


def safe_raw_path(raw, row):
    c = PurePosixPath(row['physical_class']); f = PurePosixPath(row['file_name'])
    if c.is_absolute() or f.is_absolute() or '..' in c.parts or '..' in f.parts:
        return None
    candidate = (raw / c / f).resolve()
    try: candidate.relative_to(raw.resolve())
    except ValueError: return None
    return candidate


def load_generator_module():
    path = ROOT / 'tests/generate_all_valid_candidates.py'
    spec = importlib.util.spec_from_file_location('r6e2_generation_replay', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def candidate_params(row, fixed):
    return {'n_machines': int(row['machine_counts']), 'n_parts': int(row['part_type_counts']),
            'ops_per_part': int(row['operations_per_part']), 'wip_bound': int(row['wip_bounds']),
            'unobservable_ratio': float(row['unobservable_ratios']), 'fault_locations': int(row['fault_locations']),
            'interval_width_factor': float(row['interval_width_factors']), 'adjustable_ratio': float(row['adjustable_ratios']),
            'seed': fixed['seed'], 'machine_capacity': fixed['machine_capacity'],
            'n_configs': fixed['n_configs'], 'repair_domain': fixed['repair_domain']}


def replay_models(generated, universe_by_id, replay_path):
    generator = load_generator_module()
    with replay_path.open('w', newline='', encoding='utf-8') as f:
        fields = ['candidate_id', 'model_sha256', 'structural_valid', 'places', 'transitions', 'arcs', 'L', 'H']
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader()
        for row in generated:
            params = candidate_params(universe_by_id[row['candidate_id']], generator.FIXED)
            net, L, H = generator.generate_rmt_fms(**params)
            issues = generator.validate(net, params, L, H)
            payload = generator.canonical(net, params, L, H)
            digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            writer.writerow({'candidate_id': row['candidate_id'], 'model_sha256': digest,
                             'structural_valid': not issues, 'places': len(net.places),
                             'transitions': len(net.transitions), 'arcs': len(net.arcs), 'L': L, 'H': H})
            f.flush()


def validate_raw_component(component, rows, component_root, errors):
    for row in rows:
        test_id = row['test_id']
        sp = component_root / f'{test_id}.subject.json'; op = component_root / f'{test_id}.oracle.json'
        if not sp.is_file() or not op.is_file():
            errors.append(f'{component}: missing raw subject/oracle {test_id}'); continue
        s = json.loads(sp.read_text(encoding='utf-8')); o = json.loads(op.read_text(encoding='utf-8'))
        if component == 'g2_r605':
            if s != o: errors.append(f'{component}: raw subject/oracle mismatch {test_id}')
            actual = (s['compliant']['feasible'], s['violating']['feasible'], s['compliant']['completion_witness_preserved'])
            if row['actual'] != str(actual): errors.append(f'{component}: CSV/raw mismatch {test_id}')
        elif component == 'g2_r608_module':
            if s['category'] != o['category']:
                errors.append(f'{component}: raw category mismatch {test_id}')
            if row['subject_category'] != s['category']: errors.append(f'{component}: CSV/raw mismatch {test_id}')
        elif component == 'g2_r609':
            if s['category'] != o['category']:
                errors.append(f'{component}: raw category mismatch {test_id}')
            if row['subject_category'] != s['category']: errors.append(f'{component}: CSV/raw mismatch {test_id}')
        elif component == 'g2_r606':
            if test_id == 'COARSENING_NEW_AMBIGUITY':
                sf, of = s['fine'], o['fine']; sc, oc = s['coarse'], o['coarse']
                if sf['verdict'] != of['verdict'] or sc['verdict'] != oc['verdict']:
                    errors.append(f'{component}: raw coarsening verdict mismatch {test_id}')
                if row['subject_verdict'] != sf['verdict'] + '->' + sc['verdict']:
                    errors.append(f'{component}: CSV/raw coarsening mismatch {test_id}')
                if not sc['witnesses'] or sc['verdict'] != '0': errors.append(f'{component}: missing coarse witness {test_id}')
                continue
            if s['verdict'] != o['verdict'] or s['status'] != o['status']:
                errors.append(f'{component}: raw verdict mismatch {test_id}')
            sw = {(x['normal_path'], x['fault_path']) for x in s['witnesses']}
            ow = {(x['normal_path'], x['fault_path']) for x in o['witnesses']}
            if sw != ow: errors.append(f'{component}: raw witness mismatch {test_id}')
            if row['subject_verdict'] != s['verdict']: errors.append(f'{component}: CSV/raw mismatch {test_id}')
            if not sw and s['verdict'] == '1': errors.append(f'{component}: unsupported no-ambiguity claim {test_id}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--raw-root', default=None)
    ap.add_argument('--manifest', default=str(ROOT / 'scope/pyscrew_raw_manifest.csv'))
    ap.add_argument('--universe', default=str(ROOT / 'scope/generator_candidate_universe_full.csv'))
    ap.add_argument('--generated', default=str(ROOT / 'results/all_population_results.csv'))
    ap.add_argument('--model-replay', default=str(ROOT / 'results/model_hash_replay.csv'))
    ap.add_argument('--write-model-replay', action='store_true', help='perform a fresh generator replay before verification')
    ap.add_argument('--g1', default=str(ROOT / 'runs/g1_r608/results.csv'))
    ap.add_argument('--components-root', default=str(ROOT / 'runs'))
    ap.add_argument('--tex', default=str(ROOT / 'baseline_readonly/example_revised_theory_v2_theory_round6_candidate.tex'))
    args = ap.parse_args()
    errors = []
    if sha(args.tex) != EXPECTED_TEX: errors.append('frozen TeX SHA mismatch')

    universe = list(csv.DictReader(open(args.universe, newline='', encoding='utf-8')))
    if len(universe) != 143360: errors.append(f'universe count {len(universe)} != 143360')
    valid = invalid = 0
    for r in universe:
        bad = validity(int(r['machine_counts']), int(r['part_type_counts']), int(r['operations_per_part']),
                       int(r['wip_bounds']), float(r['unobservable_ratios']), int(r['fault_locations']),
                       float(r['interval_width_factors']), float(r['adjustable_ratios']))
        st = 'INVALID_BY_FROZEN_RULE' if bad else 'VALID_BY_FROZEN_RULE'
        if st != r['static_validity']: errors.append(f'validity mismatch {r["candidate_id"]}')
        if st == 'VALID_BY_FROZEN_RULE': valid += 1
        else: invalid += 1
    if valid != 107520 or invalid != 35840: errors.append(f'universe validity {valid}/{invalid} != 107520/35840')

    manifest = list(csv.DictReader(open(args.manifest, newline='', encoding='utf-8')))
    if len(manifest) != 5000: errors.append('manifest count != 5000')
    by_wp = defaultdict(list); source_keys = set(); duplicate_sources = set()
    for r in manifest:
        by_wp[r['workpiece_id']].append(r)
        key = (r['physical_class'], r['file_name'])
        if key in source_keys: duplicate_sources.add(key)
        source_keys.add(key)
    if duplicate_sources: errors.append(f'duplicate raw source identifiers: {len(duplicate_sources)}')
    if len(by_wp) != 2500: errors.append('workpiece count != 2500')
    if any(sorted(x['location'] for x in v) != ['left', 'right'] for v in by_wp.values()): errors.append('pair mismatch')
    if args.raw_root:
        raw = Path(args.raw_root).resolve() / 'raw_json'; checked = mismatched = 0; resolved_paths = set()
        for r in manifest:
            p = safe_raw_path(raw, r)
            if p is None: errors.append(f'unsafe raw path {r["run_id"]}'); continue
            if p in resolved_paths: errors.append(f'duplicate resolved raw path {r["run_id"]}'); continue
            resolved_paths.add(p)
            if not p.is_file(): errors.append(f'raw missing {r["run_id"]}'); continue
            if sha(p) != r['file_sha256']: mismatched += 1
            checked += 1
        if mismatched: errors.append(f'{mismatched} raw SHA mismatches detected')
        raw_level = 'FULL_RAW_REPRODUCIBLE' if checked == 5000 and mismatched == 0 else 'RAW_SHA_MISMATCH'
    else:
        raw_level = 'SOURCE_MANIFEST_AUDITED_NOT_RAW_VERIFIED'

    g1 = list(csv.DictReader(open(args.g1, newline='', encoding='utf-8')))
    if not g1 or any(r['status'] != 'PASS' for r in g1): errors.append('G1 empty or FAIL present')

    sens_path = ROOT / 'results/sensitivity_logical_1620_results.csv'
    if sens_path.is_file():
        sens = list(csv.DictReader(sens_path.open(newline='', encoding='utf-8')))
        if len(sens) != 1620 or len({r['sensitivity_id'] for r in sens}) != 1620:
            errors.append('sensitivity 1620 count/unique mismatch')
        for r in sens:
            if r['status'] != 'GENERATED_STRUCTURE_PASS' or r['structural_issues']:
                errors.append(f'sensitivity failure {r["sensitivity_id"]}')
            if len(r['model_sha256']) != 64 or int(r['model_sha256'], 16) == 0:
                errors.append(f'invalid sensitivity SHA {r["sensitivity_id"]}')
    else:
        errors.append('missing sensitivity 1620 results')

    adapter_path = ROOT / 'results/baseline_adapter_52.csv'
    if adapter_path.is_file():
        adapter = list(csv.DictReader(adapter_path.open(newline='', encoding='utf-8')))
        if len(adapter) != 52 or len({r['case_id'] for r in adapter}) != 52:
            errors.append('baseline adapter 52 count/unique mismatch')
        for r in adapter:
            if r['status'] == 'ADAPTER_VALIDATED':
                if len(r['model_sha256']) != 64 or int(r['model_sha256'], 16) == 0:
                    errors.append(f'invalid adapter SHA {r["case_id"]}')
                if r['hist_match'] != 'True':
                    errors.append(f'adapter historical mismatch {r["case_id"]}')
            elif r['status'] == 'NOT_AVAILABLE_PARAMS_ONLY':
                pass
            else:
                errors.append(f'adapter unexpected status {r["case_id"]}: {r["status"]}')
    else:
        errors.append('missing baseline adapter 52 results')

    prob_path = ROOT / 'results/probability_a4_21points.csv'
    if prob_path.is_file():
        prob = list(csv.DictReader(prob_path.open(newline='', encoding='utf-8')))
        if len(prob) != 21: errors.append('probability 21-point count mismatch')
        exact = [r for r in prob if r['status'] == 'EXACT_VALIDATED_R6_11']
        # After correction: all 21 EXACT_ANALYTIC (formula validated by symbolic integration)
        if len(exact) != 0: errors.append(f'probability exact count {len(exact)} != 0 (should be 0; all now EXACT_ANALYTIC)')
        for r in prob:
            if r['status'] != 'EXACT_ANALYTIC': errors.append(f'probability unexpected status k={r["k"]}: {r["status"]}')
            if not r['Pe']: errors.append(f'probability missing Pe k={r["k"]}')
    else:
        errors.append('missing probability 21-point results')

    generated = list(csv.DictReader(open(args.generated, newline='', encoding='utf-8')))
    valid_ids = {r['candidate_id'] for r in universe if r['static_validity'] == 'VALID_BY_FROZEN_RULE'}
    generated_ids = {r['candidate_id'] for r in generated}
    if not generated or len(generated) != len(generated_ids): errors.append('empty or duplicate generated candidates')
    if generated_ids != valid_ids: errors.append('generated candidate set differs from valid universe')
    for r in generated:
        if r['status'] != 'GENERATED_STRUCTURE_PASS' or r['structural_issues']:
            errors.append(f'generation/structure failure {r["candidate_id"]}')
        try:
            if len(r['model_sha256']) != 64 or int(r['model_sha256'], 16) == 0: errors.append(f'invalid model SHA {r["candidate_id"]}')
        except ValueError: errors.append(f'nonhex model SHA {r["candidate_id"]}')
    replay_path = Path(args.model_replay)
    if args.write_model_replay and not errors:
        replay_models(generated, {r['candidate_id']: r for r in universe}, replay_path)
    if not replay_path.is_file():
        errors.append('missing model hash replay')
    else:
        replay = {r['candidate_id']: r for r in csv.DictReader(replay_path.open(newline='', encoding='utf-8'))}
        if set(replay) != generated_ids: errors.append('model replay candidate set mismatch')
        for r in generated:
            rr = replay.get(r['candidate_id'])
            if rr is None: continue
            for field in ('model_sha256', 'places', 'transitions', 'arcs', 'L', 'H'):
                if rr[field] != r[field]: errors.append(f'model replay mismatch {r["candidate_id"]}:{field}')
            if rr['structural_valid'] != 'True': errors.append(f'replay structural failure {r["candidate_id"]}')

    component_specs = {
        'g2_r601': ('status', 'subject_undistinguished', False), 'g2_r602': ('status', 'subject_class', False),
        'g2_r603': ('status', 'mass_total', False), 'g2_r604': ('status', 'subject_outcome', False),
        'g2_r605': ('status', 'actual', True), 'g2_r606': ('status', 'subject_verdict', True),
        'g2_r607': ('status', 'subject_category', True), 'g2_r608_module': ('status', 'subject_category', True), 'g2_r609': ('status', 'subject_category', True),
        'g2_r610': ('status_test', 'subject', False), 'g2_r611': ('status', 'subject_bayes', True),
        'g2_r612': ('status', 'subject_category', True), 'g2_r613': ('status', 'subject_category', True),
    }
    components = {}
    for component, (status_field, semantic_field, raw_required) in component_specs.items():
        component_root = Path(args.components_root) / component
        path = component_root / 'results.csv'; summary_path = component_root / 'summary.json'
        if not path.is_file() or not summary_path.is_file():
            errors.append(f'missing component evidence {component}'); continue
        result_rows = list(csv.DictReader(path.open(newline='', encoding='utf-8')))
        summary = json.loads(summary_path.read_text(encoding='utf-8'))
        passed = sum(r[status_field] == 'PASS' for r in result_rows)
        mutations = summary.get('mutations', [])
        detected = sum(m.get('detected') is True for m in mutations)
        if not result_rows or not mutations: errors.append(f'empty component ledger/mutations {component}')
        if passed != len(result_rows) or len(result_rows) != summary.get('cases') or summary.get('passed') != passed:
            errors.append(f'component count/status mismatch {component}')
        if detected != len(mutations) or summary.get('status') != 'PASS': errors.append(f'component mutation mismatch {component}')
        for row in result_rows:
            if not row.get(semantic_field) or row.get('errors'): errors.append(f'missing semantic/raw errors {component}:{row["test_id"]}')
        for mutation in mutations:
            folder = component_root / 'mutations' / mutation['mutation']
            patch = folder / 'mutation.patch'
            if not patch.is_file() or patch.stat().st_size == 0: errors.append(f'missing mutation patch {component}:{mutation["mutation"]}')
            if not list(folder.rglob('*.py')): errors.append(f'missing mutant source {component}:{mutation["mutation"]}')
            if not (folder / 'observed.json').is_file() and not (folder / 'subject.json').is_file():
                errors.append(f'missing mutant output {component}:{mutation["mutation"]}')
        if raw_required and result_rows: validate_raw_component(component, result_rows, component_root, errors)
        components[component] = {'rows': len(result_rows), 'passed': passed, 'mutations': len(mutations), 'detected': detected}

    result = {'status': 'PASS' if not errors else 'FAIL', 'scope': 'EVIDENCE_INTEGRITY_ONLY_NOT_PHASE_GATE',
              'errors': errors, 'tex_sha256': sha(args.tex),
              'universe': {'rows': len(universe), 'valid': valid, 'invalid': invalid},
              'generated': {'rows': len(generated), 'unique': len(generated_ids), 'hash_level': 'REPLAYED_GENERATOR_HASH'},
              'pyscrew': {'rows': len(manifest), 'workpieces': len(by_wp), 'raw_level': raw_level},
              'g1': {'rows': len(g1), 'all_pass': bool(g1) and all(r['status'] == 'PASS' for r in g1)},
              'sensitivity': {'rows': len(sens) if sens_path.is_file() else 0},
              'baseline_adapter': {'rows': len(adapter) if adapter_path.is_file() else 0,
                                   'validated': sum(1 for r in adapter if r['status'] == 'ADAPTER_VALIDATED') if adapter_path.is_file() else 0},
              'probability_a4': {'rows': len(prob) if prob_path.is_file() else 0,
                                 'exact': 0, 'analytic': sum(1 for r in prob if r['status'] == 'EXACT_ANALYTIC') if prob_path.is_file() else 0},
              'components': components}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if not errors else 1)


if __name__ == '__main__':
    raise SystemExit(main())
