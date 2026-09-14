import pytest
import json
from types import SimpleNamespace


def test_original_contracts_discriminate_target_and_preserved_condition():
    from eval.codex_demo import cases
    from eval.codegen_sandbox import evaluate_trusted_fixture
    controls = {
        'access': ("def evaluate(authorized):\n    return 'allow' if authorized else 'deny'", "def evaluate(authorized):\n    return 'allow'"),
        'discount': ("def evaluate(total):\n    return min(total * 0.1, 7)", "def evaluate(total):\n    return total * 0.1"),
        'token': ("def evaluate(age, used):\n    return age < 15 and not used", "def evaluate(age, used):\n    return age < 15"),
    }
    for case in cases():
        correct, omitted = controls[case['id']]
        assert evaluate_trusted_fixture(correct, case['tests'])['status'] == 'passed'
        assert evaluate_trusted_fixture(omitted, case['tests'])['status'] == 'failed'


def test_prepare_freezes_order_and_common_oracles_and_excludes_them_from_prompts(tmp_path):
    from eval.codex_demo import prepare
    manifest = prepare(tmp_path / 'run', model='test-model', replications=3)
    assert len(manifest['schedule']) == 18
    assert manifest['confirmatory_eligible'] is False
    assert manifest['scope'] == 'original_contract_demonstration'
    for case in manifest['cases']:
        assert case['clean'].startswith(case['defective'])
        assert 'expected' not in case['scaffold']
    with pytest.raises(FileExistsError):
        prepare(tmp_path / 'run', model='test-model', replications=3)


def test_invalid_collection_size_rejected_before_output(tmp_path):
    from eval.codex_demo import prepare
    for count in (0, 6, True):
        with pytest.raises(ValueError):
            prepare(tmp_path / 'run', model='test-model', replications=count)
        assert not (tmp_path / 'run').exists()


@pytest.mark.parametrize('answer', ['null', '42', '[{}]'])
def test_invalid_json_shape_is_retained_and_remaining_calls_continue(tmp_path, monkeypatch, answer):
    from eval import codex_demo as demo
    class Provider:
        last_call_metadata = {}
        def __init__(self, **kwargs): pass
        def complete(self, request): return answer
    monkeypatch.setattr(demo, 'CodexCLIProvider', Provider)
    monkeypatch.setattr(demo.subprocess, 'run', lambda *a, **k: SimpleNamespace(returncode=0, stdout='{"status":"smoke_passed"}'))
    executable = tmp_path / 'cli'
    executable.write_text('fixture only')
    report = demo.run(tmp_path / 'run', model='fixture', executable=str(executable), replications=1)
    assert report['complete_pairs'] == 0
    assert report['status_counts']['clean'] == {'not_executed': 3}
    assert len(list((tmp_path / 'run').glob('episode-*/outcome.json'))) == 6
