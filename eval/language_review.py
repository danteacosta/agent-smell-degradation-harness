"""Export and verify first-reading forms, without models, results or labels.

Give each reader only one form. Custody files and other forms are not part of
that handoff. Prior exposure must be recorded; exporting proves no blinding.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import stat

from eval import language_controls


INSTRUCTIONS = """# First reading of requirements — individual form

Only this form should be given to this reviewer. Do not inspect other forms,
the custody mapping, or results before recording an interpretation. Declare any
prior exposure to these examples, alternative versions, or their results;
blinding is not assumed for a reviewer who has already seen them.

For each item, describe the rule you understand, other plausible readings,
missing context, confidence, and rationale. Do not implement code: the
implementation instructions below are part of the observed original context.
Missing information may remain inconclusive.

Draft not yet distributed. This is not confirmatory H1/H2 annotation.
"""

GUIDE = """# Candidate review — offline preparation

Give each reviewer only one Markdown/JSON pair from forms/. Never distribute
the whole directory: different versions from the same cluster could influence
interpretations. custodian/ is custodian-only material. Record assignment and
prior exposure, and freeze each independent response before a comparative
review of intent, intervention, and category.

There are six forms with four items each, one per cluster, and ten unique texts.
Ambiguity-cluster texts occur twice; control texts occur three times. The 24
positions are neither participants nor new experimental observations.
Participants, independence, rubric, and distribution remain pending; no human
label is created.

Texts come from the original language_controls_v1 profile. Reviewer forms
contain no model result or answer key. The examples are constructed and have
published results, so prior exposure must be declared. This review does not
admit cases to the corpus, estimate statistical power, or validate H1/H2.

