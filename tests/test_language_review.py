"""Public packet contracts: isolation, faithful inputs and honest empty labels."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from eval.language_controls import cases
from eval.language_review import (export_review, prepare_review, record_response,
                                  verify_review_export)


def read_forms(output):
    return [json.loads(p.read_text()) for p in sorted((output / 'forms').glob('*.json'))]


def test_each_reader_sees_one_text_per_cluster_with_balanced_coverage(tmp_path):
    output = tmp_path / 'review'
    export_review(output)
    forms = read_forms(output)
    custody = json.loads((output / 'custodian/manifest.json').read_text())
    items = {r['item_id']: r for r in custody['items']}
    assert len(forms) == 6
    assert len(items) == 10
    counts = Counter()
    for form in forms:
        assert len(form['items']) == 4
        selected = [items[r['item_id']] for r in form['items']]
        assert len({r['cluster'] for r in selected}) == 4
        counts.update(r['item_id'] for r in selected)
    for item_id, item in items.items():
        group_size = sum(r['cluster'] == item['cluster'] for r in items.values())
        assert counts[item_id] == 6 // group_size
    assert sum(len(r['mapping']) for r in items.values()) == 12


def test_reviewer_files_preserve_exact_prompts_and_exclude_custody(tmp_path):
    output = tmp_path / 'review'
    export_review(output)
    inventory = cases()
    expected = {c[arm] + c['scaffold'] for c in inventory for arm in ('clean', 'defective')}
    observed = set()
    for form in read_forms(output):
        assert set(form) == {'schema_version', 'status', 'form_id', 'reviewer_id',
                             'prior_exposure_declared', 'items'}
        assert form['reviewer_id'] is None
        assert form['prior_exposure_declared'] is None
        assert form['status'] == 'draft_not_distributed'
        markdown = (output / 'forms' / (form['form_id'] + '.md')).read_text()
        for row in form['items']:
            assert set(row) == {'item_id', 'observed_requirement_and_interface',
                               'interpretation', 'other_plausible_interpretations',
                               'missing_context', 'confidence', 'rationale'}
            prompt = row['observed_requirement_and_interface']
            assert prompt in expected
            assert prompt in markdown
            observed.add(prompt)
            assert all(row[k] is None for k in ('interpretation', 'other_plausible_interpretations',
                                                'missing_context', 'confidence', 'rationale'))
        serialized = json.dumps(form) + markdown
        for case in inventory:
            assert case['id'] not in serialized
            assert case['reference_source'] not in serialized
        assert 'Only this form' in markdown
        assert 'Do not implement' in markdown
    assert observed == expected


def test_extra_inventory_metadata_never_enters_reviewer_files():
    inventory = deepcopy(cases())
    for case in inventory:
        case['provider_response'] = 'SECRET_OBSERVED_RESULT'
    files = prepare_review(inventory, seed=77)
    assert all(b'SECRET_OBSERVED_RESULT' not in raw for name, raw in files.items()
               if name.startswith('forms/'))


def test_export_is_deterministic_and_receipt_covers_every_file(tmp_path):
    first, second = tmp_path / 'a', tmp_path / 'b'
    for output in (first, second):
        result = export_review(output, seed=41)
        assert result['confirmatory_eligible'] is False
        receipt = json.loads((output / 'receipt.json').read_text())
        assert receipt['participants'] == receipt['human_labels'] == 0
        assert receipt['distributed'] is False
        assert set(receipt['files']) == {str(p.relative_to(output)) for p in output.rglob('*')
                                       if p.is_file() and p.name != 'receipt.json'}
        for name, sha in receipt['files'].items():
            assert hashlib.sha256((output / name).read_bytes()).hexdigest() == sha
        assert output.stat().st_mode & 0o777 == 0o700
        assert all(p.stat().st_mode & 0o777 == 0o600 for p in output.rglob('*') if p.is_file())
    for p in first.rglob('*'):
        if p.is_file():
            assert p.read_bytes() == (second / p.relative_to(first)).read_bytes()


def test_verifier_detects_tampering_and_unreceipted_files(tmp_path):
    output = tmp_path / 'review'
    export_review(output)
    assert verify_review_export(output)['status'] == 'review_export_verified'
    form = output / 'forms/FORM-A.md'
    original = form.read_bytes()
    form.write_bytes(original + b'changed')
    with pytest.raises(ValueError, match='hash mismatch'):
        verify_review_export(output)
    form.write_bytes(original)
    extra = output / 'unreceipted.txt'
    extra.write_text('unexpected')
    with pytest.raises(ValueError, match='inventory'):
        verify_review_export(output)


def test_verifier_rejects_symlink_and_relaxed_permissions(tmp_path):
    output = tmp_path / 'review'
    export_review(output)
    target = tmp_path / 'outside.txt'
    target.write_text('outside')
    link = output / 'link.txt'
    link.symlink_to(target)
    with pytest.raises(ValueError, match='symbolic links'):
        verify_review_export(output)
    link.unlink()
    form = output / 'forms/FORM-A.json'
    form.chmod(0o644)
    with pytest.raises(ValueError, match='mode 0600'):
        verify_review_export(output)


def completed_form(output, tmp_path):
    form = json.loads((output / 'forms/FORM-A.json').read_text())
    form['status'] = 'completed'
    form['reviewer_id'] = 'reviewer-01'
    form['prior_exposure_declared'] = False
    for item in form['items']:
        item.update({
            'interpretation': 'The stated behavior is required.',
            'other_plausible_interpretations': 'none',
            'missing_context': 'none identified',
            'confidence': 'high',
            'rationale': 'This reading follows the explicit condition.',
        })
    path = tmp_path / 'completed.json'
    path.write_text(json.dumps(form))
    return path


def test_completed_response_is_bound_to_original_form_and_immutable(tmp_path):
    output = tmp_path / 'review'
    export_review(output)
    completed = completed_form(output, tmp_path)
    recorded = tmp_path / 'responses' / 'FORM-A-reviewer-01.json'
    recorded.parent.mkdir()
    result = record_response(output, completed, recorded)
    assert result == {'status': 'independent_response_recorded', 'form_id': 'FORM-A',
                      'reviewer_id': 'reviewer-01', 'confirmatory_eligible': False,
                      'bundle_forms': 6}
    envelope = json.loads(recorded.read_text())
    assert envelope['schema_version'] == 'candidate-interpretation-response/v1'
    assert envelope['confirmatory_eligible'] is False
    assert envelope['response']['items'][0]['confidence'] == 'high'
    assert recorded.stat().st_mode & 0o777 == 0o600
    before = recorded.read_bytes()
    with pytest.raises(FileExistsError):
        record_response(output, completed, recorded)
    assert recorded.read_bytes() == before


@pytest.mark.parametrize('mutation, match', [
    (lambda form: form['items'][0].update({'observed_requirement_and_interface': 'changed'}),
     'changed item identity'),
    (lambda form: form['items'][0].update({'interpretation': ''}), 'interpretation'),
    (lambda form: form['items'][0].update({'confidence': 'certain'}), 'confidence'),
    (lambda form: form.update({'prior_exposure_declared': None}), 'prior_exposure'),
])
def test_completed_response_rejects_changed_or_incomplete_answers(tmp_path, mutation, match):
    output = tmp_path / 'review'
    export_review(output)
    completed = completed_form(output, tmp_path)
    form = json.loads(completed.read_text())
    mutation(form)
    completed.write_text(json.dumps(form))
    with pytest.raises(ValueError, match=match):
        record_response(output, completed, tmp_path / 'response.json')


@pytest.mark.parametrize('symlink', [False, True])
def test_existing_destination_is_never_modified(tmp_path, symlink):
    original = tmp_path / 'original'
    original.mkdir()
    sentinel = original / 'keep.txt'
    sentinel.write_text('user work')
    destination = tmp_path / 'output' if symlink else original
    if symlink:
        destination.symlink_to(original, target_is_directory=True)
    with pytest.raises(FileExistsError):
        export_review(destination)
    assert sentinel.read_text() == 'user work'
    assert sorted(p.name for p in original.iterdir()) == ['keep.txt']


def test_export_rejects_relative_and_repository_paths(tmp_path):
    with pytest.raises(ValueError, match='absolute'):
        export_review(Path('relative-review'))
    repository_output = Path(__file__).resolve().parents[1] / 'private-review'
    with pytest.raises(ValueError, match='outside the repository'):
        export_review(repository_output)
    assert not repository_output.exists()


def test_unsupported_profile_shape_is_rejected_before_export():
    with pytest.raises(ValueError, match='profile'):
        prepare_review(cases()[:-1], seed=42)


def test_command_line_prepares_an_offline_draft_and_rejects_reuse(tmp_path):
    output = tmp_path / 'cli'
    command = [sys.executable, '-m', 'eval.language_review', '--output', str(output),
               '--seed', '123']
    run = subprocess.run(command, capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    assert json.loads(run.stdout)['status'] == 'drafts_prepared'
    before = (output / 'receipt.json').read_bytes()
    repeated = subprocess.run(command, capture_output=True, text=True)
    assert repeated.returncode != 0
    assert (output / 'receipt.json').read_bytes() == before

    verified = subprocess.run(
        [sys.executable, '-m', 'eval.language_review', '--output', str(output),
         '--verify-existing'], capture_output=True, text=True)
    assert verified.returncode == 0, verified.stderr
    assert json.loads(verified.stdout)['status'] == 'review_export_verified'

    completed = completed_form(output, tmp_path)
    response = tmp_path / 'cli-response.json'
    recorded = subprocess.run(
        [sys.executable, '-m', 'eval.language_review', '--output', str(output),
         '--record-completed', str(completed), '--response-output', str(response)],
        capture_output=True, text=True)
    assert recorded.returncode == 0, recorded.stderr
    assert json.loads(recorded.stdout)['status'] == 'independent_response_recorded'
    assert response.is_file()
