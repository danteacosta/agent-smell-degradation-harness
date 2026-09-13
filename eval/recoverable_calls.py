"""Private response/cost reconciliation at the provider-call boundary.

This is not a T1--T3 checkpoint replay engine. It never reconstructs timestamps,
changes frozen inputs, or resolves an unobserved remote outcome by retrying it.
The owning process and local filesystem are trusted; hashes are not signatures.
"""
from contextlib import contextmanager
import argparse
from dataclasses import asdict
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import time
import threading

from eval.exploratory_cost import BudgetedProvider, CostLedger, _redacted_call_id


class RecoveryBlocked(ValueError):
    pass


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def durable_create(path, value):
    """Exclusive immutable receipt; partial writes remain visible and block reuse."""
    data = encoded(value)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, "wb", closefd=False) as stream:
            stream.write(data)
            stream.flush()
            os.fsync(fd)
    finally:
        os.close(fd)
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def read_record(path, limit):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode) or os.fstat(fd).st_size > limit:
            raise RecoveryBlocked("invalid or oversized recovery record")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            raw = stream.read(limit + 1)
        value = json.loads(raw)
        if raw != encoded(value):
            raise RecoveryBlocked("noncanonical or truncated recovery record")
        return value
    finally:
        os.close(fd)


class CallSession:
    def __init__(self, directory, configuration, scope, *, max_calls=4096,
                 max_response_bytes=4_194_304, max_total_bytes=268_435_456,
                 deadline_seconds=3600):
        for limit in (max_calls, max_response_bytes, max_total_bytes, deadline_seconds):
            if type(limit) is not int or limit <= 0:
                raise ValueError("resource limits must be positive integers")
        required = {"run_id", "configuration_sha256", "corpus_sha256", "rubric_sha256",
                    "oracle_sha256", "source_revision", "pricing_sha256"}
        if set(scope) != required or any(not isinstance(v, str) or not v for v in scope.values()):
            raise RecoveryBlocked("complete frozen scope is required")
        self.directory = directory
        self._lock = threading.RLock()
        self._failed = False
        self.max_calls, self.max_response_bytes = max_calls, max_response_bytes
        self.max_total_bytes = max_total_bytes
        self.deadline = time.monotonic() + deadline_seconds
        self.scope = {"schema": "recoverable-calls/v1", "scope": scope,
                      "cost_configuration_sha256": configuration.configuration_sha256,
                      "limits": [max_calls, max_response_bytes, max_total_bytes, deadline_seconds]}
        manifest = directory / "session.json"
        if manifest.exists():
            if read_record(manifest, 16384) != self.scope:
                raise RecoveryBlocked("frozen session scope or limits changed")
        else:
            if any(directory.iterdir()):
                raise RecoveryBlocked("unrecognized evidence directory")
            durable_create(manifest, self.scope)
        intents = sorted(directory.glob("*.intent.json"))
        if len(intents) > max_calls:
            raise RecoveryBlocked("call inventory limit exceeded")
        allowed = {"session.json", "cost-ledger.jsonl", "cost-ledger.jsonl.ready",
                   "cost-ledger.jsonl.ready.tmp", "cost-ledger.jsonl.fail-closed",
                   "cost-ledger.jsonl.fail-closed.tmp"}
        for path in directory.iterdir():
            if path.name not in allowed and not path.name.endswith((".intent.json", ".response.json")):
                raise RecoveryBlocked("unrecognized session entry")
        self.intents, self.responses = {}, {}
        for path in intents:
            item = read_record(path, 16384)
            key = (item["call_id"], item["attempt"])
            if (type(key[1]) is not int or key[1] < 1 or key in self.intents
                    or item["scope_sha256"] != digest(self.scope)
                    or path.name != self.filename(key, "intent")):
                raise RecoveryBlocked("invalid or duplicate call binding")
            self.intents[key] = item
        for path in directory.glob("*.response.json"):
            record = read_record(path, max_response_bytes + 32768)
            unsigned = {k: v for k, v in record.items() if k != "sha256"}
            key = (record["call_id"], record["attempt"])
            if (not isinstance(record["response"], str)
                    or len(record["response"].encode("utf-8")) > max_response_bytes
                    or key not in self.intents or record["sha256"] != digest(unsigned)
                    or record["intent_sha256"] != digest(self.intents[key])
                    or path.name != self.filename(key, "response")):
                raise RecoveryBlocked("response integrity or identity mismatch")
            self.responses[key] = record
        ledger_path = directory / "cost-ledger.jsonl"
        if self.intents and not ledger_path.exists():
            raise RecoveryBlocked("missing cost evidence; never recreate its budget")
        # Inspect only to refuse ambiguity before CostLedger's normal recovery
        # writes a terminal stop. CostLedger then validates hashes and arithmetic.
        reservations = {}
        if ledger_path.exists():
            if ledger_path.stat().st_size > 16_777_216:
                raise RecoveryBlocked("ledger size limit exceeded")
            for line in ledger_path.read_bytes().splitlines():
                event = json.loads(line)
                if event["event_type"] == "reservation":
                    key = (event["call_id"], event["attempt"])
                    if key not in self.intents or key not in self.responses:
                        raise RecoveryBlocked("ambiguous call: response/billing reconciliation required")
                    intent = self.intents[key]
                    if event["provider"] != intent["provider"] or event["phase"] != intent["phase"]:
                        raise RecoveryBlocked("ledger/response binding mismatch")
                    reservations[key] = event
        if set(self.responses) - set(reservations):
            raise RecoveryBlocked("response has no cost reservation")
        self.ledger = CostLedger(ledger_path, configuration, recovery_records=self.responses)
        if self.ledger.status not in {"ready", "running"}:
            raise RecoveryBlocked("terminal or unverified ledger cannot continue")
        reconciled = {(e["call_id"], e["attempt"]): e for e in self.ledger.events
                      if e["event_type"] == "reconciliation" and e.get("status") == "reconciled"}
        for key, record in self.responses.items():
            event = reconciled.get(key)
            usage = self.ledger._normalized_usage(record["metadata"].get("usage"))
            if event is None or event.get("outcome") != "success" or any(
                    event.get(k, 0) != v for k, v in usage.items()):
                raise RecoveryBlocked("response usage differs from reconciled cost")

    @staticmethod
    def filename(key, kind):
        return f"{digest(list(key))}.{kind}.json"

    def complete(self, provider, request, *, call_id, phase, attempt=1):
        with self._lock:
            return self._complete(provider, request, call_id=call_id, phase=phase, attempt=attempt)

    def _complete(self, provider, request, *, call_id, phase, attempt):
        if self._failed:
            raise RecoveryBlocked("reopen and reconcile the session after failure")
        if time.monotonic() >= self.deadline:
            raise RecoveryBlocked("session deadline reached before dispatch")
        if type(attempt) is not int or attempt < 1:
            raise ValueError("explicit positive attempt required")
        if len(encoded(asdict(request))) > 1_048_576:
            raise RecoveryBlocked("request exceeds replay hashing bound")
        key = (_redacted_call_id(call_id), attempt)
        intent = {"call_id": key[0], "attempt": attempt, "provider": provider.name,
                  "model": getattr(provider, "model", None),
                  "model_version": getattr(provider, "model_version", None),
                  "phase": phase, "request_sha256": digest(asdict(request)),
                  "scope_sha256": digest(self.scope)}
        if key in self.intents and self.intents[key] != intent:
            raise RecoveryBlocked("same call identity has different request or provider")
        if key in self.responses:
            self.last_replayed = True
            return self.responses[key]["response"]
        if any(e.get("call_id") == key[0] and e.get("attempt") == attempt
               and e["event_type"] == "reservation" for e in self.ledger.events):
            raise RecoveryBlocked("reserved call cannot be redispatched")
        if sum(p.stat().st_size for p in self.directory.iterdir()) + self.max_response_bytes + 32768 > self.max_total_bytes:
            raise RecoveryBlocked("insufficient evidence quota before dispatch")
        if key not in self.intents:
            if len(self.intents) >= self.max_calls:
                raise RecoveryBlocked("session call limit reached")
            durable_create(self.directory / self.filename(key, "intent"), intent)
            self.intents[key] = intent

        def persist(response, metadata):
            if not isinstance(response, str) or len(response.encode("utf-8")) > self.max_response_bytes:
                raise RecoveryBlocked("response exceeds frozen resource bound")
            if len(encoded(metadata)) > 16384:
                raise RecoveryBlocked("response metadata exceeds bound")
            record = {"call_id": key[0], "attempt": attempt, "intent_sha256": digest(intent),
                      "response": response, "metadata": metadata}
            record["sha256"] = digest(record)
            durable_create(self.directory / self.filename(key, "response"), record)
            # Do not mark reusable until cost reconciliation succeeds.

        try:
            result = BudgetedProvider(provider, self.ledger, response_sink=persist).complete(
                request, call_id=call_id, phase=phase, attempt=attempt)
        except BaseException:
            self._failed = True
            raise
        self.responses[key] = read_record(self.directory / self.filename(key, "response"),
                                         self.max_response_bytes + 32768)
        self.last_replayed = False
        return result


