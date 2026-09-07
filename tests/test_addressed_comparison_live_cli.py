"""No secrets or transport access in offline CLI operations."""
import json
import socket
import subprocess
import sys

import pytest

from eval.addressed_comparison_plan import prepare_comparison
from test_addressed_comparison_custody import prepared
from test_addressed_comparison_plan import failed_predecessor, snapshot


def api():
    from eval import addressed_comparison_live
    return addressed_comparison_live


def cli(*args):
    return subprocess.run([sys.executable, '-m', 'eval.addressed_comparison_live', *map(str, args)],
                          text=True, capture_output=True, timeout=20)


def test_prepare_and_report_are_network_free_and_preserve_old_files(tmp_path, monkeypatch, capsys):
    _, predecessor = failed_predecessor(tmp_path / 'old')
    plan = tmp_path / 'approved.json'
    plan.write_text(json.dumps(prepare_comparison(predecessor, approval=True)))
    directory = tmp_path / 'PRIVATE-new'
    monkeypatch.setattr(socket, 'socket', lambda *args, **kw: pytest.fail('offline network'))
    assert api().main(['prepare', '--approved-plan', str(plan), '--directory', str(directory), '--approve-live']) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['accounting']['reserved_attempts'] == 0
    assert result['main_collection_released'] is False
    before = snapshot(tmp_path)
    assert api().main(['report', '--directory', str(directory)]) == 0
    assert 'PRIVATE' not in capsys.readouterr().out
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize('args', [[], ['--PRIVATE-secret'], ['development', '--directory', 'PRIVATE-path'],
    ['prepare', '--approved-plan', 'PRIVATE-plan', '--directory', 'PRIVATE-dir'],
    ['report', '--directory', 'PRIVATE-missing']])
def test_invalid_cli_never_echoes_private_values(args):
    result = cli(*args)
    assert result.returncode == 2
    assert 'PRIVATE' not in result.stdout + result.stderr
    assert 'Traceback' not in result.stdout + result.stderr
    assert json.loads(result.stdout)['main_collection_released'] is False


def test_missing_credentials_fail_before_reservation(tmp_path):
    _, _, directory, _ = prepared(tmp_path)
    before = (directory / 'ledger.jsonl').read_bytes()
    result = cli('development', '--directory', directory, '--approve-live')
    assert result.returncode == 2
    assert json.loads(result.stdout)['error'] == 'missing_credentials'
    assert (directory / 'ledger.jsonl').read_bytes() == before
