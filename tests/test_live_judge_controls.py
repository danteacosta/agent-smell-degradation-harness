from pathlib import Path
import subprocess

import pytest

from eval.live_judge_controls import run_controls


CONFIG = Path('tasks/exploratory_llm_judged_prepilot.example.json')


class Fake:
    def __init__(self, slot, *, missing_usage=False):
        self.name = slot.kind
        self.model = slot.model
        self.missing_usage = missing_usage
        self.last_call_metadata = {}
        self.calls = 0

    def complete(self, request):
        self.calls += 1
        assert set(request.pair) == {'task_family', 'output_keys'}
        assert 'oracle' not in request.prompt
        self.last_call_metadata = {'response_model': self.model}
        if not self.missing_usage:
            self.last_call_metadata['usage'] = {'input_tokens': 100, 'output_tokens': 10, 'cached_tokens': 0, 'total_tokens': 110}
        return '{"label":"clean","status":"covered"}'


def test_preflight_constructs_no_provider_and_exposes_72_call_plan(tmp_path):
    def forbidden(slot, env):
        pytest.fail('preflight must not construct a provider')
    report = run_controls(CONFIG, tmp_path/'run', provider_factory=forbidden)
    assert report['state'] == 'preflight_ready'
    assert report['planned_control_calls'] == 72
    assert report['budget']['worst_case_reserved_microusd'] == 988200


def test_constant_clean_live_path_records_72_calls_and_negative_misses(tmp_path):
    result = run_controls(CONFIG, tmp_path/'run', live=True,
                          provider_factory=lambda slot, env: Fake(slot))
    assert result['state'] == 'completed'
    assert result['actual_calls'] == 72
    assert result['budget']['observed_attempt_count'] == 72
    for report in result['scores']['configurations'].values():
        assert report['correct'] == 18
        assert report['false_covered'] == 18
    assert len((tmp_path/'run'/'responses.jsonl').read_text().splitlines()) == 72
    with pytest.raises(FileExistsError):
        run_controls(CONFIG, tmp_path/'run', live=True)


def test_unknown_usage_stops_after_one_call_retaining_missing_denominators(tmp_path):
    result = run_controls(CONFIG, tmp_path/'run', live=True,
                          provider_factory=lambda slot, env: Fake(slot, missing_usage=True))
    assert result['state'] == 'stopped_cost_unverified'
    assert result['actual_calls'] == 1
    assert sum(r['missing'] for r in result['scores']['configurations'].values()) == 71
    assert result['scores']['confirmatory_eligible'] is False


def test_reconciled_provider_error_stops_without_claiming_run_is_running(tmp_path):
    class ReconciledError(Fake):
        def complete(self, request):
            super().complete(request)
            raise RuntimeError('provider failed after reporting usage')

    result = run_controls(CONFIG, tmp_path/'run', live=True,
                          provider_factory=lambda slot, env: ReconciledError(slot))
    assert result['state'] == 'stopped_provider_error'
    assert result['actual_calls'] == 1
    assert result['budget']['observed_attempt_count'] == 1


def test_provider_identity_rejection_does_not_count_a_network_call(tmp_path):
    def wrong_identity(slot, env):
        provider = Fake(slot)
        provider.model = 'unapproved-model'
        return provider

    result = run_controls(CONFIG, tmp_path/'run', live=True, provider_factory=wrong_identity)
    assert result['state'] == 'stopped_cost_unverified'
    assert result['actual_calls'] == 0


def test_private_output_cannot_be_written_inside_a_different_checkout(tmp_path):
    repo = tmp_path/'another-checkout'
    repo.mkdir()
    subprocess.run(['git', 'init', '--quiet', str(repo)], check=True)
    with pytest.raises(ValueError, match='outside'):
        run_controls(CONFIG, repo/'private-run', live=True,
                     provider_factory=lambda slot, env: Fake(slot))
    assert not (repo/'private-run').exists()
