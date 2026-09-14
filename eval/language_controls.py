"""Original language probes; assistant-reviewed, not a qualified natural corpus.

Twin cases share the rewritten prompt and have incompatible intended policies.
Their purpose is to expose interpretation, not count independent applications.
"""
from collections import Counter
from itertools import product

from label_plane.behavior_pairs import analyze


def cases():
    scaffold = (
        '\nImplement exactly one pure Python function with the following interface: {}. '
        'No imports, I/O, annotations, classes or nested functions. '
        'Return only a JSON object with the single key source_code containing Python source. '
        'Do not use tools.\n'
    )
    coordination = [
        ('coord_and_outside', '(flag a is true or flag b is true) and flag c is true',
         '(a or b) and c', lambda a, b, c: (a or b) and c),
        ('coord_or_outside', 'flag a is true or (flag b is true and flag c is true)',
         'a or (b and c)', lambda a, b, c: a or (b and c)),
    ]
    inventory = []
    for identifier, wording, expression, policy in coordination:
        inventory.append({
            'id': identifier, 'family': 'coordination', 'cluster': 'coordination_twin',
            'role': 'ambiguity_probe', 'source': 'Paska Table III; original example',
            'mutation': 'Remove only the grouping parentheses.',
            'clean': f'Return True exactly when {wording}. Otherwise return False.',
            'defective': 'Return True exactly when flag a is true or flag b is true and flag c is true. Otherwise return False.',
            'scaffold': scaffold.format('evaluate(a, b, c), all inputs Boolean; return Boolean'),
            'tests': [{'args': list(values), 'expected': policy(*values)}
                      for values in product([False, True], repeat=3)],
            'reference_source': f'def evaluate(a, b, c):\n    return {expression}',
        })
    for actor in ('sender', 'receiver'):
        inventory.append({
            'id': 'pronoun_' + actor, 'family': 'pronoun', 'cluster': 'pronoun_twin',
            'role': 'ambiguity_probe', 'source': 'Femmer section 3.2; original example',
            'mutation': f'Replace only "the {actor}" in the response condition with "it".',
            'clean': f'A sender is paired with a receiver. Return True exactly when the {actor} is enabled. Otherwise return False.',
            'defective': 'A sender is paired with a receiver. Return True exactly when it is enabled. Otherwise return False.',
            'scaffold': scaffold.format('evaluate(sender_enabled, receiver_enabled), both inputs Boolean; return Boolean'),
            'tests': [{'args': [sender, receiver], 'expected': sender if actor == 'sender' else receiver}
                      for sender, receiver in product([False, True], repeat=2)],
            'reference_source': f'def evaluate(sender_enabled, receiver_enabled):\n    return {actor}_enabled',
        })
    for case in inventory:
        twin = next(c for c in inventory if c['cluster'] == case['cluster'] and c['id'] != case['id'])
        case['alternatives'] = [{'id': twin['id'], 'tests': twin['tests']}]
    inventory.extend([
        {'id': 'negative_threshold', 'family': 'negative_wording', 'cluster': 'threshold_control',
         'role': 'equivalence_control', 'source': 'Femmer section 3.2; original control',
         'mutation': 'Complement the condition and swap both responses; preserve meaning.',
         'clean': 'For integer x, return True exactly when x is at least 5. Otherwise return False.',
         'defective': 'For integer x, return False exactly when x is less than 5. Otherwise return True.',
         'scaffold': scaffold.format('evaluate(x), integer input; return Boolean'),
         'tests': [{'args': [x], 'expected': x >= 5} for x in range(-1, 11)],
         'reference_source': 'def evaluate(x):\n    return x >= 5',
         'rewritten_reference_source': 'def evaluate(x):\n    return not x < 5',
         'alternatives': []},
        {'id': 'negative_boolean', 'family': 'negative_wording', 'cluster': 'boolean_control',
         'role': 'equivalence_control', 'source': 'Femmer section 3.2; original control',
         'mutation': 'Complement the condition and swap both responses; preserve meaning.',
         'clean': 'Return True exactly when Boolean enabled is true. Otherwise return False.',
         'defective': 'Return False exactly when Boolean enabled is false. Otherwise return True.',
         'scaffold': scaffold.format('evaluate(enabled), Boolean input; return Boolean'),
         'tests': [{'args': [x], 'expected': x} for x in (False, True)],
         'reference_source': 'def evaluate(enabled):\n    return enabled',
         'rewritten_reference_source': 'def evaluate(enabled):\n    return not (enabled == False)',
         'alternatives': []},
    ])
    return inventory


def classify_interpretation(intended, alternatives):
    reports = [intended, *alternatives]
    if any(r.get('status') not in {'passed', 'failed'} for r in reports):
        return 'execution_unknown'
    intended_passed = intended['status'] == 'passed'
    alternative_passed = any(r['status'] == 'passed' for r in alternatives)
    if intended_passed:
        return 'both' if alternative_passed else 'intended_only'
    return 'alternative_only' if alternative_passed else 'neither'


def summarize(manifest, plan, outcomes, interpretations, dispatch_stopped):
    groups = {}
    for cluster in sorted({c['cluster'] for c in manifest['cases']}):
        members = [c for c in manifest['cases'] if c['cluster'] == cluster]
        ids = {c['id'] for c in members}
        groups[cluster] = {
            'role': members[0]['role'], 'family': members[0]['family'],
            'case_ids': sorted(ids),
            'interpretations_by_variant': {
                variant: dict(Counter(label for row, label in zip(outcomes, interpretations, strict=True)
                                      if row['intent_id'] in ids and row['variant'] == variant))
                for variant in ('clean', 'defective')
            },
            'intended_policy_diagnostic': analyze(
                [p for p in plan if p['intent_id'] in ids],
                [o for o in outcomes if o['intent_id'] in ids]),
        }
    return {
        'schema_version': 'constructed-language-controls-summary/v1',
        'scope': manifest['scope'], 'confirmatory_eligible': False,
        'planned_episodes': len(manifest['schedule']), 'groups': groups,
        'interpretations': dict(Counter(interpretations)),
        'dispatch_stopped': dispatch_stopped,
        'interpretation': 'Descriptive original probes only. Twins share rewritten prompts; '
                          'controls are meaning-preserving. No pooled smell-effect estimate, '
                          'independent human validation or H1/H2 decision.',
    }
