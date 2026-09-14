import json
import multiprocessing
import os
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor

import pytest

from eval.recoverable_calls import call_session, RecoveryBlocked, encoded, digest
from test_exploratory_cost import config, request


SCOPE = {"run_id": "fixture-run", "configuration_sha256": "a" * 64,
         "corpus_sha256": "b" * 64, "rubric_sha256": "c" * 64,
         "oracle_sha256": "d" * 64, "source_revision": "e" * 40,
         "pricing_sha256": "f" * 64}


class Provider:
    name = "openai"
    model = "openai-model"
    model_version = "openai-snapshot"

    def __init__(self):
        self.calls = 0
        self.last_call_metadata = {}

    def complete(self, request):
        self.calls += 1
        self.last_call_metadata = {"usage": {"input_tokens": 1, "output_tokens": 1},
                                   "response_model": self.model}
        return "private response"


def complete(session, provider, **kw):
    return session.complete(provider, request(), call_id=kw.get("call_id", "artifact:T1"),
                            phase="generation.T1")


def test_restart_replays_identical_response_without_charging_again(tmp_path):
    provider = Provider()
    path = tmp_path / "calls"
    with call_session(path, config(), SCOPE) as session:
        assert complete(session, provider) == "private response"
        spent = session.ledger.report()["spent_microusd"]
        head = session.ledger.ledger_head_hash
    with call_session(path, config(), SCOPE) as session:
        assert complete(session, provider) == "private response"
        assert session.last_replayed is True
        assert session.ledger.ledger_head_hash == head
        assert session.ledger.report()["spent_microusd"] == spent > 0
        complete(session, provider, call_id="next:T1")
    assert provider.calls == 2


def test_durable_response_reconciles_after_interrupt_before_cost(tmp_path, monkeypatch):
    path = tmp_path / "calls"
    provider = Provider()
    with call_session(path, config(), SCOPE) as session:
        def interrupt(*args, **kwargs):
            raise KeyboardInterrupt()
        monkeypatch.setattr(session.ledger, "reconcile_response", interrupt)
        with pytest.raises(KeyboardInterrupt):
            complete(session, provider)
        with pytest.raises(RecoveryBlocked):
            complete(session, provider, call_id="another")
    with call_session(path, config(), SCOPE) as session:
        assert session.ledger.report()["pending_attempt_count"] == 0
        assert session.ledger.report()["spent_microusd"] > 0
        assert complete(session, provider) == "private response"
    assert provider.calls == 1


def test_remote_acceptance_without_response_never_retries_or_edits_ledger(tmp_path):
    class Interrupted(Provider):
        def complete(self, request):
            self.calls += 1
            raise KeyboardInterrupt()
    path = tmp_path / "calls"
    provider = Interrupted()
    with call_session(path, config(), SCOPE) as session:
        with pytest.raises(KeyboardInterrupt):
            complete(session, provider)
    before = {p.name: p.read_bytes() for p in path.iterdir()}
    with pytest.raises(RecoveryBlocked, match="ambiguous"):
        with call_session(path, config(), SCOPE):
            pytest.fail("must block before provider construction")
    assert before == {p.name: p.read_bytes() for p in path.iterdir()}
    assert provider.calls == 1


@pytest.mark.parametrize("change", ["request", "model", "scope", "config", "response"])
def test_changed_identity_or_evidence_blocks_replay(tmp_path, change):
    path = tmp_path / "calls"
    provider = Provider()
    with call_session(path, config(), SCOPE) as session:
        complete(session, provider)
    scope = dict(SCOPE)
    configuration = config()
    if change == "scope":
        scope["oracle_sha256"] = "0" * 64
    if change == "config":
        configuration = config(cap="0.50")
    if change == "response":
        target = next(path.glob("*.response.json"))
        target.write_bytes(target.read_bytes().replace(b"private response", b"changed response"))
    with pytest.raises((RecoveryBlocked, ValueError)):
        with call_session(path, configuration, scope) as session:
            if change == "model":
                provider.model = "other-model"
            req = replace(request(), prompt="changed") if change == "request" else request()
            session.complete(provider, req, call_id="artifact:T1", phase="generation.T1")
    assert provider.calls == 1