receipt.json is written last and hashes every other file. Its absence indicates
an incomplete export. Verify the bundle before distribution. Use a new private
directory for each review and an immutable file for each returned response;
never overwrite forms or responses.
"""

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FORM_KEYS = {'schema_version', 'status', 'form_id', 'reviewer_id',
             'prior_exposure_declared', 'items'}
ITEM_KEYS = {'item_id', 'observed_requirement_and_interface', 'interpretation',
             'other_plausible_interpretations', 'missing_context', 'confidence',
             'rationale'}
RESPONSE_TEXT_FIELDS = ('interpretation', 'other_plausible_interpretations',
                        'missing_context', 'rationale')


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _json(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode()


def _outside_repository(path: Path, *, existing: bool) -> Path:
    """Resolve a private path and fail closed if it aliases the repository."""
    path = Path(path)
    if not path.is_absolute():
        raise ValueError('private paths must be absolute')
    resolved = path.resolve(strict=existing)
    repository = REPOSITORY_ROOT.resolve()
    if resolved == repository or repository in resolved.parents:
        raise ValueError('private review artifacts must be outside the repository')
    return resolved


def _load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f'invalid JSON artifact: {path.name}') from error
    if not isinstance(value, dict):
        raise ValueError(f'JSON artifact must contain an object: {path.name}')
    return value


def prepare_review(inventory: list[dict], seed: int = 20260914) -> dict[str, bytes]:
    """Prepare the supported original profile before any filesystem mutation."""
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    if len(inventory) != 6 or len({c['id'] for c in inventory}) != 6:
        raise ValueError('unsupported original language profile')
    groups = {}
    for case in inventory:
        if any(not isinstance(case.get(k), str) or not case[k].strip()
               for k in ('id', 'cluster', 'clean', 'defective', 'scaffold')):
            raise ValueError('profile fields must contain text')
        for arm in ('clean', 'defective'):
            prompt = case[arm] + case['scaffold']
            groups.setdefault(case['cluster'], {}).setdefault(prompt, []).append(
                {'case_id': case['id'], 'arm': arm})
    sizes = {cluster: len(texts) for cluster, texts in groups.items()}
    if sizes != {'coordination_twin': 3, 'pronoun_twin': 3,
                 'threshold_control': 2, 'boolean_control': 2}:
        raise ValueError('unsupported original language profile shape')

    rng = random.Random(seed)
    items, by_cluster, custody = {}, {}, []
    for cluster, texts in sorted(groups.items()):
        prompts = sorted(texts)
        rng.shuffle(prompts)
        by_cluster[cluster] = []
        for prompt in prompts:
            item_id = 'R-' + _sha(f'{seed}:{len(items)}'.encode())[:12]
            items[item_id] = {
                'item_id': item_id, 'observed_requirement_and_interface': prompt,
                'interpretation': None, 'other_plausible_interpretations': None,
                'missing_context': None, 'confidence': None, 'rationale': None,
            }
            by_cluster[cluster].append(item_id)
            custody.append({'item_id': item_id, 'cluster': cluster,
                            'prompt_sha256': _sha(prompt.encode()), 'mapping': texts[prompt]})

    files, assignments = {}, []
    for number in range(6):
        selected = [ids[(number + offset) % len(ids)]
                    for offset, ids in enumerate(by_cluster.values())]
        rng.shuffle(selected)
        form_id = 'FORM-' + chr(65 + number)
        rows = [items[item_id] for item_id in selected]
        form = {'schema_version': 'candidate-interpretation-review/v1',
                'status': 'draft_not_distributed', 'form_id': form_id,
                'reviewer_id': None, 'prior_exposure_declared': None, 'items': rows}
        files[f'forms/{form_id}.json'] = _json(form)
        markdown = INSTRUCTIONS
        for row in rows:
            markdown += (f"\n## {row['item_id']}\n\n```text\n"
                         + row['observed_requirement_and_interface']
                         + '\n```\n\nInterpretation:\nOther plausible readings:\n'
                         + 'Missing context:\nConfidence and rationale:\n')
        files[f'forms/{form_id}.md'] = markdown.encode()
        assignments.append({'form_id': form_id, 'item_ids': selected})

    files['custodian/inventory.json'] = _json(inventory)
    files['custodian/manifest.json'] = _json({
        'schema_version': 'candidate-review-custody/v1', 'seed': seed,
        'status': 'not_for_annotators', 'profile': 'language_controls_v1',
        'items': custody, 'assignments': assignments, 'reviewer_assignments': [],
        'inventory_sha256': _sha(files['custodian/inventory.json']),
        'source_sha256': {Path(p).name: _sha(Path(p).read_bytes())
                          for p in (__file__, language_controls.__file__)},
    })
    files['README.md'] = GUIDE.encode()
    files['receipt.json'] = _json({
        'schema_version': 'draft-language-review-receipt/v1',
        'scope': 'constructed_candidate_first_reading_preparation',
        'confirmatory_eligible': False, 'distributed': False,
        'participants': 0, 'human_labels': 0, 'forms': 6, 'items_per_form': 4,
        'unique_prompts': 10, 'files': {name: _sha(raw) for name, raw in files.items()},
    })
    return files


def verify_review_export(output: Path) -> dict:
    """Verify export completeness, hashes, topology, and form/custody linkage."""
    output = _outside_repository(output, existing=True)
    if not output.is_dir():
        raise ValueError('review export must be a directory')
    artifacts = list(output.rglob('*'))
    if any(path.is_symlink() for path in artifacts):
        raise ValueError('review export must not contain symbolic links')
    receipt_path = output / 'receipt.json'
    receipt = _load_json(receipt_path)
    if receipt.get('schema_version') != 'draft-language-review-receipt/v1':
        raise ValueError('unsupported review receipt')
    expected_files = receipt.get('files')
    if not isinstance(expected_files, dict) or not expected_files:
        raise ValueError('receipt must contain file hashes')
    observed_files = {str(path.relative_to(output)) for path in output.rglob('*')
                      if path.is_file() and path.name != 'receipt.json'}
    if observed_files != set(expected_files):
        raise ValueError('review export file inventory does not match receipt')
    for name, expected_sha in expected_files.items():
        path = output / name
        if not isinstance(expected_sha, str) or _sha(path.read_bytes()) != expected_sha:
            raise ValueError(f'review artifact hash mismatch: {name}')
    if stat.S_IMODE(output.stat().st_mode) != 0o700:
        raise ValueError('review export directory must have mode 0700')
    if any(stat.S_IMODE(path.stat().st_mode) != 0o600 for path in artifacts if path.is_file()):
        raise ValueError('review export files must have mode 0600')

    manifest = _load_json(output / 'custodian/manifest.json')
    try:
        inventory = json.loads((output / 'custodian/inventory.json').read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError('invalid custody inventory') from error
    if not isinstance(inventory, list):
        raise ValueError('custody inventory must contain a list')
    if manifest.get('schema_version') != 'candidate-review-custody/v1':
        raise ValueError('unsupported custody manifest')
    if manifest.get('inventory_sha256') != _sha(_json(inventory)):
        raise ValueError('custody inventory hash mismatch')
    custody_items = manifest.get('items')
    assignments = manifest.get('assignments')
    if not isinstance(custody_items, list) or not isinstance(assignments, list):
        raise ValueError('custody manifest is incomplete')
    by_id = {item.get('item_id'): item for item in custody_items
             if isinstance(item, dict) and isinstance(item.get('item_id'), str)}
    if len(by_id) != 10:
        raise ValueError('custody item inventory must contain ten unique prompts')

    form_paths = sorted((output / 'forms').glob('*.json'))
    if len(form_paths) != receipt.get('forms'):
        raise ValueError('unexpected number of review forms')
    assignment_map = {row.get('form_id'): row.get('item_ids') for row in assignments
                      if isinstance(row, dict)}
    seen = set()
    for path in form_paths:
        form = _load_json(path)
        if (set(form) != FORM_KEYS
                or form.get('schema_version') != 'candidate-interpretation-review/v1'):
            raise ValueError(f'invalid reviewer form: {path.name}')
        form_id = form.get('form_id')
        if path.stem != form_id or form.get('status') != 'draft_not_distributed':
            raise ValueError(f'invalid reviewer form identity: {path.name}')
        if form.get('reviewer_id') is not None or form.get('prior_exposure_declared') is not None:
            raise ValueError(f'draft reviewer identity must be empty: {path.name}')
        rows = form.get('items')
        if not isinstance(rows, list) or len(rows) != receipt.get('items_per_form'):
            raise ValueError(f'invalid reviewer form size: {path.name}')
        ids = []
        clusters = set()
        for row in rows:
            if not isinstance(row, dict) or set(row) != ITEM_KEYS:
                raise ValueError(f'invalid reviewer item: {path.name}')
            item_id = row.get('item_id')
            custody = by_id.get(item_id)
            prompt = row.get('observed_requirement_and_interface')
            if custody is None or not isinstance(prompt, str):
                raise ValueError(f'unknown reviewer item: {path.name}')
            if custody.get('prompt_sha256') != _sha(prompt.encode()):
                raise ValueError(f'reviewer prompt does not match custody: {item_id}')
            if any(row.get(field) is not None for field in ITEM_KEYS - {
                    'item_id', 'observed_requirement_and_interface'}):
                raise ValueError(f'draft reviewer answers must be empty: {item_id}')
            ids.append(item_id)
            clusters.add(custody.get('cluster'))
            seen.add(item_id)
        if ids != assignment_map.get(form_id) or len(clusters) != len(rows):
            raise ValueError(f'reviewer assignment mismatch: {form_id}')
    if seen != set(by_id):
        raise ValueError('review forms do not cover the custody inventory')
    return {'status': 'review_export_verified', 'forms': len(form_paths),
            'unique_prompts': len(by_id), 'confirmatory_eligible': False}


def export_review(output: Path, seed: int = 20260914) -> dict:
    files = prepare_review(language_controls.cases(), seed)
    output = _outside_repository(output, existing=False)
    if not output.parent.is_dir():
        raise ValueError('private parent directory must already exist')
    output.mkdir(mode=0o700, parents=False, exist_ok=False)
    for name, raw in files.items():
        target = output / name
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(raw)
        target.chmod(0o600)
    verify_review_export(output)
    return {'status': 'drafts_prepared', 'file_count': len(files),
            'confirmatory_eligible': False, 'distributed': False}


def record_response(bundle: Path, completed_form: Path, output: Path) -> dict:
    """Validate and immutably record one independent reviewer response."""
    bundle = _outside_repository(bundle, existing=True)
    completed_form = _outside_repository(completed_form, existing=True)
    output = _outside_repository(output, existing=False)
    if not output.parent.is_dir():
        raise ValueError('private response parent directory must already exist')
    verification = verify_review_export(bundle)
    submitted = _load_json(completed_form)
    if (set(submitted) != FORM_KEYS
            or submitted.get('schema_version') != 'candidate-interpretation-review/v1'):
        raise ValueError('unsupported completed review form')
    if submitted.get('status') != 'completed':
        raise ValueError('completed review form must have status completed')
    reviewer_id = submitted.get('reviewer_id')
    if not isinstance(reviewer_id, str) or not reviewer_id.strip():
        raise ValueError('reviewer_id must be a non-empty pseudonymous identifier')
    if type(submitted.get('prior_exposure_declared')) is not bool:
        raise ValueError('prior_exposure_declared must be true or false')
    form_id = submitted.get('form_id')
    expected_path = bundle / 'forms' / f'{form_id}.json'
    if not expected_path.is_file():
        raise ValueError('completed form_id is not part of this export')
    expected = _load_json(expected_path)
    rows = submitted.get('items')
    if not isinstance(rows, list) or len(rows) != len(expected['items']):
        raise ValueError('completed form has an unexpected number of items')
    for submitted_row, expected_row in zip(rows, expected['items']):
        if not isinstance(submitted_row, dict) or set(submitted_row) != ITEM_KEYS:
            raise ValueError('completed form contains an invalid item')
        for field in ('item_id', 'observed_requirement_and_interface'):
            if submitted_row.get(field) != expected_row[field]:
                raise ValueError('completed form changed item identity or prompt')
        for field in RESPONSE_TEXT_FIELDS:
            value = submitted_row.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f'{field} must be explicit, using none if applicable')
        if submitted_row.get('confidence') not in {'low', 'medium', 'high'}:
            raise ValueError('confidence must be low, medium, or high')
    receipt_path = bundle / 'receipt.json'
    envelope = {
        'schema_version': 'candidate-interpretation-response/v1',
        'status': 'recorded_independent_response',
        'confirmatory_eligible': False,
        'form_id': form_id,
        'reviewer_id': reviewer_id.strip(),
        'source_form_sha256': _sha(expected_path.read_bytes()),
        'export_receipt_sha256': _sha(receipt_path.read_bytes()),
        'response_sha256': _sha(_json(submitted)),
        'response': submitted,
    }
    with output.open('xb') as stream:
        stream.write(_json(envelope))
    output.chmod(0o600)
    return {'status': 'independent_response_recorded', 'form_id': form_id,
            'reviewer_id': reviewer_id.strip(), 'confirmatory_eligible': False,
            'bundle_forms': verification['forms']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path,
                        help='new directory under an existing private parent')
    parser.add_argument('--seed', type=int, default=20260914)
    parser.add_argument('--verify-existing', action='store_true',
                        help='verify the existing export at --output')
    parser.add_argument('--record-completed', type=Path,
                        help='completed form to validate and record')
    parser.add_argument('--response-output', type=Path,
                        help='new immutable response envelope path')
    args = parser.parse_args()
    if args.verify_existing:
        if args.record_completed or args.response_output:
            parser.error('--verify-existing cannot be combined with response options')
        result = verify_review_export(args.output)
    elif args.record_completed:
        if not args.response_output:
            parser.error('--record-completed requires --response-output')
        result = record_response(args.output, args.record_completed, args.response_output)
    else:
        if args.response_output:
            parser.error('--response-output requires --record-completed')
        result = export_review(args.output, args.seed)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
