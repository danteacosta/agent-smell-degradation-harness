"""Offline acceptance contracts for source-based pilot preparation."""
import copy

import pytest


def api():
    from eval import pilot_preparation
    return pilot_preparation


def candidates():
    p = api()
    return [dict(source_intent_id=f'intent-{i}', project_id=f'project-{i % 6}',
                 source_url=f'https://example.org/revision/record-{i}',
                 source_revision_id='a' * 40, source_locator=f'req-{i}',
                 license='Apache-2.0', license_url='https://example.org/LICENSE',
                 clean_requirement=f'Action {i} requires permission.',
                 defective_requirement=f'Action {i}.',
                 clean_requirement_sha256=p.digest(f'Action {i} requires permission.'),
                 defective_requirement_sha256=p.digest(f'Action {i}.'),
                 reference_constraint={'constraint_id': f'c-{i}', 'text': f'Action {i} requires permission.'},
                 atomic_obligations=[f'Action {i}', 'permission'],
                 reviews={'rights': 'pending', 'independence': 'pending', 'manipulation': 'pending'})
            for i in range(24)]


def test_pending_reviews_are_not_automatically_admitted():
    result = api().audit_candidates(candidates())
    assert result['candidate_count'] == 24
    assert result['project_count'] == 6
    assert result['admitted_count'] == 0
    assert not result['corpus_ready']


@pytest.mark.parametrize('mutation', ['hash', 'intent', 'locator', 'reference', 'project', 'mutable_revision'])
def test_candidate_structural_failures_are_rejected(mutation):
    rows = candidates()
    if mutation == 'hash': rows[0]['clean_requirement'] += ' altered'
    if mutation == 'intent': rows[0]['source_intent_id'] = rows[1]['source_intent_id']
    if mutation == 'locator':
        for k in ['project_id', 'source_revision_id', 'source_locator']:
            rows[0][k] = rows[1][k]
    if mutation == 'reference': rows[0]['reference_constraint']['constraint_id'] = 'c-1'
    if mutation == 'project':
        for row in rows: row['project_id'] = 'one'
    if mutation == 'mutable_revision': rows[0]['source_revision_id'] = 'main'
    with pytest.raises(ValueError): api().audit_candidates(rows)


def test_sampling_is_label_blind_stable_and_preserves_historical_responses():
    p = api()
    rows = [dict(text_id=f't-{i}', project_id=f'p-{i % 6}', criteria='x' * (10+i),
                 obligation_count=1+i % 3, old_responses=[{'label': 'clean'}]) for i in range(60)]
    first = p.select_natural_sample(rows, per_project=4)
    altered = copy.deepcopy(rows)
    for row in altered: row['old_responses'] = [{'label': 'severe'}]
    second = p.select_natural_sample(list(reversed(altered)), per_project=4)
    assert first['selection_sha256'] == second['selection_sha256']
    assert len(first['selected']) == 24
    assert first['selected'][0]['old_responses'] != second['selected'][0]['old_responses']
    assert 'old_responses' not in str(first['selection_inputs'])


def control_seed():
    return dict(seed_id='s1', source_intent_id='intent-1',
                source_revision_id='a'*40, source_locator='requirement-1',
                clauses=['The service stores the document.', 'The service keeps earlier versions.'],
                target_index=1, context=('Other interfaces list the available formats.\n' * 24),
                ambiguous_text='The service handles documents according to the policy in unavailable section X.')


def test_controls_have_private_oracles_and_exact_single_clause_deletion():
    p = api()
    pack = p.build_source_controls([control_seed()])
    assert len(pack['cases']) == 5
    by_op = {x['oracle']['operation']: x for x in pack['cases']}
    full = by_op['long_covered']['request']['generated_acceptance_criteria']
    omitted = by_op['long_omitted']['request']['generated_acceptance_criteria']
    assert full.replace('The service keeps earlier versions.\n', '', 1) == omitted
    assert len(omitted) / len(full) >= .9
    assert by_op['insufficient']['oracle']['expected_status'] == 'uncertain'
    for case in pack['cases']:
        prompt = p.render_request(case['request'])
        assert 'expected_status' not in prompt
        assert 'source_intent_id' not in prompt
        assert 'seed_id' not in prompt


def test_duplicate_target_in_context_is_rejected():
    seed = control_seed()
    seed['context'] += seed['clauses'][1]
    with pytest.raises(ValueError): api().build_source_controls([seed])


