import json
from datetime import datetime, timezone
from itertools import product
from types import SimpleNamespace

import pytest

from eval import codex_demo


def inventory():
    from eval.language_controls import cases
    return cases()


def test_twins_share_rewritten_prompt_but_preserve_distinct_complete_truth_tables():
    cases = inventory()
    assert len(cases) == 6
    for family, domain_size in [('coordination', 8), ('pronoun', 4)]:
        twins = [c for c in cases if c['family'] == family]
        assert len(twins) == 2
        assert twins[0]['defective'] + twins[0]['scaffold'] == twins[1]['defective'] + twins[1]['scaffold']
        assert twins[0]['clean'] != twins[1]['clean']
        assert twins[0]['cluster'] == twins[1]['cluster']
        assert twins[0]['tests'] != twins[1]['tests']
        for c in twins:
            assert len(c['tests']) == domain_size
            assert c['alternatives'][0]['tests'] == next(x['tests'] for x in twins if x['id'] != c['id'])
    coord = [c for c in cases if c['family'] == 'coordination']
    assert {tuple(t['args']) for t in coord[0]['tests']} == set(product([False, True], repeat=3))
    assert [t['expected'] for t in coord[0]['tests'] if t['args'] == [True, False, False]] == [False]
    assert [t['expected'] for t in coord[1]['tests'] if t['args'] == [True, False, False]] == [True]


def test_original_reference_and_equivalent_controls_satisfy_behavior_contracts():
    from eval.codegen_sandbox import evaluate_trusted_fixture
    for c in inventory():
        assert evaluate_trusted_fixture(c['reference_source'], c['tests'])['status'] == 'passed'
        if c['role'] == 'equivalence_control':
            assert c['alternatives'] == []
            assert evaluate_trusted_fixture(c['rewritten_reference_source'], c['tests'])['status'] == 'passed'
        else:
            assert evaluate_trusted_fixture(c['reference_source'], c['alternatives'][0]['tests'])['status'] == 'failed'


def test_profile_freezes_labels_without_calling_it_a_confirmatory_corpus(tmp_path):
    manifest = codex_demo.prepare(tmp_path / 'run', model='fixture', replications=2,
                                  profile='language_controls_v1')
    assert manifest['scope'] == 'constructed_language_controls_pilot'
    assert manifest['confirmatory_eligible'] is False
    assert len(manifest['schedule']) == 24
    assert manifest['variant_labels']['defective'].startswith('rewritten')
    assert all(c['role'] in {'ambiguity_probe', 'equivalence_control'} for c in manifest['cases'])
    assert 'eval/language_controls.py' in manifest['code_hashes']


def test_unknown_profile_is_rejected_before_creating_evidence(tmp_path):
    with pytest.raises(ValueError, match='profile'):
        codex_demo.prepare(tmp_path / 'run', model='fixture', replications=2, profile='unreviewed')
    assert not (tmp_path / 'run').exists()


@pytest.mark.parametrize('intended,alternative,expected', [
    ('passed', 'failed', 'intended_only'), ('failed', 'passed', 'alternative_only'),
    ('passed', 'passed', 'both'), ('failed', 'failed', 'neither'),
    ('runtime_error', 'failed', 'execution_unknown'),
    ('passed', 'timeout', 'execution_unknown'),
])
def test_interpretation_reports_uncertainty_instead_of_inventing_a_defect(intended, alternative, expected):
    from eval.language_controls import classify_interpretation
    assert classify_interpretation({'status': intended}, [{'status': alternative}]) == expected


