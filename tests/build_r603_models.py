#!/usr/bin/env python3
"""Build finite deterministic TPN models for R6-03 (no expected answers embedded)."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'models' / 'r603'
OUT.mkdir(parents=True, exist_ok=True)

places = ['root', 'work_c', 'work_e', 'work_d', 'work_h', 'work_budget', 'work_budget2', 'complete', 'legal_end']
completion = [{'complete': 1}]
legal = [{'legal_end': 1}]
initial = {'root': 1}
transitions = []
for name, target, weight in [('choose_c', 'work_c', '1'), ('choose_e', 'work_e', '1'),
                              ('choose_d', 'work_d', '1'), ('choose_h', 'work_h', '1'),
                              ('choose_budget', 'work_budget', '1')]:
    transitions.append({'id': name, 'kind': 'immediate', 'pre': {'root': 1}, 'post': {target: 1},
                        'weight': weight, 'label': None})
transitions += [
    {'id': 'c_fire', 'kind': 'timed', 'pre': {'work_c': 1}, 'post': {'complete': 1}, 'interval': ['1', '1'], 'label': 'c', 'external_event': 'done'},
    {'id': 'e_fire', 'kind': 'timed', 'pre': {'work_e': 1}, 'post': {'legal_end': 1}, 'interval': ['1', '1'], 'label': 'e', 'external_event': 'legal_end'},
    {'id': 'h_fire', 'kind': 'timed', 'pre': {'work_h': 1}, 'post': {'complete': 1}, 'interval': ['2', '2'], 'label': 'h', 'external_event': 'done'},
    {'id': 'budget_prepare', 'kind': 'timed', 'pre': {'work_budget': 1}, 'post': {'work_budget2': 1}, 'interval': ['0', '0'], 'label': 'prepare', 'external_event': None},
    {'id': 'budget_fire', 'kind': 'timed', 'pre': {'work_budget2': 1}, 'post': {'complete': 1}, 'interval': ['1', '1'], 'label': 'b', 'external_event': 'done'},
]
base = {'schema': 'FINITE_DETERMINISTIC_TPN_V1', 'id': 'R603_FIVE_OUTCOMES', 'places': places,
        'initial_marking': initial, 'transitions': transitions, 'completion_markings': completion,
        'legal_noncompletion_markings': legal, 'H_A': '1', 'path_budget': 3,
        'observation_projection': 'label_plus_external_completion'}
(OUT / 'five_outcomes.json').write_text(json.dumps(base, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
budget = dict(base); budget['id'] = 'R603_BUDGET_FRONTIER'; budget['path_budget'] = 2
(OUT / 'budget_frontier.json').write_text(json.dumps(budget, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
endpoint = dict(base); endpoint['id'] = 'R603_ENDPOINT_DUE_BEFORE_TRUNCATION'
endpoint['transitions'] = [dict(t, interval=['1', '1']) if t['id'] == 'h_fire' else t for t in transitions]
(OUT / 'endpoint.json').write_text(json.dumps(endpoint, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('built', len(list(OUT.glob('*.json'))))
