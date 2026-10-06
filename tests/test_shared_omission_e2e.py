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
    prompts = {'sample': 'INCOMPLETE_REQUEST'}
    transformed, selected = study.transform_plan(calls, records, prompts)
    assert selected == {'sample': 'c1'}
    assert len({c['call_id'] for c in transformed}) == 6
    for call in transformed:
        if call['source'] == 'code_incomplete':
            assert 'MUTANT_IMPLEMENTATION' in call['prompt']
            assert 'CORRECT_REFERENCE_SECRET' not in call['prompt']
            assert 'INCOMPLETE_REQUEST' in call['prompt']
        else:
            assert call['prompt'] == 'old'
    assert study.transform_plan(calls, records, prompts) == (transformed, selected)


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