def test_same_session_concurrent_duplicates_make_one_call(tmp_path):
    provider = Provider()
    with call_session(tmp_path / "calls", config(), SCOPE) as session:
        with ThreadPoolExecutor(2) as pool:
            assert list(pool.map(lambda _: complete(session, provider), range(2))) == ["private response"] * 2
    assert provider.calls == 1


@pytest.mark.parametrize("limits", [{"max_total_bytes": 1}, {"max_calls": 0}, {"deadline_seconds": -1}])
def test_limits_block_before_call(tmp_path, limits):
    provider = Provider()
    with pytest.raises(ValueError):
        with call_session(tmp_path / "calls", config(), SCOPE, **limits) as session:
            complete(session, provider)
    assert provider.calls == 0


def test_two_writers_cannot_open_same_session(tmp_path):
    path = tmp_path / "calls"
    with call_session(path, config(), SCOPE):
        with pytest.raises(BlockingIOError):
            with call_session(path, config(), SCOPE):
                pytest.fail("second writer")


def test_rehashed_usage_cannot_disagree_with_existing_cost_record(tmp_path):
    path = tmp_path / "calls"
    with call_session(path, config(), SCOPE) as session:
        complete(session, Provider())
    response = next(path.glob("*.response.json"))
    value = json.loads(response.read_text())
    value["metadata"]["usage"]["input_tokens"] = 2
    value.pop("sha256")
    value["sha256"] = digest(value)
    response.write_bytes(encoded(value))
    with pytest.raises(RecoveryBlocked, match="usage differs"):
        with call_session(path, config(), SCOPE):
            pass


def test_oversized_response_poisoned_session_cannot_dispatch_again(tmp_path):
    provider = Provider()
    path = tmp_path / "calls"
    with call_session(path, config(), SCOPE, max_response_bytes=1) as session:
        with pytest.raises(RecoveryBlocked, match="response exceeds"):
            complete(session, provider)
        with pytest.raises(RecoveryBlocked, match="reopen"):
            complete(session, provider, call_id="different")
    with pytest.raises(RecoveryBlocked, match="ambiguous"):
        with call_session(path, config(), SCOPE, max_response_bytes=1):
            pass
    assert provider.calls == 1


def abrupt_call_worker(path, boundary):
    """Exit without finally/atexit handlers, after a fixture-only remote call."""
    class AbruptProvider(Provider):
        def complete(self, request):
            response = super().complete(request)
            if boundary == "remote_acceptance":
                os._exit(91)
            return response

    with call_session(path, config(), SCOPE) as session:
        reconcile = session.ledger.reconcile_response

        def terminate(*args, **kwargs):
            if boundary == "after_cost":
                reconcile(*args, **kwargs)
            os._exit(91)

        session.ledger.reconcile_response = terminate
        complete(session, AbruptProvider())


@pytest.mark.parametrize("boundary", ["remote_acceptance", "before_cost", "after_cost"])
def test_abrupt_process_exit_preserves_recovery_boundary(tmp_path, boundary):
    path = tmp_path / "calls"
    child = multiprocessing.get_context("spawn").Process(
        target=abrupt_call_worker, args=(path, boundary))
    child.start()
    try:
        child.join(10)
        assert child.exitcode == 91
    finally:
        if child.is_alive():
            child.kill()
            child.join(5)
    before = {p.name: p.read_bytes() for p in path.iterdir()}
    if boundary == "remote_acceptance":
        with pytest.raises(RecoveryBlocked, match="ambiguous"):
            with call_session(path, config(), SCOPE):
                pytest.fail("unknown remote outcome must not resume")
        assert before == {p.name: p.read_bytes() for p in path.iterdir()}
        return
    provider = Provider()
    with call_session(path, config(), SCOPE) as session:
        assert complete(session, provider) == "private response"
        assert session.last_replayed
        assert provider.calls == 0
        assert session.ledger.report()["pending_attempt_count"] == 0
        assert session.ledger.report()["spent_microusd"] > 0
        assert sum(e["event_type"] == "reconciliation" for e in session.ledger.events) == 1
        if boundary == "after_cost":
            assert before == {p.name: p.read_bytes() for p in path.iterdir()}
        complete(session, provider, call_id="next:T1")
        assert provider.calls == 1
