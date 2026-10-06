from scripts import shared_omission_e2e as study


def test_code_prompt_uses_confirmed_mutant_not_correct_reference(tmp_path):
    correct = tmp_path / 'correct.html'
    mutant = tmp_path / 'mutant.html'
    correct.write_text('<html>CORRECT_REFERENCE_SECRET</html>')
    mutant.write_text('<html>MUTANT_IMPLEMENTATION</html>')
    records = [{'case': 'sample', 'reference': 'a1', 'roles': {'mutant': ['c1']},
                'artifacts': {'a1': {'artifact_path': str(correct)}, 'c1': {'artifact_path': str(mutant)}}}]
    calls = [{'case': 'sample', 'source': source, 'suite_index': k, 'prompt': 'old', 'targets': ['a1','c1']}
             for source in study.ma.SOURCES for k in (1,2)]
    complete = {'sample': 'COMPLETE_REQUIREMENT'}
    incomplete = {'sample': 'INCOMPLETE_REQUEST'}
    transformed, selected = study.transform_plan(calls, records, complete, incomplete)
    assert selected == {'sample': 'c1'}
    assert len({c['call_id'] for c in transformed}) == 8
    for call in transformed:
        if call['source'] in ('code_complete', 'code_incomplete'):
            assert 'MUTANT_IMPLEMENTATION' in call['prompt']
            assert 'CORRECT_REFERENCE_SECRET' not in call['prompt']
            expected = complete['sample'] if call['source'] == 'code_complete' else incomplete['sample']
            assert expected in call['prompt']
        else:
            assert call['prompt'] == 'old'
    assert study.transform_plan(calls, records, complete, incomplete) == (transformed, selected)


def test_primary_holds_mutant_code_constant_and_interaction_is_explicit():
    def rows(call, source, mutant_verdict):
        return [
            dict(call_id=call, case='sample', project_id='p', source=source, suite_index=1,
                 slot_id='a', role='correct', verdict='quiet', is_reference=True),
            dict(call_id=call, case='sample', project_id='p', source=source, suite_index=1,
                 slot_id='c', role='mutant', verdict=mutant_verdict, is_reference=False),
        ]
    data = []
    data += rows('sc', 'spec_complete', 'assertion_alarm')
    data += rows('si', 'spec_incomplete', 'quiet')
    data += rows('cc', 'code_complete', 'assertion_alarm')
    data += rows('ci', 'code_incomplete', 'quiet')
    result = study.analyse(data)
    assert result['primary']['comparison'] == 'code_complete - code_incomplete'
    assert result['primary']['mean_difference'] == 1
    assert result['scaffold_replication']['mean_difference'] == 1
    assert result['factorial_interaction']['mean_difference'] == 0
    assert result['factorial_interaction']['status'] == 'exploratory_no_decision_gate'


def test_finalize_writes_four_arm_analysis_once_and_receipt_excludes_itself(tmp_path):
    rows = []
    for source, verdict in [('spec_complete', 'assertion_alarm'), ('spec_incomplete', 'quiet'),
                            ('code_complete', 'assertion_alarm'), ('code_incomplete', 'quiet')]:
        rows.extend([
            dict(call_id=source, case='sample', project_id='p', source=source, suite_index=1,
                 slot_id='a', role='correct', verdict='quiet', is_reference=True),
            dict(call_id=source, case='sample', project_id='p', source=source, suite_index=1,
                 slot_id='c', role='mutant', verdict=verdict, is_reference=False),
        ])

    result = study.finalize(tmp_path, rows)
    saved = __import__('json').loads((tmp_path / 'results.json').read_text())
    receipt = __import__('json').loads((tmp_path / 'receipt.json').read_text())['files']
    assert result == saved['analysis'] and result['primary']['mean_difference'] == 1
    assert 'receipt.json' not in receipt
    assert receipt == {path: digest for path, digest in study.ma.ta.inventory(tmp_path).items()
                       if path != 'receipt.json'}
    import pytest
    with pytest.raises(FileExistsError):
        study.finalize(tmp_path, rows)


