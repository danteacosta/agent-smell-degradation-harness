from __future__ import annotations

import json
from pathlib import Path

from agents.stub import StubAgent
from eval.identity import create_episode_identity
from eval.runner import run_eval_with_agent


def test_episode_identity_is_reproducible_and_replication_safe():
    kwargs = {
        "experiment_id": "agent-smell",
        "run_id": "run-20260730",
        "intent_id": "RF-09",
        "workload_id": "RF-09",
        "variant_id": "clean",
        "task_id": "test_gen",
        "configuration_id": "cfg-direct",
    }

    first = create_episode_identity(replication_id=0, **kwargs)
    repeated = create_episode_identity(replication_id=0, **kwargs)
    another_replication = create_episode_identity(replication_id=1, **kwargs)

    assert first == repeated
    assert first.episode_id != another_replication.episode_id
    assert first.episode_id in first.trace_name
    assert another_replication.replication_id == 1


def test_runner_persists_identity_before_execution_in_trace_and_export(tmp_path: Path):
    pair = {
        "intent_id": "RF-IDENTITY",
        "clean_requirement": "Return eligible orders within 30 days.",
        "smelly_requirement": "Return old orders soon.",
        "smell": {"type": "vague_threshold"},
        "oracle_spec": {
            "codegen": {"result": "ok"},
            "test_gen": {"result": "ok"},
        },
    }
    episodes_path = tmp_path / "episodes.jsonl"
    _metrics, episodes = run_eval_with_agent(
        StubAgent(),
        pairs=[pair],
        output_path=tmp_path / "metrics.json",
        traces_dir=tmp_path / "traces",
        episodes_path=episodes_path,
        experiment_id="agent-smell",
        run_id="run-20260730",
        replication_id=3,
        configuration_id="cfg-direct",
    )

    episode = episodes[0]
    required_identity = {
        "experiment_id",
        "run_id",
        "episode_id",
        "replication_id",
        "intent_id",
        "workload_id",
        "variant_id",
        "task_id",
        "configuration_id",
    }
    assert required_identity <= episode.keys()
    assert episode["replication_id"] == 3
    assert episode["variant_id"] == episode["variant"]
    assert episode["task_id"] == episode["task_family"]
    assert Path(episode["provenance_path"]).name == f"{episode['episode_id']}.jsonl"

    trace_events = [
        json.loads(line)
        for line in Path(episode["provenance_path"]).read_text(encoding="utf-8").splitlines()
    ]
    assert trace_events
    assert all(event["episode_identity"]["episode_id"] == episode["episode_id"] for event in trace_events)

    written = [json.loads(line) for line in episodes_path.read_text(encoding="utf-8").splitlines()]
    assert written[0]["episode_id"] == episode["episode_id"]
    assert written[0]["replication_id"] == 3


def test_runner_generates_distinct_run_identity_when_one_is_not_supplied(tmp_path: Path):
    pair = {
        "intent_id": "RF-RUN-ID",
        "clean_requirement": "Return eligible orders within 30 days.",
        "smelly_requirement": "Return old orders soon.",
        "smell": {"type": "vague_threshold"},
        "oracle_spec": {"codegen": {}, "test_gen": {}},
    }

    _metrics, first = run_eval_with_agent(
        StubAgent(),
        pairs=[pair],
        output_path=tmp_path / "first.json",
        traces_dir=tmp_path / "first-traces",
    )
    _metrics, second = run_eval_with_agent(
        StubAgent(),
        pairs=[pair],
        output_path=tmp_path / "second.json",
        traces_dir=tmp_path / "second-traces",
    )

    assert first[0]["run_id"] != second[0]["run_id"]
    assert first[0]["episode_id"] != second[0]["episode_id"]
