#!/usr/bin/env python3
"""Same-task adapter for 52 historical models: map freeze params to current engine, verify structural equivalence."""

import csv
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys_path_backup = list(__import__('sys').path)
spec = importlib.util.spec_from_file_location('r6e2_gen', ROOT / 'tests/generate_all_valid_candidates.py')
gen = importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)
__import__('sys').path[:] = sys_path_backup

FREEZE = json.loads((ROOT / 'scope/freeze.json').read_text(encoding='utf-8'))
HIST = list(csv.DictReader((ROOT / 'scope/逻辑逐行_完整精度.csv').open(newline='', encoding='utf-8')))
FIXED = {'seed': 0, 'machine_capacity': 1, 'n_configs': 2, 'repair_domain': 'standard'}


def adapt_and_verify(case_id, params):
    merged = dict(params); merged.update({k: v for k, v in FIXED.items() if k not in merged})
    net, L, H = gen.generate_rmt_fms(**merged)
    issues = gen.validate(net, merged, L, H)
    payload = gen.canonical(net, merged, L, H)
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    hist = next((r for r in HIST if r['case_id'] == case_id and r['method'] == 'main'), None)
    if hist is None:
        return {'status': 'MISSING_HISTORICAL', 'model_sha256': digest}
    hist_match = (str(L) == hist['L'] and str(H) == hist['H']
                  and str(len(net.places)) == hist['places'] and str(len(net.transitions)) == hist['transitions'])
    return {'status': 'ADAPTER_VALIDATED' if not issues and hist_match else 'ADAPTER_MISMATCH',
            'model_sha256': digest, 'L': str(L), 'H': str(H),
            'places': len(net.places), 'transitions': len(net.transitions),
            'hist_L': hist['L'], 'hist_H': hist['H'], 'hist_places': hist['places'],
            'structural_issues': ';'.join(issues), 'hist_match': hist_match}


def main():
    out = []
    seen = set()
    for task in FREEZE['tasks']:
        if task.get('method') != 'main':
            continue
        cid = task['case_id']
        if cid in seen:
            continue
        seen.add(cid)
        family = task.get('family')
        if family == 'rmt_original_subset' and task.get('params'):
            r = adapt_and_verify(cid, task['params'])
            out.append({'case_id': cid, 'family': family, **r})
        elif family == 'micro':
            out.append({'case_id': cid, 'family': 'micro', 'status': 'NOT_AVAILABLE_PARAMS_ONLY',
                        'model_sha256': '', 'note': 'micro model has no generator params in freeze'})
        else:
            out.append({'case_id': cid, 'family': family, 'status': 'SKIPPED',
                        'model_sha256': '', 'note': f'unexpected family/method: {family}/{task.get("method")}'})
    path = ROOT / 'results/baseline_adapter_52.csv'
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['case_id', 'family', 'status', 'model_sha256', 'L', 'H',
                                          'places', 'transitions', 'hist_L', 'hist_H', 'hist_places',
                                          'structural_issues', 'hist_match', 'note'])
        w.writeheader(); w.writerows(out)
    from collections import Counter
    c = Counter(r['status'] for r in out)
    print(json.dumps({'total': len(out), 'statuses': dict(c)}, indent=2))


if __name__ == '__main__':
    main()