def test_execute_emits_all_four_sources_without_intermediate_overwrite(tmp_path, monkeypatch):
    artifacts = {}
    for slot, role in [('a', 'correct'), ('c', 'mutant')]:
        path = tmp_path / 'artifacts' / slot / 'app.html'
        study.ma.ta.put(path, f'<html>{role}</html>')
        artifacts[slot] = {'role': role, 'artifact_path': str(path)}
    schedule = []
    for source in study.SOURCES:
        call_id = f'call-{source}'
        directory = tmp_path / 'calls' / call_id
        suite = f'module.exports = {{source: "{source}"}};\n'
        study.ma.ta.put(directory / 'suite.cjs', suite)
        study.ma.ta.put(directory / 'result.json', {
            'status': 'suite_ready', 'suite_sha256': study.ma.ta.sha256_file(directory / 'suite.cjs')})
        schedule.append({'call_id': call_id, 'case': 'sample', 'project_id': 'p',
                         'source': source, 'suite_index': 1, 'targets': ['a', 'c']})
    study.ma.ta.put(tmp_path / 'generation.json', {'suite_ready': 4})
    manifest = {'schedule': schedule, 'cases': [{'case': 'sample', 'reference': 'a',
                                                 'artifacts': artifacts}]}
    monkeypatch.setattr(study, 'verify', lambda out: manifest)

    def executor(artifact, suite, output):
        mutant = 'mutant' in artifact.read_text()
        complete = 'complete' in suite.read_text() and 'incomplete' not in suite.read_text()
        return {'status': 'complete', 'tests': [
            {'outcome': 'assertion_failure' if mutant and complete else 'pass'}]}

    result = study.execute(tmp_path, executor=executor)
    saved = __import__('json').loads((tmp_path / 'results.json').read_text())
    assert len(saved['rows']) == 8
    assert set(saved['analysis']['by_source']) == set(study.SOURCES)
    assert result['primary']['comparison'] == 'code_complete - code_incomplete'
    import pytest
    with pytest.raises(FileExistsError, match='no resume'):
        study.execute(tmp_path, executor=executor)


def test_quiet_mutant_outcome_is_separate_from_reference_eligibility():
    def row(call, slot, role, verdict, ref=False):
        return dict(call_id=call, case='sample', project_id='p', source='code_incomplete',
                    suite_index=1, slot_id=slot, role=role, verdict=verdict, is_reference=ref)
    rows = [row('good','a','correct','quiet',True), row('good','c','mutant','quiet'),
            row('good','other','correct','assertion_alarm'), row('bad','a','correct','assertion_alarm',True),
            row('bad','c','mutant','quiet')]
    result = study.analyse_selected(rows, {'selected_mutants':{'sample':'c'}})['code_incomplete']
    assert result['quiet'] == 2
    assert result['eligible_pairs'] == result['eligible_quiet'] == 1
    assert result['conditional_discrimination']['correct'] == {'alarms':1,'pairs':1,'rate':1.0}


def test_failed_controls_are_refused_before_generation():
    import pytest
    with pytest.raises(ValueError, match='not qualified'):
        study.validate_controls({'qualified':False})


def test_adapter_drift_is_refused_with_other_hashes_valid(tmp_path):
    import pytest
    ma = study.ma
    out = tmp_path / 'study'
    expected = {'broken_save':'assertion_alarm','keeps_rule':'quiet','lost_rule':'assertion_alarm'}
    ma.ta.put(out / 'frozen/controls.json', {'qualified':True,'expected':expected,'observed':expected,
                                         'runner_sha256':ma.ta.sha256_file(ma.ta.RUNNER)})
    manifest = {'schema_version':study.SCHEMA,'code_context_role':'confirmed_mutant','cases':[],
                'script_sha256':ma.ta.sha256_file(__import__('pathlib').Path(ma.__file__)),
                'test_anchor_script_sha256':ma.ta.sha256_file(__import__('pathlib').Path(ma.ta.__file__)),
                'runner_sha256':ma.ta.sha256_file(ma.ta.RUNNER),'image':ma.ta.IMAGE,
                'extension_script_sha256':'wrong'}
    ma.ta.put(out / 'frozen/manifest.json',manifest)
    ma.ta.put(out / 'frozen/receipt.json',{'files':ma.ta.inventory(out / 'frozen')})
    with pytest.raises(ValueError,match='extension script drift'):
        study.verify(out)
