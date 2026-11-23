#!/usr/bin/env python3
"""R6-10 cross-layer alignment checker (subject, evidence only)."""

C = 'R6-E2-R6-10-PARTIAL'
TEX = 'a4196145c95812ff19376a5985b6a6f2cf469d432c80836071cad1c8ac174c5a'


def check(pair):
    logical = {p['id']: p for p in pair['logical_paths']}
    probability = {p['id']: p for p in pair['probability_paths']}
    checks = {}
    checks['discrete_structure'] = set(logical) == set(probability)
    checks['fault_domain'] = (pair['logical_H_psi'] == pair['probability_H_psi']
        and all(logical[k]['fault'] == probability[k]['fault'] for k in logical.keys() & probability.keys()))
    checks['persistent_support'] = all(logical[k].get('enabling_signature') == probability[k].get('enabling_signature') for k in logical.keys() & probability.keys())
    checks['completion_domain'] = all(logical[k]['completion'] == probability[k]['completion']
        and logical[k]['completion_marking'] == probability[k]['completion_marking'] for k in logical.keys() & probability.keys())
    checks['external_completion'] = all(bool(probability[k].get('external_completion')) for k in probability)
    checks['support_alignment'] = all(logical[k]['support'] == probability[k]['support'] for k in logical.keys() & probability.keys())
    observations = [pair['observation_map'][k] for k in sorted(logical)]
    checks['observation_injective'] = len(observations) == len(set(observations))
    checks['observation_projection'] = all(probability[k]['observation'] == pair['observation_map'][k] for k in logical.keys() & probability.keys())
    checks['measurable_support'] = all(p.get('measurable') is True for p in pair['probability_paths'])
    checks['no_post_completion_information'] = not pair.get('post_completion_observed', False)
    checks['no_hidden_internal_deadlock'] = not pair.get('internal_unobservable_deadlock', False)
    applicable = all(v for k, v in checks.items() if k != 'support_alignment')
    return {'status': 'THEOREM_APPLICABLE' if applicable else 'THEOREM_NOT_APPLICABLE',
            'contract': C, 'tex_sha256': TEX, 'alignment_checks': checks,
            'counterexample_claimed': False,
            'reason': 'all sufficient conditions hold' if applicable else 'sufficient conditions not established; no theorem counterexample inferred'}
