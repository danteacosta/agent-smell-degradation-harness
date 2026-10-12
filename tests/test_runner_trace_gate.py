"""Offline public runner contract: tampered evidence cannot publish metrics."""
import json
from pathlib import Path

import pytest

from agents.stub import StubAgent
from eval.runner import run_eval_with_agent
from eval.task_adapters import DEFAULT_TASK_ADAPTERS
from observability.trace_integrity import read_verified_trace, trace_receipt
from observability.tracing import ProvenanceRecorder


PAIR = {
    'intent_id': 'trace-gate', 'clean_requirement': 'Return within 30 days.',
    'smelly_requirement': 'Return soon.', 'smell': {'type': 'vague_threshold'},
    'oracle_spec': {'codegen': {'return_window_days': 30}},
}


def test_emission_receipt_cannot_be_regenerated_from_a_truncated_file(tmp_path):
    path = tmp_path / 'trace.jsonl'
    rec = ProvenanceRecorder(path)
    rec.operational('latency', {'ms': 1})
    rec.operational('latency', {'ms': 2})
    rec.close()
    path.write_text(path.read_text().splitlines()[0] + '\n')
    assert rec.receipt() != trace_receipt(path)


def test_emission_receipt_matches_flushed_unicode_events_and_does_not_expose_mutable_state(tmp_path):
    path = tmp_path / 'trace.jsonl'
    rec = ProvenanceRecorder(path)
    rec.operational('latency', {'description': 'ação\nconcluída'})
    snapshot = rec.receipt()
    assert snapshot == trace_receipt(path)
    snapshot['event_count'] = 999
    assert rec.receipt()['event_count'] == 1
    rec.close()


def test_verified_reader_returns_the_checked_snapshot_even_if_path_changes(tmp_path, monkeypatch):
    path = tmp_path / 'trace.jsonl'
    rec = ProvenanceRecorder(path)
    rec.operational('latency', {'ms': 1})
    rec.close()
    receipt = rec.receipt()
    real_read = Path.read_bytes
    def read_then_change(file):
        data = real_read(file)
        file.write_bytes(b'altered after read')
        return data
    monkeypatch.setattr(Path, 'read_bytes', read_then_change)
    assert read_verified_trace(path, receipt=receipt)[0]['payload'] == {'ms': 1}


def test_existing_trace_prefix_cannot_be_adopted_as_fresh_emission(tmp_path):
    path = tmp_path / 'trace.jsonl'
    path.write_text('{"event_id":"preexisting","sequence_number":0,"parent_event_id":null}\n')
    rec = ProvenanceRecorder(path)
    rec.operational('latency', {'ms': 1})
    rec.close()
    with pytest.raises(ValueError, match='trace integrity'):
        read_verified_trace(path, receipt=rec.receipt())


def test_verified_reader_requires_a_receipt_even_for_an_intact_trace(tmp_path):
    path = tmp_path / 'trace.jsonl'
    rec = ProvenanceRecorder(path)
    rec.operational('latency', {'ms': 1})
    rec.close()
    with pytest.raises(ValueError, match='receipt is required'):
        read_verified_trace(path, receipt=None)


@pytest.mark.parametrize('kind', ['rewrite', 'delete', 'truncate'])
def test_agent_trace_tampering_stops_before_scoring(tmp_path, kind):
    traces = tmp_path / 'traces'
    evaluated = []
    base = DEFAULT_TASK_ADAPTERS[0]

    class Evaluator:
        task_family = base.task_family
        def evaluate(self, **kwargs):
            evaluated.append(kwargs)
            return base.evaluate(**kwargs)

    class Agent(StubAgent):
        def generate(self, pair, variant, task_family):
            path = next(traces.glob('*.jsonl'))
            if kind == 'delete':
                path.unlink()
            elif kind == 'truncate':
                path.write_bytes(b'')
            else:
                path.write_text(json.dumps({'event_id': 'forged', 'sequence_number': 0,
                                             'parent_event_id': None}) + '\n')
            return super().generate(pair, variant, task_family)

    output = tmp_path / 'metrics.json'
    with pytest.raises(ValueError, match='trace integrity'):
        run_eval_with_agent(Agent(), pairs=[PAIR], output_path=output,
                            traces_dir=traces, task_adapters=[Evaluator()])
    assert evaluated == []
    assert not output.exists()


def test_later_episode_cannot_modify_a_completed_trace_before_metrics(tmp_path):
    traces = tmp_path / 'traces'

    class Agent(StubAgent):
        def generate(self, pair, variant, task_family):
            if variant == 'smelly':
                completed = next(traces.glob('*clean*.jsonl'))
                events = [json.loads(line) for line in completed.read_text().splitlines()]
                events[0]['payload']['intent_id'] = 'changed-after-close'
                completed.write_text(''.join(json.dumps(e) + '\n' for e in events))
            return super().generate(pair, variant, task_family)

    output = tmp_path / 'metrics.json'
    with pytest.raises(ValueError, match='trace integrity'):
        run_eval_with_agent(Agent(), pairs=[PAIR], output_path=output,
                            traces_dir=traces, task_adapters=[DEFAULT_TASK_ADAPTERS[0]])
    assert not output.exists()


def test_intact_runner_trace_records_a_matching_local_receipt(tmp_path):
    _, episodes = run_eval_with_agent(StubAgent(), pairs=[PAIR],
        output_path=tmp_path / 'metrics.json', traces_dir=tmp_path / 'traces',
        task_adapters=[DEFAULT_TASK_ADAPTERS[0]])
    assert len(episodes) == 2
    for episode in episodes:
        assert episode['trace_receipt'] == trace_receipt(Path(episode['provenance_path']))


def test_validator_cannot_change_a_trace_before_metrics_are_published(tmp_path):
    class Validator:
        name = 'tampering-validator'
        def validate(self, path):
            path.write_bytes(b'')
            return True
    output = tmp_path / 'metrics.json'
    with pytest.raises(ValueError, match='trace integrity'):
        run_eval_with_agent(StubAgent(), pairs=[PAIR], output_path=output,
            traces_dir=tmp_path / 'traces', task_adapters=[DEFAULT_TASK_ADAPTERS[0]],
            validators=[Validator()])
    assert not output.exists()


def test_task_evaluator_cannot_change_evidence_consumed_after_scoring(tmp_path):
    traces = tmp_path / 'traces'
    base = DEFAULT_TASK_ADAPTERS[0]

    class Evaluator:
        task_family = base.task_family
        def evaluate(self, **kwargs):
            evaluation = base.evaluate(**kwargs)
            next(traces.glob('*.jsonl')).write_bytes(b'')
            return evaluation

    output = tmp_path / 'metrics.json'
    with pytest.raises(ValueError, match='trace integrity'):
        run_eval_with_agent(StubAgent(), pairs=[PAIR], output_path=output,
            traces_dir=traces, task_adapters=[Evaluator()])
    assert not output.exists()
