"""Whole context survives construction; clarified instructions do not repair labels."""
import copy
import json

import pytest

from label_plane import addressed_judge, scoped_judge
from label_plane.artifact_segments import build_snapshot
from test_scoped_judge import seed


def api():
    from label_plane import qualified_judge
    return qualified_judge


@pytest.mark.parametrize('context', [
    '- A value is computed from the\n  previous value plus one.\n',
    '| Name | Role |\n| --- | --- |\n| A | Reader |\n',
    '```python\nvalue = 1\nprint(value)\n```\n',
    'Résumé of the system.\r\nWrapped context continues\r\nwithout a new paragraph.\r\n',
])
def test_context_remains_contiguous_in_both_distributed_variants(context):
    original = seed(); original['context'] = context
    before = copy.deepcopy(original)
    cases = api().build_cases([original])
    for case in cases:
        if case['oracle']['operation'] in {'distributed_complete', 'long_omission'}:
            assert case['item']['criteria'].count(context) == 1
            assert context.encode('utf-8') in case['item']['criteria'].encode('utf-8')
    assert original == before


def test_historical_midpoint_interrupts_a_wrapped_instruction():
    original = seed(); original['context'] = '- Compute the next\n  numeric value.\n'
    historical = scoped_judge.build_cases([original])[1]
    assert original['context'] not in historical['item']['criteria']
    corrected = api().build_cases([original])[1]
    assert original['context'] in corrected['item']['criteria']


@pytest.mark.parametrize('target', [0, 1])
def test_only_target_clause_is_removed_and_all_other_controls_are_preserved(target):
    original = seed(); original['target_index'] = target
    historical = scoped_judge.build_cases([original])
    corrected = api().build_cases([original])
    assert len({c['id'] for c in corrected}) == 6
    assert not {c['id'] for c in corrected} & {c['id'] for c in historical}
    for old, new in zip(historical, corrected):
        assert old['oracle'] == new['oracle']
        assert {k:v for k,v in old['item'].items() if k!='criteria'} == {
            k:v for k,v in new['item'].items() if k!='criteria'}
        if new['oracle']['operation'] not in {'distributed_complete','long_omission'}:
            assert new['item'] == old['item']
    full, missing = corrected[1]['item']['criteria'], corrected[2]['item']['criteria']
    assert full.replace(original['clauses'][target], '', 1) == missing
    assert all(clause in missing for i,clause in enumerate(original['clauses']) if i!=target)


def test_v4_stays_unchanged_and_both_arms_receive_the_same_data_without_oracles():
    case = api().build_cases([seed('PRIVATE_SOURCE')])[2]
    v4 = api().build_prompt(case['item'], 'v4')
    v5 = api().build_prompt(case['item'], 'v5')
    assert v4 == addressed_judge.build_prompt(case['item'])
    assert v4 != v5
    assert json.loads(v4.split('INPUT_JSON:\n')[1]) == json.loads(v5.split('INPUT_JSON:\n')[1])
    assert 'interface' in v5 and 'incomplete support' in v5
    for text in (v4,v5):
        assert 'PRIVATE_SOURCE' not in text and 'target_index' not in text
        assert 'long_omission' not in text and 'oracle' not in text


@pytest.mark.parametrize('status', ['covered','omitted','uncertain'])
def test_parser_retains_model_status_and_distinguishes_version_without_semantic_promotion(status):
    item = api().build_cases([seed()])[0]['item']
    identifier = build_snapshot(item['criteria'])['segments'][0]['id']
    raw = json.dumps({'checks':[{'id':o['id'],'status':status,'evidence_ids':[identifier]}
                               for o in item['obligations']]})
    old = api().parse_response(raw,item,'v4')
    new = api().parse_response(raw,item,'v5')
    assert new['status'] == old['status'] == status
    assert new['checks'] == old['checks']
    assert new['prompt_version'] != old['prompt_version']
    assert new['semantic_validity'] == 'not_measured'
    assert new['locator_integrity'] == 'valid'


@pytest.mark.parametrize('arm', ['v2','unknown',None])
def test_unknown_arm_is_rejected(arm):
    item = scoped_judge.build_cases([seed()])[0]['item']
    with pytest.raises(ValueError): api().build_prompt(item,arm)
    with pytest.raises(ValueError): api().parse_response('{}',item,arm)


def test_invalid_or_invented_evidence_is_not_repaired_by_candidate_parser():
    item = api().build_cases([seed()])[0]['item']
    raw = json.dumps({'checks':[{'id':o['id'],'status':'covered','evidence_ids':['fake']}
                               for o in item['obligations']]})
    with pytest.raises(ValueError): api().parse_response(raw,item,'v5')
