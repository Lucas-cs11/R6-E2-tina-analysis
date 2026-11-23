#!/usr/bin/env python3
"""R6-06 subject: psi-specific observation projection and ambiguity witnesses."""

from fractions import Fraction as F

C = 'R6-E2-R6-06-PARTIAL'
TEX = 'a4196145c95812ff19376a5985b6a6f2cf469d432c80836071cad1c8ac174c5a'


def quantized(value, quantum):
    if quantum is None: return str(F(value))
    q = F(quantum); t = F(value); scaled = t / q
    return str(scaled.numerator // scaled.denominator)


def project(path, psi):
    fields = psi['fields']; out = {}
    if 'word' in fields: out['word'] = list(path.get('labels', []))
    if 'completion_time' in fields:
        out['completion_time'] = quantized(path['completion_time'], psi.get('quantum'))
    if 'intermediate_labels' in fields: out['intermediate_labels'] = list(path.get('intermediate_labels', []))
    if 'intermediate_times' in fields:
        out['intermediate_times'] = [quantized(x, psi.get('quantum')) for x in path.get('intermediate_times', [])]
    if 'external_completion' in fields: out['external_completion'] = path.get('external_completion')
    out['intermediate_labels'] = list(path.get('intermediate_labels', []))
    return out


def evaluate(data, psi=None):
    psi = psi or data['psi']
    if not psi.get('prefix_compatible', True):
        return {'status': 'UNSUPPORTED', 'contract': C, 'tex_sha256': TEX, 'verdict': 'PERP', 'witnesses': []}
    paths = [p for p in data['paths'] if p.get('sample_termination', True)]
    projected = [(p, project(p, psi)) for p in paths]
    witnesses = []
    for i, (normal, no) in enumerate(projected):
        if normal['fault']: continue
        for fault, fo in projected:
            if fault['fault'] and no == fo:
                witnesses.append({'normal_path': normal['id'], 'fault_path': fault['id'], 'observation': no})
    if witnesses:
        verdict = '0'
    else:
        # Absence of a witness is not proved by a self-declared boolean flag.
        # This component only decides positive ambiguity from concrete paths.
        verdict = 'PERP'
    return {'status': 'DECIDED' if verdict != 'PERP' else 'UNRESOLVED', 'contract': C,
            'tex_sha256': TEX, 'verdict': verdict, 'witnesses': witnesses}
