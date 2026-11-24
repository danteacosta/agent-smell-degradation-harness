import hashlib
import json
from tempfile import TemporaryDirectory
from pathlib import Path
import pytest
from eval.temporal_cohort_candidate import audit
from eval.temporal_warning_readiness import assess, main

ROOT=Path(__file__).resolve().parents[1]

def candidate():
    return json.loads((ROOT/'data/prepilot/temporal-warning-plan.candidate.json').read_text())


def test_cli_binds_report_to_exact_plan_bytes(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(ROOT)
    plan, output = tmp_path/'plan.json', tmp_path/'report.json'
    first = json.dumps(candidate()).encode()
    plan.write_bytes(first)
    assert main(['--plan', str(plan), '--output', str(output)]) == 2
    old = output.read_bytes()
    report = json.loads(old)
    assert report['plan_sha256'] == hashlib.sha256(first).hexdigest()
    second = b'\n' + first
    plan.write_bytes(second)
    assert main(['--plan', str(plan)]) == 2
    # Both calls printed reports; use only the second one.
    printed = capsys.readouterr().out
    decoded = json.JSONDecoder()
    _, offset = decoded.raw_decode(printed)
    latest = json.loads(printed[offset:])
    assert latest['plan_sha256'] == hashlib.sha256(second).hexdigest()
    assert latest['plan_sha256'] != report['plan_sha256']
    assert output.read_bytes() == old


@pytest.mark.parametrize('cap,ready', [(0.11, True), (0.10999999999999999, False)])
def test_decimal_budget_boundary(declared, cap, ready):
    declared['budget'] = {'estimated_provider_cost_usd': 0.1,
                          'contingency_fraction': 0.1, 'approved_cap_usd': cap}
    report = assess(declared, ROOT)
    assert (report['decision'] == 'prerequisites_declared') is ready


@pytest.mark.parametrize('budget', [None, {'estimated_provider_cost_usd': 10**400,
                                        'contingency_fraction': 0, 'approved_cap_usd': 1}])
def test_invalid_or_over_cap_budget_returns_no_go(declared, budget):
    declared['budget'] = budget
    result = assess(declared, ROOT)
    assert result['decision'] == 'no_go'
    assert result['blockers'] == ['finite_cost_envelope_and_approved_cap_missing']


@pytest.mark.parametrize('task', [None, 'code_generation'])
def test_wrong_or_missing_primary_task_is_rejected(declared, task):
    if task is None:
        declared.pop('primary_task')
    else:
        declared['primary_task'] = task
    with pytest.raises(ValueError, match='primary task'):
        assess(declared, ROOT)


@pytest.mark.parametrize('key', ['"rights_approved"', r'"rights_approv\u0065d"'])
def test_cli_rejects_duplicate_nested_plan_members(tmp_path, monkeypatch, capsys, key):
    monkeypatch.chdir(ROOT)
    plan, output = tmp_path/'plan.json', tmp_path/'output.json'
    base = candidate()
    base['independent_human_reviews'] = [{'rights_approved': True}]
    plan.write_text(json.dumps(base).replace('"rights_approved": true',
                    f'{key}: false, "rights_approved": true'))
    with pytest.raises(SystemExit) as error:
        main(['--plan', str(plan), '--output', str(output)])
    assert error.value.code == 2
    assert 'duplicate JSON object member: rights_approved' in capsys.readouterr().err
    assert not output.exists()


def test_assess_rejects_duplicate_members_even_when_audit_hash_matches(declared):
    reference = declared['exposure_audit']
    path = ROOT/reference['path']
    original = json.loads(path.read_bytes())
    data = json.dumps(original).replace('"pairs_verified": 12',
                                       '"pairs_verified": 0, "pairs_verified": 12').encode()
    assert data != path.read_bytes()
    path.write_bytes(data)
    reference['sha256'] = hashlib.sha256(data).hexdigest()
    with pytest.raises(ValueError, match='duplicate JSON object member: pairs_verified'):
        assess(declared, ROOT)


def _write_reference(path, value):
    path.write_text(json.dumps(value), encoding='utf-8')
    reference = {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    if 'registry_files' in value:
        reference['registry_files'] = value['registry_files']
    return reference


@pytest.fixture
def declared():
    p=candidate();p['selection_frozen']=p['split_frozen']=True
    p['project_split']={'strictdoc':'train','CASS':'train','todomvc':'train','realworld':'calibration','kanboard':'test','paperless-ngx':'test'}
    p['independent_human_reviews']=[{'intent_id':i,'source_manifest_sha256':p['candidate_source_manifest']['sha256'],'mapping_approved':True,'manipulation_approved':True,'rights_approved':True,'prior_exposure_and_residual_cues_reviewed':True,'independent_of_author':True,'reviewer_id':reviewer} for i in p['selected_requirements'] for reviewer in ('reviewer-a','reviewer-b')]
    report_path='tests/fixtures/temporal-provider-qualification.synthetic.json'
    report_hash=hashlib.sha256((ROOT/report_path).read_bytes()).hexdigest()
    p['qualified_provider_configurations']=[{'provider':provider,'model':'fixture','model_version':'fixture','mode':'runtime','checkpoint_source':'runtime_native','qualification_passed':True,'t1_t3_before_t4':True,'prompted_snapshot':False,'configuration_hash':'a'*64,'qualification_report_sha256':report_hash,'qualification_report_path':report_path} for provider in ['provider-a','provider-b']]
    for field in ['rubric_frozen','annotation_blinding_verified','independent_annotators_ready','prefix_clock_and_collector_qualified','feature_and_score_policy_frozen','schedule_frozen','launch_authorized']:p[field]=True
    p['budget']={'estimated_provider_cost_usd':1,'contingency_fraction':.25,'approved_cap_usd':2}
    # Empty registry is a synthetic positive case, not an exposure finding.
    with TemporaryDirectory(dir=ROOT) as directory:
        source = json.loads((ROOT/p['candidate_source_manifest']['path']).read_text())
        p['exposure_audit'] = _write_reference(Path(directory)/'audit.json', audit(source, ROOT, []))
        yield p


def test_live_candidate_is_no_go_not_a_120_episode_gate():
    p=candidate();r=assess(p,ROOT)
    assert r['decision']=='no_go' and r['planned_episodes']==144
    assert len(r['blockers'])==12
    assert 'exposure_audit_not_bound_to_candidate' not in r['blockers']
    assert r['reviewed_intents']==r['qualified_distinct_providers']==0
    assert r['review_status_by_intent'] == {
        intent_id: 'awaiting_approvals' for intent_id in p['selected_requirements']
    }
    assert p['historical_launch_gate_reference'].endswith('launch-plan.candidate.json')


def test_declarations_never_authorize_collection_or_confirmatory_claims(declared):
    r=assess(declared,ROOT)
    assert r['decision']=='prerequisites_declared'
    assert r['collection_authorized_by_this_report'] is False
    assert r['confirmatory_eligible'] is False


@pytest.mark.parametrize('change', ['missing_inventory', 'count_mismatch', 'duplicate_path',
                                  'changed_bytes', 'missing_file', 'outside_root'])
def test_incomplete_or_changed_registry_cannot_clear_readiness(change, declared, tmp_path):
    source = json.loads((ROOT/declared['candidate_source_manifest']['path']).read_text())
    directory = (ROOT/declared['exposure_audit']['path']).parent
    prior = directory/'prior.json'
    prior.write_text('{"requirement_text": "unrelated synthetic input"}')
    report = audit(source, ROOT, [prior.relative_to(ROOT)])
    expected = 1
    if change == 'missing_inventory':
        report.pop('inventory')
    elif change == 'count_mismatch':
        expected = 2
    elif change == 'duplicate_path':
        report['inventory'] *= 2
        report['registry_files'] = expected = 2
    elif change == 'changed_bytes':
        prior.write_text('{"requirement_text": "changed after exposure audit"}')
    elif change == 'missing_file':
        report['inventory'][0]['path'] = str(prior.relative_to(ROOT)) + '.missing'
    else:
        outside = tmp_path/'outside.json'
        outside.write_bytes(prior.read_bytes())
        report['inventory'][0]['path'] = str(outside)
    declared['exposure_audit'] = _write_reference(directory/'scope-audit.json', report)
    declared['exposure_audit']['registry_files'] = expected
    result = assess(declared, ROOT)
    assert result['decision'] == 'no_go'
    assert result['blockers'] == ['exposure_registry_inventory_incomplete_or_changed']


@pytest.mark.parametrize('change,complete', [('one_per_intent', 0), ('alias', 11), ('duplicate', 11)])
def test_each_intent_requires_two_distinct_reviewers(change, complete, declared):
    reviews = declared['independent_human_reviews']
    if change == 'one_per_intent':
        reviews[:] = reviews[::2]
    elif change == 'alias':
        reviews[1]['reviewer_id'] = ' ＲＥＶＩＥＷＥＲ-A '
    else:
        reviews[1] = reviews[0].copy()
    result = assess(declared, ROOT)
    assert result['decision'] == 'no_go'
    assert result['reviewed_intents'] == complete
    assert result['blockers'] == ['independent_reviews_incomplete_or_not_bound_to_source']


@pytest.mark.parametrize('reviewer,decision', [(' REVIEWER-A ', False), ('reviewer-c', False),
                                              ('reviewer-c', None)])
def test_current_nonapproval_cannot_be_discarded(reviewer, decision, declared):
    reviews = declared['independent_human_reviews']
    reviews.append(dict(reviews[0], reviewer_id=reviewer, rights_approved=decision))
    result = assess(declared, ROOT)
    assert result['decision'] == 'no_go'
    assert result['reviewed_intents'] == 11
    assert result['review_status_by_intent'] == {
        intent_id: 'unresolved' if intent_id == reviews[0]['intent_id'] else 'complete'
        for intent_id in declared['selected_requirements']
    }
    assert 'reviewer-a' not in json.dumps(result)
    assert 'reviewer-c' not in json.dumps(result)
    assert result['blockers'] == ['independent_reviews_incomplete_or_not_bound_to_source']


def test_nonapproval_from_an_old_manifest_is_not_a_current_review(declared):
    reviews = declared['independent_human_reviews']
    reviews.append(dict(reviews[0], source_manifest_sha256='0'*64, rights_approved=False))
    assert assess(declared, ROOT)['decision'] == 'prerequisites_declared'


@pytest.mark.parametrize('field',['selection_frozen','split_frozen','rubric_frozen','annotation_blinding_verified','independent_annotators_ready','prefix_clock_and_collector_qualified','feature_and_score_policy_frozen','schedule_frozen','launch_authorized'])
def test_each_pending_prerequisite_keeps_no_go(field, declared):
    p=declared;p[field]=False
    assert assess(p,ROOT)['decision']=='no_go'


@pytest.mark.parametrize('change',['same_provider_alias','prompted_snapshot','future_boundary','unqualified','review_hash','author_review','missing_intent','split_overlap','budget_nan','budget_exceeded'])
def test_invalid_receipts_and_design_boundaries_fail_closed(change, declared):
    p=declared
    if change=='same_provider_alias':p['qualified_provider_configurations'][1]['provider']=' PROVIDER-A '
    elif change=='prompted_snapshot':p['qualified_provider_configurations'][1]['prompted_snapshot']=True
    elif change=='future_boundary':p['qualified_provider_configurations'][1]['t1_t3_before_t4']=False
    elif change=='unqualified':p['qualified_provider_configurations'][1]['qualification_passed']=False
    elif change=='review_hash':p['independent_human_reviews'][0]['source_manifest_sha256']='bad'
    elif change=='author_review':p['independent_human_reviews'][0]['independent_of_author']=False
    elif change=='missing_intent':p['independent_human_reviews'].pop()
    elif change=='split_overlap':p['project_split']['realworld']='test'
    elif change=='budget_nan':p['budget']['approved_cap_usd']=float('nan')
    elif change=='budget_exceeded':p['budget']['approved_cap_usd']=.1
    assert assess(p,ROOT)['decision']=='no_go'


def test_source_hash_cannot_be_replaced_by_a_status_flag(declared):
    p=declared;p['candidate_source_manifest']['sha256']='0'*64
    with pytest.raises(ValueError,match='hash mismatch'):assess(p,ROOT)


@pytest.mark.parametrize('change',['missing','hash_mismatch','directory','absolute_escape','symlink_escape'])
def test_qualification_reports_must_exist_match_and_stay_inside_root(change,tmp_path,declared):
    p=declared; c=p['qualified_provider_configurations'][1]
    if change=='missing': c['qualification_report_path']='tests/fixtures/nonexistent-qualification.json'
    elif change=='hash_mismatch': c['qualification_report_sha256']='0'*64
    elif change=='directory': c['qualification_report_path']='tests/fixtures'
    else:
        outside=tmp_path/'outside.json';outside.write_text('synthetic only')
        c['qualification_report_sha256']=hashlib.sha256(outside.read_bytes()).hexdigest()
        if change=='absolute_escape': c['qualification_report_path']=str(outside)
        else:
            # A temporary link inside the root must not grant access outside it.
            import tempfile
            with tempfile.TemporaryDirectory(dir=ROOT) as directory:
                link=Path(directory)/'linked.json';link.symlink_to(outside)
                c['qualification_report_path']=str(link.relative_to(ROOT))
                r=assess(p,ROOT)
                assert r['qualified_distinct_providers']==1 and r['decision']=='no_go'
                return
    r=assess(p,ROOT)
    assert r['qualified_distinct_providers']==1
    assert 'two_distinct_runtime_native_providers_not_qualified' in r['blockers']
    assert r['collection_authorized_by_this_report'] is False


def test_legacy_audit_blocks_even_with_all_other_prerequisites_declared(declared):
    historical = 'data/prepilot/temporal-warning-exposure-audit.json'
    declared['exposure_audit'] = {
        'path': historical,
        'sha256': hashlib.sha256((ROOT/historical).read_bytes()).hexdigest(),
        'registry_files': 898,
    }
    r = assess(declared, ROOT)
    assert r['decision'] == 'no_go'
    assert r['blockers'] == ['exposure_audit_not_bound_to_candidate',
                             'exposure_audit_missing_defective_variant_coverage']


def test_audit_for_same_ids_cannot_clear_a_revised_pair(declared):
    p = declared
    source = json.loads((ROOT/p['candidate_source_manifest']['path']).read_text())
    row = source['records'][0]
    clean, edit = row['variants']['clean'], row['manipulation']
    # Retain a valid single deletion, but make the defective input different.
    edit['end'] -= 1
    edit['text'] = clean[edit['start']:edit['end']]
    row['variants']['defective'] = clean[:edit['start']] + clean[edit['end']:]
    directory = (ROOT/p['exposure_audit']['path']).parent
    p['candidate_source_manifest'] = _write_reference(directory/'revised-source.json', source)
    for review in p['independent_human_reviews']:
        review['source_manifest_sha256'] = p['candidate_source_manifest']['sha256']
    r = assess(p, ROOT)
    assert r['decision'] == 'no_go'
    assert r['blockers'] == ['exposure_audit_not_bound_to_candidate']
    p['exposure_audit'] = _write_reference(directory/'revised-audit.json', audit(source, ROOT, []))
    assert assess(p, ROOT)['decision'] == 'prerequisites_declared'


def test_defective_only_prior_input_blocks_readiness(declared):
    source = json.loads((ROOT/declared['candidate_source_manifest']['path']).read_text())
    row = source['records'][0]
    directory = (ROOT/declared['exposure_audit']['path']).parent
    prior = directory/'prior.json'
    prior.write_text(json.dumps({'requirement_text': row['variants']['defective']}))
    report = audit(source, ROOT, [prior.relative_to(ROOT)])
    assert report['exact_or_contained_clean_input_matches'][row['intent_id']] == []
    assert report['exact_or_contained_defective_input_matches'][row['intent_id']] == [
        str(prior.relative_to(ROOT))]
    declared['exposure_audit'] = _write_reference(directory/'paired-audit.json', report)
    assert assess(declared, ROOT)['blockers'] == [
        'prior_complete_input_match_requires_candidate_replacement_or_explicit_review']


@pytest.mark.parametrize('variant', ['clean', 'defective'])
def test_hash_bound_audit_cannot_hide_reproducible_input_matches(declared, variant):
    source = json.loads((ROOT/declared['candidate_source_manifest']['path']).read_text())
    row = source['records'][0]
    directory = (ROOT/declared['exposure_audit']['path']).parent
    prior = directory/'prior-input.json'
    prior.write_text(json.dumps({'requirement_text':row['variants'][variant]}))
    report = audit(source, ROOT, [prior.relative_to(ROOT)])
    assert report[f'exact_or_contained_{variant}_input_matches'][row['intent_id']]
    # Keep the true inventory, file hashes and candidate digest; suppress hits.
    for name in ('clean', 'defective'):
        for paths in report[f'exact_or_contained_{name}_input_matches'].values():
            paths.clear()
    declared['exposure_audit'] = _write_reference(directory/'suppressed-hits.json', report)
    result = assess(declared, ROOT)
    assert result['decision'] == 'no_go'
    assert result['blockers'] == ['exposure_match_maps_not_reproducible']


@pytest.mark.parametrize('variant', ['clean', 'defective'])
@pytest.mark.parametrize('invalid', [None, False, '', [None]])
def test_malformed_match_entry_is_not_a_negative_result(declared, variant, invalid):
    path = ROOT/declared['exposure_audit']['path']
    report = json.loads(path.read_bytes())
    report[f'exact_or_contained_{variant}_input_matches'][declared['selected_requirements'][0]] = invalid
    declared['exposure_audit'] = _write_reference(path, report)
    with pytest.raises(ValueError, match='malformed exposure match list'):
        assess(declared, ROOT)


def test_cli_preserves_report_while_returning_nonzero_for_no_go(tmp_path,monkeypatch):
    monkeypatch.chdir(ROOT);out=tmp_path/'readiness.json'
    assert main(['--output',str(out)])==2
    assert json.loads(out.read_text())['decision']=='no_go'


def test_cli_never_overwrites_an_existing_report(tmp_path,monkeypatch,capsys):
    monkeypatch.chdir(ROOT)
    out=tmp_path/'readiness.json';original=b'previous evidence\n'
    out.write_bytes(original)
    with pytest.raises(SystemExit) as error:main(['--output',str(out)])
    assert error.value.code==2
    assert out.read_bytes()==original
    assert 'cannot create readiness report' in capsys.readouterr().err


def test_cli_output_cannot_replace_its_input_plan(tmp_path,monkeypatch):
    monkeypatch.chdir(ROOT)
    plan=tmp_path/'plan.json';original=json.dumps(candidate()).encode('utf-8')
    plan.write_bytes(original)
    with pytest.raises(SystemExit):main(['--plan',str(plan),'--output',str(plan)])
    assert plan.read_bytes()==original


def test_cli_repeated_export_preserves_first_result(tmp_path,monkeypatch):
    monkeypatch.chdir(ROOT)
    out=tmp_path/'readiness.json'
    assert main(['--output',str(out)])==2
    original=out.read_bytes()
    with pytest.raises(SystemExit):main(['--output',str(out)])
    assert out.read_bytes()==original
