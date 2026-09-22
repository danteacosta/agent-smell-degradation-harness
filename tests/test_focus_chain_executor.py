import json
from pathlib import Path
import pytest
from eval import focus_chain_executor as executor

IDS = ['initial_focus', 'input_above_list', 'enter_append', 'input_cleared', 'trimmed_title', 'empty_rejected', 'whitespace_rejected']

def report(failed=()):
    return {'schema_version': 'focus-chain-browser/v1', 'status': 'complete', 'app_sha256': 'a'*64,
            'cases': [{'id': name, 'status': 'failed' if name in failed else 'passed'} for name in IDS]}

@pytest.mark.parametrize('failed,category', [((), 'pass'), (('initial_focus',), 'target_only_failure'),
    (('trimmed_title',), 'non_target_only_failure'), (('initial_focus','trimmed_title'), 'mixed_failure')])
def test_classifies_independent_assertions(failed, category):
    assert executor.classify_report(json.dumps(report(failed)).encode(), bool(failed))['category'] == category

@pytest.mark.parametrize('mutation', ['missing', 'duplicate', 'unknown', 'skipped', 'exit', 'invalid_json'])
def test_incomplete_or_inconsistent_evidence_is_not_defect(mutation):
    value=report(); exitcode=0
    if mutation == 'missing': value['cases'].pop()
    if mutation == 'duplicate': value['cases'][1]=value['cases'][0]
    if mutation == 'unknown': value['cases'][0]['id']='fake'
    if mutation == 'skipped': value['cases'][0]['status']='skipped'
    if mutation == 'exit': exitcode=1
    raw=b'no' if mutation == 'invalid_json' else json.dumps(value).encode()
    assert executor.classify_report(raw,exitcode)['category'] == 'browser_error'

def test_command_enforces_offline_nonroot_isolation(tmp_path):
    inputs=tmp_path/'input'; inputs.mkdir(); (inputs/'app.html').write_text('<html></html>')
    output=tmp_path/'output'; output.mkdir()
    command=executor.container_command('sha256:'+'a'*64,inputs,output,'focus-test')
    for fragment in ['none','--read-only','ALL','no-new-privileges','--memory','--pids-limit','--cpus','--init']:
        assert fragment in command
    assert command[command.index('--user')+1].split(':')[0] != '0'
    assert not any('docker.sock' in item for item in command)

@pytest.mark.parametrize('bad', ['mutable_image','symlink_input','extra_input'])
def test_input_boundary_rejects_ambiguous_mounts(tmp_path,bad):
    inputs=tmp_path/'input'; inputs.mkdir(); app=inputs/'app.html'; app.write_text('x')
    output=tmp_path/'output'; output.mkdir(); image='sha256:'+'a'*64
    if bad=='mutable_image': image='browser:latest'
    if bad=='extra_input': (inputs/'secret.txt').write_text('private')
    if bad=='symlink_input': app.unlink(); app.symlink_to(tmp_path/'outside')
    with pytest.raises(ValueError): executor.container_command(image,inputs,output,'focus-test')

@pytest.mark.parametrize('failed', [(),('initial_focus',)])
def test_report_does_not_trust_app_claimed_summary(failed):
    value=report(failed); value['category']='pass'; value['target_failed']=False
    result=executor.classify_report(json.dumps(value).encode(),bool(failed))
    assert result['target_failed'] == bool(failed)

@pytest.mark.parametrize('fixture,category', [('reference-autofocus','pass'),('reference-imperative','pass'),
    ('mutant-no-focus','target_only_failure'),('mutant-no-clear','non_target_only_failure'),
    ('control-page-tamper','target_only_failure'),('reference-formatted-labels','pass'),
    ('mutant-hidden-labels','non_target_only_failure'),('mutant-no-trim','non_target_only_failure'),('control-interface-missing-label','interface_error')])
def test_actual_browser_qualification(tmp_path,fixture,category):
    import os
    image=os.environ.get('FOCUS_CHAIN_TEST_IMAGE')
    if not image: pytest.skip('set immutable FOCUS_CHAIN_TEST_IMAGE for isolated browser qualification')
    source=Path(__file__).resolve().parents[1]/'eval/fixtures/focus-chain'/f'{fixture}.html'
    inputs=tmp_path/'inputs'; inputs.mkdir(); (inputs/'app.html').write_bytes(source.read_bytes())
    receipt=executor.execute(image,inputs,tmp_path/'output')
    assert receipt['category'] == category, (tmp_path/'output/report.json').read_text()
    expected_failures = {'mutant-no-focus':['initial_focus'], 'control-page-tamper':['initial_focus'],
        'mutant-no-clear':['input_cleared'], 'mutant-hidden-labels':['enter_append','trimmed_title'],
        'mutant-no-trim':['trimmed_title','whitespace_rejected']}
    observed = json.loads((tmp_path/'output/report.json').read_text())
    assert [case['id'] for case in observed['cases'] if case['status']=='failed'] == expected_failures.get(fixture, [])
    assert (tmp_path/'output/initial-focus.png').read_bytes().startswith(b'\x89PNG\r\n\x1a\n')

@pytest.mark.parametrize('digest', [None, '', 'not-a-hash'])
def test_unbound_report_is_not_behavioral_evidence(digest):
    value=report(); value['app_sha256']=digest
    assert executor.classify_report(json.dumps(value).encode(),0)['category'] == 'browser_error'

def test_duplicate_json_fields_rejected():
    raw=json.dumps(report()).replace('"status": "complete"','"status": "bad", "status": "complete"',1)
    assert executor.classify_report(raw.encode(),0)['category'] == 'browser_error'
