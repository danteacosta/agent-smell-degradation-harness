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
