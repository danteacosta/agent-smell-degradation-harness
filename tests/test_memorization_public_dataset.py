"""Public readers can reproduce labels and reject semantic drift after rehashing."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

PACKET = Path(__file__).resolve().parents[1] / 'data/memorization-probe-20261002'


def read(packet: Path, name: str):
    return json.loads((packet / name).read_text())


def write(packet: Path, name: str, value) -> None:
    (packet / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def reseal(packet: Path) -> None:
    write(packet, 'receipt.json', {'files': {
        str(path.relative_to(packet)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in packet.rglob('*') if path.is_file() and path.name != 'receipt.json'
    }})


def verify(packet: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(packet / 'verify.py'), '--public', str(packet)],
                          capture_output=True, text=True, check=False)


def test_reader_reproduces_the_published_completed_probe() -> None:
    receipt_before = (PACKET / 'receipt.json').read_bytes()
    process = verify(PACKET)
    assert process.returncode == 0, process.stderr
    report = json.loads(process.stdout)
    assert (report['rules'], report['pairs'], report['answer_slots'], report['calls']) == (69, 138, 414, 1006)
    assert report['by_coder']['gpt-5.6-luna']['frozen_memorized_1'] == 22
    assert report['by_coder']['gpt-5.6-sol']['frozen_memorized_1'] == 31
    assert (PACKET / 'receipt.json').read_bytes() == receipt_before


@pytest.mark.parametrize('mutation', ['positive_as_unknown', 'second_after_no'])
def test_reader_rejects_rehashed_labels_or_judge_schedule_drift(tmp_path: Path, mutation: str) -> None:
    packet = tmp_path / 'public'
    shutil.copytree(PACKET, packet)
    results, manifest = read(packet, 'results.json'), read(packet, 'manifest.json')
    first, second = manifest['judges']
    if mutation == 'positive_as_unknown':
        row = next(r for r in results['rows'] if r['yes'] > 0)
        answer = next(a for a in row['answers'] if a['states_rule'] == 'yes')
        answer['states_rule'] = None
        row['yes'] -= 1
        row['memorized'] = int(row['yes'] >= 2)
        expected_error = 'answer state differs from judge routing'
    else:
        row = next(r for r in results['rows'] if any(a['verdicts'].get(first) == 'no' for a in r['answers']))
        answer = next(a for a in row['answers'] if a['verdicts'].get(first) == 'no')
        answer['verdicts'][second] = 'no'
        expected_error = 'incorrect conditional judge schedule'
    write(packet, 'results.json', results)
    # Synthetic source references deliberately follow the mutated result bytes,
    # so the asserted failure must come from routing rather than the SHA gate.
    source_hash = hashlib.sha256((packet / 'results.json').read_bytes()).hexdigest()
    custody, audit = read(packet, 'custody.json'), read(packet, 'audit.json')
    custody['source_results_sha256'] = source_hash
    audit['results_sha256'] = source_hash
    write(packet, 'custody.json', custody)
    write(packet, 'audit.json', audit)
    reseal(packet)  # Receipt now matches: rejection must come from behavior validation.
    process = verify(packet)
    assert process.returncode != 0
    assert expected_error in process.stderr


def test_reader_preserves_an_unresolved_judgment_as_unknown(tmp_path: Path) -> None:
    packet = tmp_path / 'synthetic-unresolved'
    shutil.copytree(PACKET, packet)
    results, manifest = read(packet, 'results.json'), read(packet, 'manifest.json')
    first = manifest['judges'][0]
    row = next(r for r in results['rows'] if r['yes'] == 1 and any(a['verdicts'].get(first) == 'no' for a in r['answers']))
    answer = next(a for a in row['answers'] if a['verdicts'].get(first) == 'no')
    answer['verdicts'][first] = None
    answer['states_rule'] = None
    results['summary']['unjudged_answers'] += 1
    write(packet, 'results.json', results)
    calls = read(packet, 'calls.json')
    slot = f"probes/{row['candidate_id']}/{row['coder']}/rep{answer['rep']}/judges/{first}"
    call = next(c for c in calls if c['slot'] == slot)
    raw = 'Unable to produce a valid judgment.'
    call.update(raw_response=raw, raw_result={'verdict': None}, verdict=None,
                original_response_sha256=hashlib.sha256(raw.encode()).hexdigest(),
                original_response_bytes=len(raw.encode()), original_response_characters=len(raw))
    write(packet, 'calls.json', calls)
    audit = read(packet, 'audit.json')
    audited_row = next(r for r in audit['rows'] if (r['candidate_id'], r['coder']) == (row['candidate_id'], row['coder']))
    audited_row.update(no=audited_row['no'] - 1, judge_unresolved=1, diagnostic='inconclusive')
    totals = audit['by_coder'][row['coder']]
    totals['no'] -= 1
    totals['judge_unresolved'] = 1
    totals['not_recovered'] -= 1
    totals['inconclusive'] = 1
    # This copy is a synthetic source with an unresolved judgment, not a claim
    # about the original collection. Rebind its result hash consistently.
    source_hash = hashlib.sha256((packet / 'results.json').read_bytes()).hexdigest()
    audit['results_sha256'] = source_hash
    custody = read(packet, 'custody.json')
    custody['source_results_sha256'] = source_hash
    write(packet, 'custody.json', custody)
    write(packet, 'audit.json', audit)
    reseal(packet)
    process = verify(packet)
    assert process.returncode == 0, process.stderr
    report = json.loads(process.stdout)
    assert report['by_coder'][row['coder']]['inconclusive'] == 1
    assert report['by_coder'][row['coder']]['judge_unresolved'] == 1
    assert report['by_coder'][row['coder']]['frozen_memorized_1'] == read(PACKET, 'audit.json')['by_coder'][row['coder']]['frozen_memorized_1']


def test_reader_rejects_rehashed_results_with_changed_source_bytes(tmp_path: Path) -> None:
    packet = tmp_path / 'source-byte-drift'
    shutil.copytree(PACKET, packet)
    path = packet / 'results.json'
    path.write_bytes(path.read_bytes() + b'\n')  # Same labels, different original source bytes.
    reseal(packet)
    process = verify(packet)
    assert process.returncode != 0
    assert 'public results bytes differ from source custody hash' in process.stderr
