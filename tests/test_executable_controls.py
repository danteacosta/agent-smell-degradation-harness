import pytest
from eval.executable_controls import contracts, evaluate, audit_contracts


def test_boundary_vectors_validate_each_contract_and_kill_each_mutant():
    report = audit_contracts()
    assert report['contracts'] == 4
    assert report['vectors_passed'] == report['vectors_total'] == 16
    assert report['mutants_killed'] == 4
    assert report['natural_language_validated'] is False


def test_numeric_boundaries_and_permission_are_not_interchangeable():
    limit = contracts()[0]['contract']
    assert evaluate(limit, {'amount': 100}) is True
    assert evaluate(limit, {'amount': 101}) is False
    permission = contracts()[1]['contract']
    assert evaluate(permission, {'role': 'admin'}) is True
    assert evaluate(permission, {'role': 'guest'}) is False


@pytest.mark.parametrize('value', [True, '100', None, float('nan')])
def test_invalid_numeric_inputs_are_rejected(value):
    with pytest.raises(ValueError):
        evaluate(contracts()[0]['contract'], {'amount': value})


def test_unknown_operator_or_missing_field_fails_closed():
    with pytest.raises(ValueError):
        evaluate({'field': 'x', 'operator': 'python', 'value': 1}, {'x': 1})
    with pytest.raises(ValueError):
        evaluate(contracts()[0]['contract'], {})
