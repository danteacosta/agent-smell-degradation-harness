"""Versioned context-preserving controls and a completeness-instruction candidate."""
from __future__ import annotations

from eval.pilot_preparation import digest
from label_plane import addressed_judge, scoped_judge

LAYOUT_VERSION = 'whole-source-context/v2'
PROMPT_VERSION = 'scope-addressed/v5-dev'
COMPLETENESS = ('Check every required part, including actor, interface and conditions. '
                'Related functionality does not supply an unspecified part. '
                'With complete scope, missing support for a required part is omitted. '
                'Uncertain requires genuinely ambiguous wording, not incomplete support.')


def build_cases(seeds):
    """Keep context contiguous; do not edit frozen constructors or their oracles."""
    cases = scoped_judge.build_cases(seeds)
    by_source = {seed['source_intent_id']: seed for seed in seeds}
    for case in cases:
        seed = by_source[case['oracle']['source_intent_id']]
        operation = case['oracle']['operation']
        if operation in {'distributed_complete', 'long_omission'}:
            clauses = list(seed['clauses'])
            if operation == 'long_omission':
                clauses[seed['target_index']] = ''
            case['item']['criteria'] = clauses[0] + '\n\n' + seed['context'] + '\n\n' + '\n'.join(clauses[1:])
            addressed_judge.checked_item(case['item'])
        case['id'] = digest([LAYOUT_VERSION, case['id']])[:24]
    return cases


def build_prompt(item, arm):
    if arm not in {'v4', 'v5'}:
        raise ValueError('invalid_arm')
    prompt = addressed_judge.build_prompt(item)
    return prompt if arm == 'v4' else prompt.replace('Return JSON only:', COMPLETENESS + '\nReturn JSON only:', 1)


def parse_response(raw, item, arm):
    if arm not in {'v4', 'v5'}:
        raise ValueError('invalid_arm')
    result = addressed_judge.parse_response(raw, item)
    if arm == 'v5':
        result['prompt_version'] = PROMPT_VERSION
    return result
