"""Bounded local files and public summaries, with no API or ledger dispatch."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

import pytest

from eval.addressed_comparison_plan import prepare_comparison
from test_addressed_comparison_plan import failed_predecessor, snapshot
from test_addressed_comparison_audit import responses


def api():
    from eval import addressed_comparison
    return addressed_comparison


def cli(*args):
    return subprocess.run([sys.executable, '-m', 'eval.addressed_comparison', *map(str, args)],
                          text=True, capture_output=True, timeout=15)


def test_prepare_export_and_audit_cli_are_offline_and_preserve_originals(tmp_path, monkeypatch, capsys):
    _, run = failed_predecessor(tmp_path / 'old')
    before = snapshot(tmp_path / 'old')

    def forbid_network(*args, **kwargs):
        raise AssertionError('offline command attempted network access')

    monkeypatch.setattr(socket, 'socket', forbid_network)
    monkeypatch.setattr(socket, 'getaddrinfo', forbid_network)
    output = tmp_path / 'PRIVATE-candidate'
    assert api().main(['prepare', '--predecessor', str(run), '--approve-offline', '--output-dir', str(output)]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary['planned_calls'] == 144
    assert summary['execution_authorized'] is False
    assert os.stat(output).st_mode & 0o777 == 0o700
    plan = json.loads((output / 'plan.json').read_text())
    rows = output / 'PRIVATE-responses.json'; rows.write_text(json.dumps(responses(plan)))
    assert api().main(['audit', '--plan', str(output / 'plan.json'), '--responses', str(rows)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report['candidate_response_rules']['evaluation'] == 'met_offline_only'
    assert report['provider_calls_dispatched'] == 0 and not report['usage_cost_verified']
    assert snapshot(tmp_path / 'old') == before
    assert not (output / 'ledger.jsonl').exists()
    assert not (output / 'closure.json').exists()


def test_existing_export_is_not_overwritten(tmp_path):
    _, run = failed_predecessor(tmp_path / 'old')
    output = tmp_path / 'PRIVATE-existing'; output.mkdir()
    marker = output / 'original'; marker.write_text('keep')
    result = cli('prepare', '--predecessor', run, '--approve-offline', '--output-dir', output)
    assert result.returncode == 2
    assert marker.read_text() == 'keep'
    assert sorted(p.name for p in output.iterdir()) == ['original']
    assert 'PRIVATE' not in result.stdout + result.stderr


def test_export_inside_any_git_checkout_is_refused(tmp_path):
    _, run = failed_predecessor(tmp_path / 'old')
    checkout = tmp_path / 'PRIVATE-checkout'; checkout.mkdir()
    subprocess.run(['git', 'init', '-q', str(checkout)], check=True)
    output = checkout / 'candidate'
    result = cli('prepare', '--predecessor', run, '--approve-offline', '--output-dir', output)
    assert result.returncode == 2 and not output.exists()


@pytest.mark.parametrize('bad', [b'{', b'\xff', b'{"x":1,"x":2}', b'[NaN]', b'x' * (16 * 1024 * 1024 + 1)],
                         ids=['json', 'unicode', 'duplicate', 'nan', 'oversized'])
def test_bad_private_file_has_fixed_public_error(tmp_path, bad):
    path = tmp_path / 'PRIVATE-file.json'; path.write_bytes(bad)
    result = cli('audit', '--plan', path, '--responses', path)
    assert result.returncode == 2
    assert json.loads(result.stdout)['execution_authorized'] is False
    assert 'PRIVATE' not in result.stdout + result.stderr
    assert 'Traceback' not in result.stdout + result.stderr


@pytest.mark.parametrize('kind', ['file_symlink', 'directory_symlink', 'fifo', 'missing'])
def test_nonregular_or_indirect_paths_are_refused_without_blocking(tmp_path, kind):
    target = tmp_path / 'PRIVATE-file'
    if kind == 'file_symlink':
        other = tmp_path / 'other'; other.write_text('{}'); target.symlink_to(other)
    elif kind == 'directory_symlink':
        other = tmp_path / 'directory'; other.mkdir(); (other / 'file').write_text('{}')
        target.symlink_to(other, target_is_directory=True); target = target / 'file'
    elif kind == 'fifo': os.mkfifo(target)
    result = cli('audit', '--plan', target, '--responses', target)
    assert result.returncode == 2 and 'PRIVATE' not in result.stdout + result.stderr


@pytest.mark.parametrize('args', [[], ['--live', 'PRIVATE-secret'], ['prepare', '--env-file', 'PRIVATE-env'],
                                 ['prepare', '--predecessor', 'PRIVATE-path']])
def test_invalid_or_live_arguments_do_not_echo_secrets(args):
    result = cli(*args)
    assert result.returncode == 2
    assert json.loads(result.stdout)['error'] in {'invalid_arguments', 'approval_required'}
    assert 'PRIVATE' not in result.stdout + result.stderr


def test_missing_observations_return_nonzero_without_hiding_report(tmp_path):
    _, run = failed_predecessor(tmp_path / 'old')
    plan = prepare_comparison(run, approval=True)
    plan_path = tmp_path / 'plan.json'; plan_path.write_text(json.dumps(plan))
    rows = tmp_path / 'rows.json'; rows.write_text('[]')
    result = cli('audit', '--plan', plan_path, '--responses', rows)
    assert result.returncode == 2
    assert json.loads(result.stdout)['totals']['missing'] == 144
