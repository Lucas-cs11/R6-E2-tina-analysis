#!/usr/bin/env python3
"""Independent R6-10 alignment reference using separate predicates."""

C = 'R6-E2-R6-10-PARTIAL'
TEX = 'a4196145c95812ff19376a5985b6a6f2cf469d432c80836071cad1c8ac174c5a'


def check(pair):
    left = pair['logical_paths']; right = pair['probability_paths']
    lmap = {x['id']: x for x in left}; rmap = {x['id']: x for x in right}
    shared = set(lmap) & set(rmap)
    omap = pair['observation_map']
    checks = {
        'discrete_structure': len(left) == len(right) == len(shared),
        'fault_domain': pair['logical_H_psi'] == pair['probability_H_psi'] and all(lmap[k]['fault'] == rmap[k]['fault'] for k in shared),
        'persistent_support': all(lmap[k].get('enabling_signature') == rmap[k].get('enabling_signature') for k in shared),
        'completion_domain': all((lmap[k]['completion'], lmap[k]['completion_marking']) == (rmap[k]['completion'], rmap[k]['completion_marking']) for k in shared),
        'external_completion': all(rmap[k].get('external_completion') not in (None, '') for k in rmap),
        'support_alignment': all(tuple(lmap[k]['support']) == tuple(rmap[k]['support']) for k in shared),
        'observation_injective': len({omap[k] for k in lmap}) == len(lmap),
        'observation_projection': all(rmap[k]['observation'] == omap[k] for k in shared),
        'measurable_support': all(x.get('measurable') is True for x in right),
        'no_post_completion_information': pair.get('post_completion_observed') is False,
        'no_hidden_internal_deadlock': pair.get('internal_unobservable_deadlock') is False,
    }
    return {'status': 'THEOREM_APPLICABLE' if all(checks.values()) else 'THEOREM_NOT_APPLICABLE',
            'contract': C, 'tex_sha256': TEX, 'alignment_checks': checks,
            'counterexample_claimed': False}
