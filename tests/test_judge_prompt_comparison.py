import json

import pytest

from label_plane.judge_controls import build_controls
from label_plane.exploratory_judge import build_judge_prompt, validate_judge_request
from label_plane.judge_prompt_comparison import (
    build_comparison_pack, comparison_prompt, parse_evidence_response, score_comparison,
    build_schema_smoke_pack,
)


def configurations():
    return {'a'*64: {'arm': 'historical', 'provider': 'p1'},
            'b'*64: {'arm': 'evidence', 'provider': 'p1'}}


def rows_with_answer(answer):
    pack = build_comparison_pack()
    return [dict(pack_sha256=pack['pack_sha256'], configuration_sha256=config,
                 replication_id=rep, occurrence_id=case['request']['occurrence_id'],
                 raw_response=json.dumps(answer(case, config)))
            for config in configurations() for rep in range(2) for case in pack['cases']]


def test_old_controls_are_preserved_and_new_controls_have_no_oracle_in_request():
    pack = build_comparison_pack()
    assert len(pack['cases']) == 36
    assert [c['request'] for c in pack['cases'][:12]] == [c['request'] for c in build_controls()['cases']]
    assert len({c['request']['occurrence_id'] for c in pack['cases']}) == 36
    assert len({c['oracle']['seed_id'] for c in pack['cases'][12:]}) == 6
    for case in pack['cases']:
        request = validate_judge_request(case['request'])
        assert comparison_prompt(request, 'historical') == build_judge_prompt(request)
        prompt = comparison_prompt(request, 'evidence')
        assert 'every clause' in prompt
        assert 'oracle' not in prompt
        assert case['oracle']['stratum'] not in prompt


def test_constant_covered_exposes_deletion_misses_and_constant_omitted_false_alarms():
    def answer(case, config):
        payload = {'label': 'clean', 'status': 'covered'}
        if config == 'b'*64:
            payload = {'label': 'severe', 'status': 'omitted', 'evidence': ''}
        return payload
    report = score_comparison(rows_with_answer(answer), configurations())
    old = report['configurations']['a'*64]
    new = report['configurations']['b'*64]
    assert old['overall']['planned'] == 72
    assert old['overall']['correct'] == 36
    assert old['strata']['new']['by_operation']['deleted']['correct'] == 0
    assert new['overall']['correct'] == 36
    assert new['overall']['false_alarm'] == 36
    assert report['confirmatory_eligible'] is False


def test_grounding_requires_quote_from_criteria_not_reference():
    case = next(c for c in build_comparison_pack()['cases'] if c['oracle']['operation'] == 'deleted')
    reference = case['request']['reference_constraints'][0]['text']
    raw = json.dumps({'label': 'clean', 'status': 'covered', 'evidence': reference})
    _, grounded = parse_evidence_response(raw, case['request'])
    assert grounded is False
    raw = json.dumps({'label': 'severe', 'status': 'omitted', 'evidence': ''})
    _, grounded = parse_evidence_response(raw, case['request'])
    assert grounded is True


@pytest.mark.parametrize('raw', [
    '{"label":"clean","label":"severe","status":"omitted","evidence":""}',
    '{"label":"clean","status":"covered"}',
    '{"label":"clean","status":"covered","evidence":[],"extra":true}',
])
def test_evidence_schema_rejects_duplicates_and_missing_fields(raw):
    with pytest.raises(ValueError):
        parse_evidence_response(raw, build_comparison_pack()['cases'][0]['request'])


def test_plan_denominators_and_duplicates_are_not_silently_dropped():
    report = score_comparison([], configurations())
    assert report['configurations']['a'*64]['overall']['missing'] == 72
    rows = rows_with_answer(lambda c, k: {'label': 'clean', 'status': 'covered'})
    with pytest.raises(ValueError):
        score_comparison(rows + rows[:1], configurations())


def test_schema_repair_explicitly_maps_fields_without_reusing_comparison_cases():
    pack = build_schema_smoke_pack()
    assert len(pack['cases']) == 4
    old_ids = {c['request']['occurrence_id'] for c in build_comparison_pack()['cases']}
    assert not old_ids & {c['request']['occurrence_id'] for c in pack['cases']}
    prompt = comparison_prompt(pack['cases'][0]['request'], 'evidence_v2')
    assert 'label must be one of: clean, minor, moderate, severe, not_visible' in prompt
    assert 'status must be one of: covered, omitted, uncertain' in prompt
    with pytest.raises(ValueError):
        parse_evidence_response('{"label":"covered","status":"clean","evidence":""}',
                                pack['cases'][0]['request'])


def test_expanded_study_has_balanced_new_templates_and_no_oracle_leakage():
    import label_plane.judge_prompt_comparison as comparison
    assert hasattr(comparison, 'study_pack')
    pack = comparison.study_pack('expanded_v2')
    assert len(pack['cases']) == 48
    previous = build_comparison_pack()['cases'] + build_schema_smoke_pack()['cases']
    assert not ({c['request']['occurrence_id'] for c in previous} &
                {c['request']['occurrence_id'] for c in pack['cases']})
    assert not ({c['request']['reference_constraints'][0]['text'] for c in previous} &
                {c['request']['reference_constraints'][0]['text'] for c in pack['cases']})
    assert len({c['oracle']['seed_id'] for c in pack['cases']}) == 12
    for seed in range(12):
        cases = [c for c in pack['cases'] if c['oracle']['seed_id'] == seed]
        assert {c['oracle']['operation'] for c in cases} == {'literal', 'paraphrased', 'deleted', 'contradicted'}
        assert sum(c['oracle']['covered'] for c in cases) == 2
    for case in pack['cases']:
        prompt = comparison_prompt(case['request'], 'evidence_v2')
        assert 'oracle' not in prompt and 'expanded_v2' not in prompt
        assert comparison_prompt(case['request'], 'historical') == build_judge_prompt(case['request'])


def test_expanded_scorer_preserves_denominators_and_false_alarm_diagnostic():
    import label_plane.judge_prompt_comparison as comparison
    assert hasattr(comparison, 'study_pack')
    pack = comparison.study_pack('expanded_v2')
    configs = {'a'*64: {'arm': 'evidence_v2', 'provider': 'p1'}}
    missing = score_comparison([], configs, study='expanded_v2')['configurations']['a'*64]
    assert missing['overall']['missing'] == 96
    rows = [dict(pack_sha256=pack['pack_sha256'], configuration_sha256='a'*64,
                 replication_id=rep, occurrence_id=c['request']['occurrence_id'],
                 raw_response='{"label":"severe","status":"omitted","evidence":""}')
            for rep in range(2) for c in pack['cases']]
    scored = score_comparison(rows, configs, study='expanded_v2')['configurations']['a'*64]
    assert scored['overall']['false_alarm'] == 48
    assert scored['strata']['expanded_new']['by_operation']['deleted']['correct'] == 24
