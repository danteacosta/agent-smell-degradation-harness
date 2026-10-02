"""Validate proposed source pairs and audit bounded public input registries.

Passing this offline check never supplies independent reviews or freezes a
cohort. Exact text absence is not proof of prospective or pretraining novelty.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_candidate(candidate, root):
    root = Path(root).resolve()
    if candidate.get('selection_frozen') is not False or candidate.get('human_approvals') != 0:
        raise ValueError('draft validation cannot assert a freeze or human approval')
    seen = set()
    for row in candidate['records']:
        identifier = row['intent_id']
        if identifier in seen:
            raise ValueError('duplicate intent')
        seen.add(identifier)
        source = row['source']
        for key, hash_key in [('path', 'sha256'), ('license_path', 'license_sha256')]:
            path = (root / source[key]).resolve()
            if not path.is_relative_to(root) or digest(path) != source[hash_key]:
                raise ValueError('source or license hash mismatch')
        source_text = (root / source['path']).read_text()
        clean, defective = row['variants']['clean'], row['variants']['defective']
        if source_text[source['start_char']:source['end_char']] != clean:
            raise ValueError('source excerpt mismatch')
        manipulation = row['manipulation']; start, end = manipulation['start'], manipulation['end']
        if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(clean)
                or clean[start:end] != manipulation['text']
                or clean[:start] + clean[end:] != defective or not defective.strip()):
            raise ValueError('pair is not the declared single deletion')
        if row['target']['constraint_id'] != identifier + '-c01':
            raise ValueError('constraint identity mismatch')
    return {'pairs_verified': len(seen), 'projects': len({r['project_id'] for r in candidate['records']})}


def _texts(value):
    # Only recorded candidate/model input fields, not full upstream source text.
    fields = {'requirement_text', 'prompt', 'A', 'B', 'C', 'clean', 'defective'}
    if isinstance(value, dict):
        for key, item in value.items():
            if key in fields and isinstance(item, str):
                yield item
            else:
                yield from _texts(item)
    elif isinstance(value, list):
        for item in value:
            yield from _texts(item)


def audit(candidate, root, registry_paths):
    result = validate_candidate(candidate, root)
    matches = {r['intent_id']: [] for r in candidate['records']}
    inventory = []
    normalize = lambda value: ' '.join(value.split())
    for relative in sorted(registry_paths):
        path = Path(root) / relative
        text = path.read_text()
        values = ([json.loads(line) for line in text.splitlines() if line.strip()]
                  if path.suffix == '.jsonl' else json.loads(text))
        inputs = list(_texts(values))
        inventory.append({'path': str(relative), 'sha256': digest(path), 'input_strings': len(inputs)})
        for row in candidate['records']:
            if any(normalize(row['variants']['clean']) in normalize(v) for v in inputs):
                matches[row['intent_id']].append(str(relative))
    return {'schema_version': 'temporal-warning-exposure-audit/v1',
            'status': 'pending_independent_review', 'confirmatory_eligible': False,
            **result, 'registry_files': len(inventory), 'inventory': inventory,
            'exact_or_contained_clean_input_matches': matches,
            'unmatched_is_not_unexposed': True,
            'limitations': ['Whitespace-normalized text audit; paraphrases and omitted-clause exposure can escape it.',
                           'Public and previously used projects; pretraining and external/private usage are unknown.',
                           'Independent review, selection and split freeze remain required.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path.cwd()
    # Exclude this proposed cohort/report, source directories and cached oracle
    # reports with no candidate input fields. Preserve the audited file inventory.
    paths = [p for p in root.glob('data/**/*.json*')
             if p.suffix in {'.json', '.jsonl'} and p not in {args.candidate.resolve(), args.output.resolve()}
             and 'sources' not in p.parts and 'temporal-warning' not in p.name]
    report = audit(json.loads(args.candidate.read_text()), root, [p.relative_to(root) for p in paths])
    args.output.write_text(json.dumps(report, indent=2) + '\n')
