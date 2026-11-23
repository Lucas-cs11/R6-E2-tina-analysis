#!/usr/bin/env python3
"""R6-03 subject: finite deterministic TPN execution with a complete mass ledger."""

from fractions import Fraction as F

C = 'R6-E2-R6-03-PARTIAL'
TEX = 'a4196145c95812ff19376a5985b6a6f2cf469d432c80836071cad1c8ac174c5a'


class InputError(Exception):
    pass


def table(model):
    return {t['id']: t for t in model['transitions']}


def enabled(model, marking):
    return sorted(t['id'] for t in model['transitions']
                  if all(marking.get(p, 0) >= n for p, n in t['pre'].items()))


def fire(model, marking, name):
    t = table(model)[name]
    minus = dict(marking)
    for p, n in t['pre'].items():
        minus[p] = minus.get(p, 0) - n
        if minus[p] == 0: del minus[p]
    after = dict(minus)
    for p, n in t.get('post', {}).items(): after[p] = after.get(p, 0) + n
    return minus, after


def terminal(model, marking):
    if marking in model['completion_markings']: return 'completed_first'
    if marking in model.get('legal_noncompletion_markings', []): return 'other_resolved'
    return None


def advance(model, state):
    term = terminal(model, state['marking'])
    if term is not None:
        if state['first_completion'] is None and term == 'completed_first':
            state['first_completion'] = state['time']
        return leaf(model, state, term)
    names = enabled(model, state['marking'])
    if not names:
        return leaf(model, state, 'unfinished_deadlock')
    immediate = [n for n in names if table(model)[n]['kind'] == 'immediate']
    if immediate:
        raise InputError('chained immediate transitions outside declared exclusive-root domain')
    timed = [n for n in names if table(model)[n]['kind'] == 'timed']
    if len(timed) != 1:
        raise InputError('declared domain requires exactly one enabled deterministic timed transition')
    name = timed[0]
    t = table(model)[name]
    if F(t['interval'][0]) != F(t['interval'][1]):
        raise InputError('only fixed-delay intervals are supported')
    event_time = state['time'] + F(t['interval'][0])
    # H_A incompletion is semantic and is assessed before a budget refusal.
    if event_time > F(model['H_A']):
        return leaf(model, state, 'horizon_incomplete')
    if len(state['history']) >= int(model['path_budget']):
        return leaf(model, state, 'unresolved_frontier')
    minus, after = fire(model, state['marking'], name)
    state['history'].append(name)
    state['time'] = event_time
    state['marking'] = after
    if t.get('label'): state['observations'].append(t['label'])
    if t.get('external_event'): state['observations'].append(t['external_event'])
    state['fire_records'].append({'transition': name, 'M_minus': minus, 'M_next': after,
                                  'time': str(event_time), 'mass': str(state['mass'])})
    return advance(model, state)


def leaf(model, state, termination):
    state['termination'] = termination
    state['sample_termination'] = termination != 'unresolved_frontier'
    state['resolved'] = termination != 'unresolved_frontier'
    return state


def execute(model):
    roots = [t for t in model['transitions'] if t['kind'] == 'immediate'
             and all(model['initial_marking'].get(p, 0) >= n for p, n in t['pre'].items())]
    if not roots: raise InputError('no enabled immediate root')
    total_weight = sum(F(t.get('weight', '0')) for t in roots)
    if total_weight <= 0: raise InputError('invalid root weights')
    leaves = []
    for root in roots:
        mass = F(root.get('weight', '0')) / total_weight
        minus, marking = fire(model, model['initial_marking'], root['id'])
        state = {'mass': mass, 'marking': marking, 'history': [root['id']], 'time': F(0),
                 'observations': [], 'first_completion': None,
                 'fire_records': [{'transition': root['id'], 'M_minus': minus, 'M_next': marking,
                                   'time': '0', 'mass': str(mass)}]}
        leaves.append(advance(model, state))
    return report(model, leaves)


def report(model, leaves):
    resolved = sum((x['mass'] for x in leaves if x['resolved']), F(0))
    frontier = sum((x['mass'] for x in leaves if not x['resolved']), F(0))
    total = resolved + frontier
    by_term = {}
    for x in leaves:
        by_term[x['termination']] = str(F(by_term.get(x['termination'], '0')) + x['mass'])
    ledger = [{'history': x['history'], 'termination': x['termination'], 'mass': str(x['mass']),
               'time': str(x['time']), 'observations': x['observations'],
               'first_completion': str(x['first_completion']) if x['first_completion'] is not None else None,
               'sample_termination': x['sample_termination'], 'fire_records': x['fire_records']}
              for x in leaves]
    return {'status': 'COMPUTED', 'contract': C, 'tex_sha256': TEX, 'model_id': model['id'],
            'leaves': ledger, 'termination_mass': by_term,
            'resolved_mass': str(resolved), 'frontier_mass': str(frontier),
            'mass_total': str(total), 'H0_H1_partition': 'not assessed without fault window',
            'invariant': 'resolved_mass + frontier_mass == 1'}
