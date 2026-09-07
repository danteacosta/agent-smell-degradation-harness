"""Behavioral contracts for a separate scope-aware diagnostic judge."""
import copy
import json

import pytest


def api():
    from label_plane import scoped_judge
    return scoped_judge


def seed(identifier='development', project='A'):
    return {'source_intent_id': identifier, 'project_id': project,
            'source_revision_id': 'a'*40, 'source_locator': identifier,
            'source_url': 'https://example.org/pinned/source',
            'license': 'Apache-2.0', 'split': 'development',
            'clauses': ['The service stores the document.',
                        'The service retains earlier versions.'],
            'target_index': 1,
            'contradiction': 'The service discards all earlier versions.',
            'context': 'The interface displays available formats.\n'*30}


def test_all_six_operations_have_distinct_scope_and_construction_oracles():
    cases=api().build_cases([seed()])
    ops={c['oracle']['operation']:c for c in cases}
    assert set(ops)=={'concise_complete','distributed_complete','long_omission',
                     'partial_missing','partial_complete','partial_contradiction'}
    assert ops['partial_missing']['oracle']['status']=='uncertain'
    assert ops['partial_complete']['oracle']['status']=='covered'
    assert ops['partial_contradiction']['oracle']['status']=='omitted'
    assert ops['long_omission']['oracle']['checks']==['covered','omitted']
    assert ops['partial_missing']['oracle']['checks']==['covered','uncertain']
    assert len(ops['long_omission']['item']['criteria'])>1000


def test_judge_visible_payload_excludes_oracles_and_source_identity():
    case=api().build_cases([seed('SECRET_SOURCE_ID')])[0]
    for arm in ('v2','v3'):
        prompt=api().build_prompt(case['item'],arm)
        assert 'SECRET_SOURCE_ID' not in prompt
        assert 'expected_status' not in prompt and 'source_intent_id' not in prompt
        assert 'OBSERVATION_SCOPE' in prompt
        assert case['item']['reference'] in json.loads(prompt.split('INPUT_JSON:\n')[1]).values()


@pytest.mark.parametrize('statuses,expected', [(['covered','covered'],'covered'),
    (['covered','uncertain'],'uncertain'), (['omitted','uncertain'],'omitted')])
def test_aggregate_uses_every_obligation_and_retains_uncertainty(statuses,expected):
    item=api().build_cases([seed()])[0]['item']
    raw=json.dumps({'checks':[{'id':c['id'],'status':s,
        'evidence':c['text'][:60] if s=='covered' else ''}
        for c,s in zip(item['obligations'],statuses)]})
    assert api().parse_response(raw,item,'v3')['status']==expected


@pytest.mark.parametrize('mutation',['missing','duplicate','unknown','ungrounded','long_quote',
    'empty_covered','extra','wrong_status','duplicate_json'])
def test_malformed_or_unverifiable_responses_are_not_repaired(mutation):
    item=api().build_cases([seed()])[0]['item']
    value={'checks':[{'id':o['id'],'status':'covered','evidence':o['text']}
                     for o in item['obligations']]}
    if mutation=='missing':value['checks'].pop()
    if mutation=='duplicate':value['checks'][1]['id']=value['checks'][0]['id']
    if mutation=='unknown':value['checks'][0]['id']='unknown'
    if mutation=='ungrounded':value['checks'][0]['evidence']='not visible'
    if mutation=='long_quote':value['checks'][0]['evidence']='x'*121
    if mutation=='empty_covered':value['checks'][0]['evidence']=''
    if mutation=='extra':value['label']='clean'
    if mutation=='wrong_status':value['checks'][0]['status']='clean'
    raw=json.dumps(value) if mutation!='duplicate_json' else '{"checks":[],"checks":[]}'
    with pytest.raises(ValueError):api().parse_response(raw,item,'v3')


def test_v2_keeps_legacy_fields_but_rejects_inconsistent_label_status():
    item=api().build_cases([seed()])[0]['item']
    with pytest.raises(ValueError):
        api().parse_response(json.dumps({'label':'clean','status':'omitted','evidence':''}),item,'v2')


def test_source_context_cannot_include_target_or_duplicate_seed():
    s=seed(); s['context']+=s['clauses'][1]
    with pytest.raises(ValueError):api().build_cases([s])
    with pytest.raises(ValueError):api().build_cases([seed(),seed()])


def test_missing_scope_or_extra_judge_visible_fields_are_rejected():
    item=api().build_cases([seed()])[0]['item']
    bad=copy.deepcopy(item);bad['scope']='unknown'
    with pytest.raises(ValueError):api().build_prompt(bad,'v3')
    bad=copy.deepcopy(item);bad['oracle']='covered'
    with pytest.raises(ValueError):api().build_prompt(bad,'v3')
