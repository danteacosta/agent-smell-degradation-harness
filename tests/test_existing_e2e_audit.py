import pytest
from scripts.audit_existing_e2e_results import compare, audit_pairs


@pytest.mark.parametrize('old,new,expected', [
    ('pass', 'pass', 'equal'),
    ('target_only_failure', 'target_only_failure', 'equal'),
    ('target_only_failure', 'pass', 'improved'),
    ('pass', 'target_only_failure', 'worsened'),
    ('browser_error', 'pass', 'unknown'),
    ('target_only_failure', 'non_target_only_failure', 'unknown'),
    ('mixed_failure', 'pass', 'unknown'),
])
def test_pair_direction_and_unknowns(old, new, expected):
    assert compare(old, new) == expected


def pair_data():
    return {'pairs': [dict(model=m, replication=r, old='pass', new='pass', comparison='equal')
                      for m in ('Luna', 'Sol') for r in (1, 2, 3)]}


def test_duplicate_pair_cannot_inflate_denominator():
    data = pair_data()
    data['pairs'][-1] = data['pairs'][0].copy()
    with pytest.raises(ValueError, match='duplicate'):
        audit_pairs(data)


def test_unknown_cannot_be_reported_as_improvement():
    data = pair_data()
    data['pairs'][0].update(old='browser_error', comparison='improved')
    with pytest.raises(ValueError, match='classification'):
        audit_pairs(data)


def test_equal_failures_remain_distinct_from_equal_passes():
    data = pair_data()
    data['pairs'][0].update(old='target_only_failure', new='target_only_failure')
    result = audit_pairs(data)
    assert result['comparisons'] == {'equal': 6}
    assert result['equal_outcomes'] == {'target_only_failure': 1, 'pass': 5}


def test_recent_six_lots_reconcile_without_pooling_requirements():
    from scripts.audit_existing_e2e_results import audit_recent
    result = audit_recent()
    packets = result['packets']
    assert len(packets) == 6
    assert sum(p['rows_verified'] for p in packets.values()) == 108
    assert result['confirmatory_eligible'] is False
    assert packets['data/e2e-realworld-comment-delete/replication-20261001']['nested_triplets'] == {'all_pass': 6}
    assert packets['data/e2e-paperless-inbox-suggestions/replication-20261001-v3']['nested_triplets'] == {
        'C_target_failure_with_AB_pass': 4, 'all_pass': 2}


@pytest.mark.parametrize('mutation, message', [
    ('duplicate', 'duplicate browser identity'),
    ('category', 'classification mismatch'),
    ('report_binding', 'report must be bound'),
    ('html_binding', 'generated artifact identity'),
    ('schedule', 'incomplete or unexpected'),
    ('receipt', 'public receipt mismatch'),
])
def test_recent_audit_rejects_inconsistent_public_evidence(tmp_path, mutation, message):
    import hashlib
    import importlib.util
    import json
    import shutil
    from scripts.audit_existing_e2e_results import ROOT, audit_recent_packet
    packet = tmp_path / 'packet'
    shutil.copytree(ROOT / 'data/e2e-paperless-inbox-suggestions/replication-20261001-v3', packet)
    qualifier = ROOT / 'eval/fixtures/paperless-inbox-suggestions/qualify.py'
    spec = importlib.util.spec_from_file_location('inbox_test_qualifier', qualifier)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    path = packet / 'summary.json'
    data = json.loads(path.read_text())
    if mutation == 'duplicate':
        data['rows'][-1] = data['rows'][0].copy()
    elif mutation == 'category':
        data['rows'][0]['category'] = 'pass'
    elif mutation == 'report_binding':
        data['rows'][0]['browser_report_sha256'] = '0' * 64
    elif mutation == 'html_binding':
        data['rows'][0]['generated_html_sha256'] = '0' * 64
    elif mutation == 'schedule':
        data['attempted_calls'] = 17
    path.write_text(json.dumps(data))
    receipt_path = packet / 'receipt.json'
    receipt = json.loads(receipt_path.read_text())
    if mutation != 'receipt':
        receipt['files']['summary.json'] = hashlib.sha256(path.read_bytes()).hexdigest()
    receipt_path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match=message):
        audit_recent_packet(packet, module.classify)