def test_collection_keeps_hidden_metadata_and_interpretations_out_of_provider_input(tmp_path, monkeypatch):
    observed = []
    class Provider:
        last_call_metadata = {}
        def __init__(self, **kwargs): pass
        def complete(self, request):
            observed.append(request.prompt)
            return json.dumps({'source_code': 'def evaluate(*args):\n    return False'})
    monkeypatch.setattr(codex_demo, 'CodexCLIProvider', Provider)
    monkeypatch.setattr(codex_demo.subprocess, 'run', lambda *a, **k: SimpleNamespace(returncode=0, stdout='{"status":"smoke_passed"}'))
    monkeypatch.setattr(codex_demo, 'execute', lambda *a: {'status': 'failed'})
    executable = tmp_path / 'cli'; executable.write_text('fixture')
    report = codex_demo.run(tmp_path / 'run', model='fixture', executable=str(executable),
                            replications=1, profile='language_controls_v1')
    allowed = {c[v] + c['scaffold'] for c in inventory() for v in ('clean', 'defective')}
    assert len(observed) == 12 and all(p in allowed for p in observed)
    assert report['planned_episodes'] == 12
    assert 'mean_project_delta' not in report
    assert report['interpretations']['neither'] == 12
    assert report['groups']['coordination_twin']['interpretations_by_variant'] == {
        'clean': {'neither': 2}, 'defective': {'neither': 2}}
    assert report['groups']['threshold_control']['interpretations_by_variant'] == {
        'clean': {'neither': 1}, 'defective': {'neither': 1}}
    assert len(list((tmp_path / 'run').glob('episode-*/interpretation.json'))) == 12
    assert len(list((tmp_path / 'run').glob('episode-*/alternative-executions.json'))) == 8


def test_provider_failure_stops_dispatch_and_preserves_every_planned_episode(tmp_path, monkeypatch):
    calls = []
    class Provider:
        last_call_metadata = {}
        def __init__(self, **kwargs): pass
        def complete(self, request):
            calls.append(request.prompt)
            raise RuntimeError('model unavailable')
    monkeypatch.setattr(codex_demo, 'CodexCLIProvider', Provider)
    monkeypatch.setattr(codex_demo.subprocess, 'run', lambda *a, **k: SimpleNamespace(returncode=0, stdout='{"status":"smoke_passed"}'))
    executable = tmp_path / 'cli'; executable.write_text('fixture')
    report = codex_demo.run(tmp_path / 'run', model='fixture', executable=str(executable),
                            replications=1, profile='language_controls_v1')
    assert len(calls) == 1
    outcomes = json.loads((tmp_path / 'run/outcomes.json').read_text())
    assert len(outcomes) == 12 and all(r['status'] == 'not_executed' for r in outcomes)
    assert report['dispatch_stopped'] is True
    assert len(list((tmp_path / 'run').glob('episode-*/outcome.json'))) == 12


def test_frozen_deadline_prevents_new_calls_and_preserves_plan(tmp_path, monkeypatch):
    class Provider:
        def __init__(self, **kwargs): pass
        def complete(self, request):
            pytest.fail('provider called after frozen deadline')
    monkeypatch.setattr(codex_demo, 'CodexCLIProvider', Provider)
    monkeypatch.setattr(codex_demo.subprocess, 'run', lambda *a, **k: SimpleNamespace(returncode=0, stdout='{"status":"smoke_passed"}'))
    executable = tmp_path / 'cli'; executable.write_text('fixture')
    deadline = datetime(2000, 1, 1, tzinfo=timezone.utc)
    report = codex_demo.run(tmp_path / 'run', model='fixture', executable=str(executable),
                            replications=1, profile='language_controls_v1', stop_at=deadline)
    assert report['interpretations'] == {'execution_unknown': 12}
    manifest = json.loads((tmp_path / 'run/manifest.json').read_text())
    assert manifest['dispatch_deadline'] == deadline.isoformat()
    assert report['dispatch_stopped'] is True


def test_naive_deadline_rejected_before_evidence_creation(tmp_path):
    with pytest.raises(ValueError, match='timezone'):
        codex_demo.prepare(tmp_path / 'run', model='fixture', replications=1,
                           stop_at=datetime(2030, 1, 1))
    assert not (tmp_path / 'run').exists()