def test_budget_counts_real_calls_and_rejects_unfunded_full_protocol():
    p = api()
    prices = [{'input_usd_per_1k': '0.0002', 'output_usd_per_1k': '0.0012'},
              {'input_usd_per_1k': '0.00132', 'output_usd_per_1k': '0.00396'}]
    result = p.plan_budget(5, prices, auxiliary_input_bounds=[2000]*30, natural_input_bounds=[1000]*24)
    assert result['base_episodes'] == 240
    assert result['provider_trajectories'] == 480
    assert result['duplicate_trajectories'] == 96
    assert result['generation_calls'] == 1440
    assert result['pipeline_judge_calls'] == 1152
    assert result['auxiliary_calls'] == 108
    assert result['planned_calls'] == 2700
    assert result['reserved_microusd'] > 1000000
    assert not result['within_cap']


@pytest.mark.parametrize('value', [True, 0, -1, 2.5])
def test_repetition_count_must_be_a_positive_integer(value):
    with pytest.raises(ValueError): api().plan_budget(value, [])


def test_preparation_never_claims_runtime_or_authorization_from_candidate_count():
    report = api().readiness(api().audit_candidates(candidates()), {'within_cap': True})
    assert report['decision'] == 'no_go'
    assert report['provider_calls_executed'] == 0
    assert not report['confirmatory_authorized']
    assert 'pilot_runtime_not_validated' in report['blockers']
    assert 'pilot_scope_authorization_missing' in report['blockers']


def test_bundle_writes_private_artifacts_without_overwriting(tmp_path):
    p = api()
    prices = [{'input_usd_per_1k': '0.0002', 'output_usd_per_1k': '0.0012'}]*2
    pool = [dict(text_id=f'p{i}-{j}', project_id=f'project-{i}', criteria='text',
                 obligation_count=2, old_responses=[], request=api().build_source_controls([control_seed()])['cases'][0]['request'])
            for i in range(6) for j in range(3)]
    for row in pool:
        row['request']['generated_acceptance_criteria'] = row['criteria']
        row['request']['occurrence_id'] = p.digest(row['text_id'])[:24]
    output = tmp_path/'private-package'
    result = p.write_preparation(candidates(), [control_seed()], pool, prices, output)
    assert result['readiness']['provider_calls_executed'] == 0
    assert (output/'manifest.json').exists()
    assert (output.stat().st_mode & 0o777) == 0o700
    saved = (output/'requests.jsonl').read_text()
    assert 'expected_status' not in saved and 'old_responses' not in saved
    with pytest.raises(FileExistsError):
        p.write_preparation(candidates(), [control_seed()], pool, prices, output)
    assert p.verify_preparation(output)['verified']
    (output/'requests.jsonl').write_text('{}\n')
    with pytest.raises(ValueError): p.verify_preparation(output)


def test_screening_is_included_in_the_same_pilot_budget():
    p = api()
    prices = [{'input_usd_per_1k': '0.0002', 'output_usd_per_1k': '0.0012'}]*2
    result = p.plan_budget(1, prices, screening_input_bounds=[1500]*30)
    assert result['screening_calls'] == 60
    assert result['planned_calls'] == 580


def test_natural_request_cannot_silently_differ_from_sampled_text(tmp_path):
    p = api()
    prices = [{'input_usd_per_1k': '0.0002', 'output_usd_per_1k': '0.0012'}]*2
    pool = [dict(text_id=f'p{i}-{j}', project_id=f'project-{i}', criteria='sampled text',
                 obligation_count=2, old_responses=[], request=p.build_source_controls([control_seed()])['cases'][0]['request'])
            for i in range(6) for j in range(3)]
    with pytest.raises(ValueError, match='sampled text'):
        p.write_preparation(candidates(), [control_seed()], pool, prices, tmp_path/'bad')
    assert not (tmp_path/'bad').exists()


def test_natural_sample_cannot_omit_corpus_projects(tmp_path):
    p = api()
    prices = [{'input_usd_per_1k': '0.0002', 'output_usd_per_1k': '0.0012'}]*2
    pool = [dict(text_id=f't-{i}', project_id='project-0', criteria='sampled text',
                 obligation_count=2, old_responses=[], request=p.build_source_controls([control_seed()])['cases'][0]['request'])
            for i in range(3)]
    with pytest.raises(ValueError, match='projects'):
        p.write_preparation(candidates(), [control_seed()], pool, prices, tmp_path/'bad')


def test_paid_terminal_generation_is_not_named_pre_final_t3():
    p = api()
    prices = [{'input_usd_per_1k': '0.0002', 'output_usd_per_1k': '0.0012'}]*2
    result = p.plan_budget(1, prices)
    assert set(result['phase_bounds']) == {'generation.T1', 'generation.T2', 'generation.artifact', 'judge'}
