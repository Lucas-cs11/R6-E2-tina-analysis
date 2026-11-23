#!/usr/bin/env python3
"""Independent R6-03 reference executor; does not import subject code."""

from fractions import Fraction as Q

C = 'R6-E2-R6-03-PARTIAL'
TEX = 'a4196145c95812ff19376a5985b6a6f2cf469d432c80836071cad1c8ac174c5a'


def run(model):
    by_id = {x['id']: x for x in model['transitions']}
    root = model['initial_marking']
    enabled_roots = []
    for x in model['transitions']:
        if x['kind'] == 'immediate' and all(root.get(p, 0) >= n for p, n in x['pre'].items()):
            enabled_roots.append(x)
    denominator = sum((Q(x['weight']) for x in enabled_roots), Q(0))
    if denominator == 0: raise ValueError('zero root weight')
    leaves = []
    for choice in enabled_roots:
        marking = dict(root)
        for p, n in choice['pre'].items(): marking[p] -= n
        marking = {p: n for p, n in marking.items() if n}
        for p, n in choice.get('post', {}).items(): marking[p] = marking.get(p, 0) + n
        history = [choice['id']]
        observations = []
        now = Q(0)
        first_completion = None
        records = [{'transition': choice['id'], 'M_minus': {p: root.get(p, 0) - n for p, n in choice['pre'].items() if root.get(p, 0) - n != 0},
                    'M_next': dict(marking), 'time': '0', 'mass': str(Q(choice['weight']) / denominator)}]
        while True:
            if marking in model['completion_markings']:
                termination = 'completed_first'; first_completion = now; break
            if marking in model.get('legal_noncompletion_markings', []):
                termination = 'other_resolved'; break
            future = [x for x in model['transitions']
                      if all(marking.get(p, 0) >= n for p, n in x['pre'].items())]
            if not future:
                termination = 'unfinished_deadlock'; break
            if len(future) != 1 or future[0]['kind'] != 'timed':
                raise ValueError('unsupported branch shape')
            event = future[0]
            delay = Q(event['interval'][0])
            if delay != Q(event['interval'][1]): raise ValueError('not deterministic')
            when = now + delay
            if when > Q(model['H_A']):
                termination = 'horizon_incomplete'; break
            if len(history) >= int(model['path_budget']):
                termination = 'unresolved_frontier'; break
            previous = dict(marking)
            for p, n in event['pre'].items(): marking[p] -= n
            marking = {p: n for p, n in marking.items() if n}
            intermediate = dict(marking)
            for p, n in event.get('post', {}).items(): marking[p] = marking.get(p, 0) + n
            history.append(event['id']); now = when
            if event.get('label'): observations.append(event['label'])
            if event.get('external_event'): observations.append(event['external_event'])
            records.append({'transition': event['id'], 'M_minus': intermediate, 'M_next': dict(marking),
                            'time': str(when), 'mass': str(Q(choice['weight']) / denominator)})
        leaves.append({'history': history, 'termination': termination, 'mass': str(Q(choice['weight']) / denominator),
                       'time': str(now), 'observations': observations,
                       'first_completion': str(first_completion) if first_completion is not None else None,
                       'sample_termination': termination != 'unresolved_frontier', 'fire_records': records})
    resolved = sum((Q(x['mass']) for x in leaves if x['sample_termination']), Q(0))
    frontier = sum((Q(x['mass']) for x in leaves if not x['sample_termination']), Q(0))
    by_term = {}
    for x in leaves:
        by_term[x['termination']] = str(Q(by_term.get(x['termination'], '0')) + Q(x['mass']))
    return {'status': 'ORACLE_COMPUTED', 'contract': C, 'tex_sha256': TEX, 'model_id': model['id'],
            'leaves': leaves, 'termination_mass': by_term, 'resolved_mass': str(resolved),
            'frontier_mass': str(frontier), 'mass_total': str(resolved + frontier)}
