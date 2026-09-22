import json

import pytest

from scripts.criteria_consensus import CATEGORIES, consensus, parse_generation, parse_judgment


def judgment(label='supported', evidence='about'):
    return {'categories': {key: {'label': label, 'evidence': evidence,
                                'reason': 'Explicit obligation.'} for key in CATEGORIES},
            'additions': [], 'scope': 'collective_or_unspecified'}


@pytest.mark.parametrize('text', ['{"criteria":["x"],"criteria":["y"],"uncertainties":[]}',
                                  '{"criteria":[NaN],"uncertainties":[]}',
                                  '{"criteria":[],"uncertainties":[]}',
                                  '```json\n{}\n```'])
def test_generation_rejects_invalid_contract(text):
    with pytest.raises(ValueError):
        parse_generation(text)


def test_uncertainty_is_not_admissible_evidence():
    data = {'criteria': ['about'], 'uncertainties': ['links']}
    vote = judgment(evidence='links')
    with pytest.raises(ValueError):
        parse_judgment(json.dumps(vote), data)


def test_absent_requires_null_evidence_and_reason():
    vote = judgment('absent', None)
    assert parse_judgment(json.dumps(vote), {'criteria': ['about']}) == vote
    vote['categories']['links']['reason'] = ''
    with pytest.raises(ValueError):
        parse_judgment(json.dumps(vote), {'criteria': ['about']})


def test_consensus_does_not_convert_two_votes_or_majority_to_unanimity():
    assert consensus(['supported', 'supported', None]) == {'primary': None, 'sensitivity': None}
    assert consensus(['supported', 'supported', 'absent']) == {'primary': None, 'sensitivity': 'supported'}
    assert consensus(['supported'] * 3) == {'primary': 'supported', 'sensitivity': 'supported'}
    assert consensus(['supported', 'absent', 'unclear']) == {'primary': None, 'sensitivity': None}


@pytest.fixture
def packet(tmp_path, monkeypatch):
    from scripts import criteria_consensus as panel
    source = tmp_path / 'source'
    source.mkdir()
    source_text = 'Original about and version command requirement.'
    panel.write(source / 'source-review/mapping/source.txt', source_text.encode())
    panel.write(source / 'source-review/mapping/LICENSE', b'License fixture')
    panel.write(source / 'source-review/mapping/NOTICE', b'Notice fixture')
    schedule = []
    for index in range(9):
        path = f'requests/position-{index + 1:02}.json'
        prompt = f'Frozen requirement prompt {index}'
        panel.write(source / path, {'prompt': prompt})
        schedule.append({'variant': ('A', 'B', 'C')[index % 3], 'slot': f'position-{index+1:02}',
                         'request_path': path, 'prompt_sha256': panel.digest(prompt.encode())})
    panel.write(source / 'custodian/schedule.json', schedule)
    panel.write(source / 'receipt.json', {'files': panel.inventory(source)})
    monkeypatch.setattr(panel, 'SOURCE_RECEIPT', panel.digest((source / 'receipt.json').read_bytes()))
    binary = tmp_path / 'codex'
    binary.write_text('#!/bin/sh\nprintf "test-cli\\n"\n')
    binary.chmod(0o700)
    output = tmp_path / 'pilot'
    before = panel.inventory(source)
    panel.prepare(source, output, binary)
    assert panel.inventory(source) == before
    return output


def fake_provider(*, fail_call=None, invalid_call=None, calibration_failure=False):
    from scripts import criteria_consensus as panel
    prompts = []

    class Provider:
        last_call_metadata = {'billing_mode': 'chatgpt_subscription'}

        def __init__(self, **kwargs):
            self.model = kwargs['model']
            assert kwargs['timeout_seconds'] == 180

        def complete(self, request):
            prompts.append((self.model, request.prompt))
            assert request.pair == {}
            assert request.max_output_tokens is None
            if len(prompts) == fail_call:
                raise RuntimeError('simulated infrastructure failure')
            if len(prompts) == invalid_call:
                return 'not JSON'
            if 'Fixtures JSON:\n' in request.prompt:
                cases = json.loads(request.prompt.split('Fixtures JSON:\n')[1])
                assert all(set(case) == {'id', 'artifact'} for case in cases)
                expected_cases = {case['id']: case for case in panel.fixtures()}
                values = {}
                for case in cases:
                    vote = judgment()
                    for category, label in expected_cases[case['id']]['expected'].items():
                        vote['categories'][category] = {'label': label,
                            'evidence': case['artifact']['criteria'][0] if label != 'absent' else None,
                            'reason': 'Fixture evidence.'}
                    if case['id'] == 'fixture-08':
                        vote['additions'] = ['Unsupported URL and exit code.']
                    values[case['id']] = vote
                if calibration_failure:
                    values['fixture-01']['categories']['links'] = {
                        'label': 'absent', 'evidence': None, 'reason': 'Deliberately wrong.'}
                return json.dumps(values)
            if 'Artifact JSON:\n' in request.prompt:
                artifact = json.loads(request.prompt.split('Artifact JSON:\n')[1])
                assert 'variant' not in artifact
                return json.dumps(judgment(evidence=artifact['criteria'][0]))
            return json.dumps({'criteria': ['All six obligations are explicitly stated.'], 'uncertainties': []})
    return Provider, prompts