@contextmanager
def call_session(directory, configuration, scope, **limits):
    """One writer per private session; no implicit adoption of historical runs."""
    directory = Path(directory).absolute()
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
            raise RecoveryBlocked("session directory must be private and owned")
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for path in directory.iterdir():
            if path.is_symlink() or not path.is_file():
                raise RecoveryBlocked("unexpected recovery entry")
        os.fsync(fd)
        for parent in directory.parents:
            ancestor = os.open(parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                os.fsync(ancestor)
            finally:
                os.close(ancestor)
        yield CallSession(directory, configuration, scope, **limits)
    finally:
        os.close(fd)


def main():
    """Reconcile already durable response usage; never initialize a provider."""
    from eval.provider_runtime_config import load_exploratory_runtime_config
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True)
    parser.add_argument("--runtime-config", required=True)
    parser.add_argument("--scope", required=True)
    args = parser.parse_args()
    directory = Path(args.directory)
    if not (directory / "session.json").is_file():
        parser.error("only an existing recoverable-calls/v1 session can be reconciled")
    scope = json.loads(Path(args.scope).read_text())
    configuration = load_exploratory_runtime_config(args.runtime_config).cost_configuration()
    manifest = read_record(directory / "session.json", 16384)
    limits = dict(zip(("max_calls", "max_response_bytes", "max_total_bytes", "deadline_seconds"),
                      manifest["limits"], strict=True))
    with call_session(directory, configuration, scope, **limits) as session:
        print(json.dumps({"schema": "call-reconciliation-report/v1",
                          "reusable_response_count": len(session.responses),
                          "ledger": session.ledger.report(),
                          "scope_sha256": digest(session.scope),
                          "provider_calls_made": 0, "full_pipeline_resume_qualified": False}, indent=2))


if __name__ == "__main__":
    main()
