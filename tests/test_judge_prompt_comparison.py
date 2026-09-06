import json

import pytest

from label_plane.judge_controls import build_controls
from label_plane.exploratory_judge import build_judge_prompt, validate_judge_request
from label_plane.judge_prompt_comparison import (
    build_comparison_pack, comparison_prompt, parse_evidence_response, score_comparison,
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
