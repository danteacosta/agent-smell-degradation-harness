"""Exercise collection restarts without providers, network, or real model calls."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
CASE = "example-case"


@pytest.fixture
def collection(tmp_path):
    checkout = tmp_path / "checkout"
    scripts = checkout / "scripts"
    scripts.mkdir(parents=True)
    wrapper = scripts / "run_historical_arm.sh"
    shutil.copyfile(ROOT / "scripts/run_historical_arm.sh", wrapper)
    cases = checkout / "data/historical-arm/cases"
    cases.mkdir(parents=True)
    (cases / f"{CASE}.json").write_text(json.dumps({"case": CASE}))
    for command in (
        ["git", "init", "-q"],
        ["git", "add", "data/historical-arm"],
        ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
         "-c", "core.hooksPath=/dev/null", "commit", "-qm", "Freeze test admission"],
    ):
        subprocess.run(command, cwd=checkout, check=True, capture_output=True)

    fake_python = tmp_path / "fake-python"
    fake_python.write_text(f"#!{sys.executable}\n" + r'''
import json
import os
from pathlib import Path
import sys

args = sys.argv[1:]
if args[0] == '-c':
    os.execv(sys.executable, [sys.executable, *args])
if args[:2] == ['scripts/historical_arm.py', 'analyse']:
    print(json.dumps({'estimate': 0.5}))
    sys.exit(0)
if args[0] != 'scripts/abc_case.py' or args[1] not in ('prepare', 'run'):
    raise AssertionError(f'unexpected fake Python invocation: {args}')
with Path(os.environ['FAKE_CALLS']).open('a') as stream:
    stream.write(json.dumps({'phase': args[1]}) + '\n')
packet = Path(args[args.index('--packet') + 1])
if args[1] == 'prepare':
    (packet / 'frozen').mkdir(parents=True)
    config = json.loads(Path(args[2]).read_text())
    (packet / 'frozen/manifest.json').write_text(json.dumps({'case': config}))
else:
    (packet / 'run-started.json').write_text('{}')
    if os.environ.get('FAKE_INTERRUPT') == '1':
        sys.exit(2)
    (packet / 'results.json').write_text(json.dumps({'case': 'example-case', 'rows': []}))
''')
    fake_python.chmod(0o700)
    calls = tmp_path / "calls.jsonl"
    evidence = tmp_path / "private-evidence"
    env = {**os.environ, "PYTHON": str(fake_python), "EVIDENCE_ROOT": str(evidence),
           "FAKE_CALLS": str(calls)}
    env.pop("FAKE_INTERRUPT", None)
    return checkout, wrapper, evidence, calls, env


def collect(collection, *, interrupt=False):
    checkout, wrapper, _, _, env = collection
    env = {**env, **({"FAKE_INTERRUPT": "1"} if interrupt else {})}
    return subprocess.run(["bash", str(wrapper), "collect"], cwd=checkout,
                          env=env, capture_output=True, text=True, timeout=20)


def phases(collection):
    calls = collection[3]
    return [json.loads(line)["phase"] for line in calls.read_text().splitlines()] if calls.exists() else []


def test_collect_skips_published_cases_on_reinvocation(collection):
    first = collect(collection)
    assert first.returncode == 0, first.stderr
    assert phases(collection) == ["prepare", "run"]
    published = collection[0] / f"data/historical-arm-results/v1/{CASE}/results.json"
    original = published.read_bytes()

    second = collect(collection)
    assert second.returncode == 0, second.stderr
    assert phases(collection) == ["prepare", "run"]
    assert published.read_bytes() == original


def test_collect_refuses_to_repeat_an_interrupted_attempt(collection):
    first = collect(collection, interrupt=True)
    assert first.returncode != 0
    packet = collection[2] / "historical-arm-v1" / CASE
    assert (packet / "run-started.json").exists()
    assert not (packet / "results.json").exists()
    assert phases(collection) == ["prepare", "run"]

    second = collect(collection)
    assert second.returncode != 0
    assert "no automatic retry" in second.stderr
    assert phases(collection) == ["prepare", "run"]
    assert not (collection[0] / f"data/historical-arm-results/v1/{CASE}/results.json").exists()


def test_collect_recovers_a_private_final_without_repeating_calls(collection):
    packet = collection[2] / "historical-arm-v1" / CASE
    packet.mkdir(parents=True)
    (packet / "run-started.json").write_text('{}')
    final = json.dumps({"case": CASE, "rows": []}).encode()
    (packet / "results.json").write_bytes(final)

    recovered = collect(collection)
    assert recovered.returncode == 0, recovered.stderr
    assert phases(collection) == []
    assert (collection[0] / f"data/historical-arm-results/v1/{CASE}/results.json").read_bytes() == final