def test_successful_run_is_bounded_preserves_frozen_prompts_and_cannot_repeat(packet):
    from scripts import criteria_consensus as panel
    provider, prompts = fake_provider()
    report = panel.run(packet, provider)
    assert report['calls_attempted'] == 39
    assert report['generations']['valid'] == 9
    assert report['judgments']['valid'] == 27
    assert all(row['resolved'] == 3 for row in report['by_variant_category'])
    assert [prompt for model, prompt in prompts if model == panel.GENERATOR] == [
        f'Frozen requirement prompt {index}' for index in range(9)]
    assert all(model not in prompt for model, prompt in prompts)
    panel.verify(packet)
    assert packet.stat().st_mode & 0o777 == 0o700
    assert all(path.stat().st_mode & 0o777 == 0o600 for path in packet.rglob('*') if path.is_file())
    with pytest.raises(FileExistsError):
        panel.run(packet, provider)
    assert len(prompts) == 39


def test_calibration_failure_retains_raw_response_and_stops_before_generation(packet):
    from scripts import criteria_consensus as panel
    provider, prompts = fake_provider(calibration_failure=True)
    report = panel.run(packet, provider)
    assert len(prompts) == 1
    assert report['stop_reason'] == 'calibration_failed'
    assert report['generations']['attempted'] == report['judgments']['attempted'] == 0
    assert (packet / 'calls/calibration-1-response.txt').is_file()
    assert all(row['supported_fraction_bounds'] == [0, 1] for row in report['by_variant_category'])
    panel.verify(packet)


def test_provider_failure_stops_every_remaining_slot_without_retry(packet):
    from scripts import criteria_consensus as panel
    provider, prompts = fake_provider(fail_call=5)
    report = panel.run(packet, provider)
    assert len(prompts) == 5
    assert report['stop_reason'] == 'provider_infrastructure_error'
    assert report['generations']['attempted'] == 2
    assert report['generations']['valid'] == 1
    assert report['judgments']['attempted'] == 0
    panel.verify(packet)


def test_invalid_generation_retains_slot_and_skips_only_its_three_judgments(packet):
    from scripts import criteria_consensus as panel
    provider, prompts = fake_provider(invalid_call=4)
    report = panel.run(packet, provider)
    assert len(prompts) == 36
    assert report['generations']['planned'] == 9
    assert report['generations']['valid'] == 8
    assert report['judgments']['planned'] == 27
    assert report['judgments']['attempted'] == 24
    assert sum(row['unresolved'] for row in report['by_variant_category']) == 6


def test_invalid_judge_does_not_create_two_vote_primary_or_sensitivity(packet):
    from scripts import criteria_consensus as panel
    provider, _ = fake_provider(invalid_call=13)
    report = panel.run(packet, provider)
    assert report['calls_attempted'] == 39
    assert report['judgments']['valid'] == 26
    assert sum(row['primary'] is None for row in report['category_rows']) == 6
    assert sum(row['sensitivity'] is None for row in report['category_rows']) == 6


def test_changed_frozen_payload_rejected_before_any_calls(packet):
    from scripts import criteria_consensus as panel
    (packet / 'frozen/rubric.txt').write_text('Changed rubric')
    provider, prompts = fake_provider()
    with pytest.raises(ValueError, match='receipt inventory mismatch'):
        panel.run(packet, provider)
    assert not prompts
    assert not (packet / 'run-started.json').exists()


def test_unanimous_unclear_retains_coverage_uncertainty(packet):
    from scripts import criteria_consensus as panel
    provider, _ = fake_provider()
    panel.run(packet, provider)
    path = packet / 'results.json'
    state = json.loads(path.read_text())
    for judgments in state['judgments'].values():
        for result in judgments.values():
            for entry in result['value']['categories'].values():
                entry['label'] = 'unclear'
    # Simulate an entirely ambiguous collection in a disposable test packet.
    path.write_text(json.dumps(state))
    report = panel.analyze(packet)
    assert all(row['supported_fraction_bounds'] == [0, 1] for row in report['by_variant_category'])
    assert all(row['resolved'] == 3 and row['resolved_coverage'] == 0
               for row in report['by_variant_category'])


def test_json_overflow_is_rejected():
    from scripts.criteria_consensus import strict_json
    with pytest.raises(ValueError, match='nonfinite'):
        strict_json('{"number":1e999}')


def test_symlink_in_frozen_packet_rejected_without_calls(packet):
    from scripts import criteria_consensus as panel
    link = packet / 'frozen/alias'
    link.symlink_to(packet / 'frozen/rubric.txt')
    provider, prompts = fake_provider()
    with pytest.raises(ValueError, match='symlink'):
        panel.run(packet, provider)
    assert not prompts


def test_nonprivate_packet_rejected_without_calls(packet):
    from scripts import criteria_consensus as panel
    packet.chmod(0o755)
    provider, prompts = fake_provider()
    with pytest.raises(ValueError, match='private'):
        panel.run(packet, provider)
    assert not prompts


def test_surrogate_output_is_retained_and_invalid_without_aborting_receipt(packet):
    from scripts import criteria_consensus as panel
    provider, _ = fake_provider()
    class InvalidUnicode(provider):
        def complete(self, request):
            if self.model == panel.GENERATOR:
                return '{"criteria":["\\ud800"],"uncertainties":[]}'.replace('\\ud800', '\ud800')
            return super().complete(request)
    report = panel.run(packet, InvalidUnicode)
    assert report['generations']['statuses'] == {'invalid_output': 9}
    assert report['judgments']['attempted'] == 0
    panel.verify(packet)
