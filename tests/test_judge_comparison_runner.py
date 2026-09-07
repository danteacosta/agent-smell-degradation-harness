from pathlib import Path
import json

import pytest

from eval.judge_prompt_comparison import run_comparison

CONFIG = Path('tasks/exploratory_llm_judged_prepilot.example.json')


class Fake:
    def __init__(self, slot, missing_usage=False):
        self.name, self.model = slot.kind, slot.model
        self.last_call_metadata = {}
        self.missing_usage = missing_usage

    def complete(self, request):
        assert request.max_output_tokens == 96
        assert set(request.pair) == {'task_family', 'output_keys'}
        self.last_call_metadata = {'response_model': self.model}
        if not self.missing_usage:
            self.last_call_metadata['usage'] = dict(input_tokens=300, output_tokens=40,
                                                   total_tokens=340, cached_tokens=0)
        result = {'label': 'clean', 'status': 'covered'}
        if request.prompt.startswith('Assess'):
            result['evidence'] = ''
        return json.dumps(result)


def test_preflight_freezes_288_calls_and_both_envelopes_under_one_dollar(tmp_path):
    def forbidden(slot, env):
        pytest.fail('preflight must not create clients')
    report = run_comparison(CONFIG, tmp_path/'run', provider_factory=forbidden)
    assert report['state'] == 'preflight_ready'
    assert report['planned_calls'] == 288
    assert report['budget']['worst_case_reserved_microusd'] <= 1_000_000
    assert report['direct_experiment_envelope_microusd'] <= 1_000_000
    assert not (tmp_path/'run').exists()


def test_live_path_retains_denominators_evidence_failures_and_refuses_overwrite(tmp_path):
    result = run_comparison(CONFIG, tmp_path/'run', live=True,
                            provider_factory=lambda slot, env: Fake(slot))
    assert result['state'] == 'completed'
    assert result['actual_calls'] == 288
    assert result['budget']['pending_attempt_count'] == 0
    for value in result['scores']['configurations'].values():
        assert value['overall']['planned'] == 72
        assert value['overall']['correct'] == 36
        if value['arm'] == 'evidence':
            assert value['overall']['evidence_invalid'] == 72
    manifest = json.loads((tmp_path/'run'/'manifest.json').read_text())
    assert len(manifest['order']) == 288
    assert len((tmp_path/'run'/'responses.jsonl').read_text().splitlines()) == 288
    with pytest.raises(FileExistsError):
        run_comparison(CONFIG, tmp_path/'run', live=True)


@pytest.mark.parametrize('study,planned', [('comparison_v1', 288), ('expanded_v2', 384)])
def test_unknown_usage_stops_after_one_attempt_and_never_retries(tmp_path, study, planned):
    report = run_comparison(CONFIG, tmp_path/'run', live=True,
                            provider_factory=lambda slot, env: Fake(slot, missing_usage=True), study=study)
    assert report['state'] == 'stopped_cost_unverified'
    assert report['actual_calls'] == 1
    assert sum(v['overall']['missing'] for v in report['scores']['configurations'].values()) == planned-1


def test_output_cannot_be_inside_checkout():
    with pytest.raises(ValueError, match='outside'):
        run_comparison(CONFIG, Path.cwd()/'private-comparison-test', live=True)


def test_schema_smoke_is_a_separate_16_call_plan(tmp_path):
    report = run_comparison(CONFIG, tmp_path/'smoke', study='schema_smoke_v2')
    assert report['planned_calls'] == 16
    assert {r['arm'] for r in report['configurations'].values()} == {'evidence_v2'}
    assert report['direct_experiment_envelope_microusd'] < 1_000_000


def test_expanded_study_freezes_384_calls_and_persists_every_occurrence(tmp_path):
    def forbidden(slot, env):
        pytest.fail('offline preflight must not create providers')
    preflight = run_comparison(CONFIG, tmp_path/'run', study='expanded_v2', provider_factory=forbidden)
    assert preflight['planned_calls'] == 384
    assert preflight['state'] == 'preflight_ready'
    assert {r['arm'] for r in preflight['configurations'].values()} == {'historical', 'evidence_v2'}
    assert preflight['direct_experiment_envelope_microusd'] < 1_000_000
    result = run_comparison(CONFIG, tmp_path/'run', study='expanded_v2', live=True,
                            provider_factory=lambda slot, env: Fake(slot))
    assert result['state'] == 'completed'
    assert result['actual_calls'] == 384
    assert len((tmp_path/'run'/'responses.jsonl').read_text().splitlines()) == 384
    for config in result['scores']['configurations'].values():
        assert config['overall']['planned'] == 96
        assert config['overall']['correct'] == 48
        assert config['strata']['expanded_new']['by_operation']['deleted']['correct'] == 0
