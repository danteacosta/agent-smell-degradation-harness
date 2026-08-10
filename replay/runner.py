from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from feature_plane.deployable import DeployableFeatureInput, extract_deployable_features

from .schema import (
    ARP_PACKAGE_VERSION,
    ARP_WIRE_VERSION,
    REPLAY_VERSION,
    ContractError,
    canonical_json_bytes,
    sha256_bytes,
    validate_bundle_mapping,
)

_EXIT_CODES = {"approve": 0, "warn": 10, "block": 20}
_FIXTURE_DIAGNOSTICS = {
    "latency-only": {"operational": {"latency_ms": 950.0}},
}


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read JSON {path}: {exc}") from exc


def _read_trace(path: Path) -> tuple[list[dict[str, Any]], bytes]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ContractError(f"cannot read trace {path}: {exc}") from exc
    events: list[dict[str, Any]] = []
    try:
        for line in raw.decode("utf-8").splitlines():
            if line.strip():
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ContractError("trace lines must be JSON objects")
                events.append(value)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"trace is not valid UTF-8 JSONL: {exc}") from exc
    return events, raw


def _build_bundle(root: Path, manifest: Mapping[str, Any], case: Mapping[str, Any]) -> dict[str, Any]:
    trace_name = case.get("trace")
    requirement_name = manifest.get("requirement", "requirement.json")
    if not isinstance(trace_name, str) or not isinstance(requirement_name, str):
        raise ContractError("manifest trace and requirement paths must be strings")
    events, raw = _read_trace(root / trace_name)
    actual_hash = sha256_bytes(raw)
    expected_hash = case.get("trace_sha256")
    if expected_hash and expected_hash != actual_hash:
        raise ContractError("trace_sha256 does not match raw trace bytes")
    merged_manifest = dict(manifest)
    merged_manifest.update({"case_id": case.get("case_id"), "trace_sha256": actual_hash})
    bundle = {
        "manifest": merged_manifest,
        "requirement": _read_json(root / requirement_name),
        "events": events,
        "_trace_raw": raw,
        "diagnostic": copy.deepcopy(_FIXTURE_DIAGNOSTICS.get(str(case.get("case_id")), {})),
    }
    return bundle


def load_fixture(case_id: str, fixtures_root: str | Path) -> dict[str, Any]:
    root = Path(fixtures_root)
    manifest = _read_json(root / "manifest.json")
    cases = manifest.get("cases") if isinstance(manifest, Mapping) else None
    case = next((item for item in cases or [] if item.get("case_id") == case_id), None)
    if case is None:
        raise ContractError(f"unknown fixture {case_id}")
    return _build_bundle(root, manifest, case)


def load_bundle(bundle_root: str | Path) -> dict[str, Any]:
    root = Path(bundle_root)
    manifest = _read_json(root / "manifest.json")
    if not isinstance(manifest, Mapping):
        raise ContractError("manifest must be an object")
    if isinstance(manifest.get("cases"), list):
        if len(manifest["cases"]) != 1:
            raise ContractError("arbitrary bundle must contain exactly one case")
        case = manifest["cases"][0]
    else:
        case = {
            "case_id": manifest.get("case_id", root.name),
            "trace": manifest.get("trace"),
            "trace_sha256": manifest.get("trace_sha256"),
        }
    return _build_bundle(root, manifest, case)


def _features(bundle: Mapping[str, Any]) -> dict[str, dict[str, float | int]]:
    requirement = bundle["requirement"]
    trace_path = Path("/dev/null")
    # The strict extractor accepts a path.  Keep the replay input in a short
    # temporary file only for this process; the file is not part of the report.
    import tempfile

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".jsonl") as handle:
        for event in bundle["events"]:
            handle.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")
        handle.flush()
        features = extract_deployable_features(
            DeployableFeatureInput(
                intent_id=str(bundle["manifest"].get("case_id", "replay-case")),
                requirement_text=str(requirement["text"]),
                task_family=str(requirement["task_family"]),
            ),
            handle.name,
        )
    return features


def _decision(features: Mapping[str, Mapping[str, float | int]]) -> tuple[str, list[dict[str, Any]]]:
    provenance = features["provenance"]
    constraints = int(provenance.get("constraint_count", 0))
    unresolved = int(provenance.get("unresolved_reference_count", 0))
    contradictions = int(provenance.get("contradiction_count", 0))
    checks = int(provenance.get("validation_check_count", 0))
    coverage = int(provenance.get("coverage_target_count", 0))
    errors = int(provenance.get("error_count", 0))
    if not constraints or contradictions or errors or not checks:
        return "block", [{
            "constraint": "requirement constraints",
            "checkpoint": "interpretation.completed",
            "confidence": 0.95,
            "recommended_action": "block",
        }]
    if unresolved or not coverage:
        return "warn", [{
            "constraint": "requirement constraints",
            "checkpoint": "interpretation.completed",
            "confidence": 0.55,
            "recommended_action": "clarify",
        }]
    return "approve", []


def _hash_projection(report: Mapping[str, Any]) -> dict[str, Any]:
    projection = copy.deepcopy(dict(report))
    projection.pop("report_sha256", None)
    baselines = projection.get("baselines")
    if isinstance(baselines, dict):
        baselines.pop("diagnostic", None)
    metadata = projection.get("metadata")
    if isinstance(metadata, dict):
        for key in ("path", "timestamp", "environment"):
            metadata.pop(key, None)
    return projection


def run_bundle(bundle: Mapping[str, Any]) -> dict[str, Any]:
    try:
        validated = validate_bundle_mapping(bundle)
        raw = bundle.get("_trace_raw")
        if not isinstance(raw, bytes):
            raw = "\n".join(json.dumps(event, ensure_ascii=False, separators=(",", ":")) for event in validated["events"]).encode("utf-8") + b"\n"
        trace_hash = sha256_bytes(raw)
        manifest_hash = validated["manifest"].get("trace_sha256")
        if manifest_hash and manifest_hash != trace_hash:
            raise ContractError("trace_sha256 does not match replay input")
        features = _features(validated)
        decision, evidence = _decision(features)
        diagnostic = copy.deepcopy(bundle.get("diagnostic") or {})
        diagnostic.setdefault("output_only", {"available": False, "source": "test-only-sidecar"})
        diagnostic.setdefault("operational", {"latency_ms": features["operational"].get("latency_ms", 0.0)})
        report: dict[str, Any] = {
            "schema_version": "constraint-replay/v1",
            "replay_version": REPLAY_VERSION,
            "arp_wire_version": ARP_WIRE_VERSION,
            "arp_package_version": ARP_PACKAGE_VERSION,
            "decision": decision,
            "exit_code": _EXIT_CODES[decision],
            "trace_sha256": trace_hash,
            "report_sha256": "",
            "features": features,
            "baselines": {
                "deployable": {
                    "constraint_count": features["provenance"].get("constraint_count", 0),
                    "validation_check_count": features["provenance"].get("validation_check_count", 0),
                    "coverage_target_count": features["provenance"].get("coverage_target_count", 0),
                },
                "diagnostic": diagnostic,
            },
            "semantic_evidence": evidence,
            "status": "non_confirmatory_demo",
            "metadata": {"case_id": validated["manifest"].get("case_id")},
        }
        report["report_sha256"] = sha256_bytes(canonical_json_bytes(_hash_projection(report)))
        return report
    except ContractError:
        raise
    except (TypeError, ValueError, OSError) as exc:
        raise ContractError(str(exc)) from exc


def run_fixture(case_id: str, fixtures_root: str | Path) -> dict[str, Any]:
    return run_bundle(load_fixture(case_id, fixtures_root))


def benchmark(fixtures_root: str | Path) -> dict[str, Any]:
    cases = ("clean", "constraint-loss", "constraint-warning", "negative-control", "latency-only")
    reports = {case_id: run_fixture(case_id, fixtures_root) for case_id in cases}
    negative = ("negative-control", "latency-only")
    false_alerts = sum(reports[case_id]["decision"] != "approve" for case_id in negative)
    return {
        "status": "non_confirmatory_demo",
        "cases": {case_id: reports[case_id]["decision"] for case_id in cases},
        "negative_cases": len(negative),
        "false_alerts": false_alerts,
        "false_alert_rate": false_alerts / len(negative),
        "reports": reports,
    }


def to_sarif(report: Mapping[str, Any], optional_extensions: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Serialize only trusted deployable fields to SARIF 2.1.0."""

    decision = str(report.get("decision", "invalid-contract"))
    rule_id = "constraint-contract" if decision == "invalid-contract" else "constraint-preservation"
    level = {"approve": "note", "warn": "warning", "block": "error"}.get(decision, "error")
    properties: dict[str, Any] = {
        "decision": decision,
        "exit_code": report.get("exit_code", 30),
        "trace_sha256": report.get("trace_sha256"),
        "evidence": report.get("semantic_evidence", []),
    }
    # Optional provider extensions are intentionally not copied.  This keeps
    # untrusted values out of both the decision and the serialized artifact.
    _ = optional_extensions
    result = {
        "ruleId": rule_id,
        "level": level,
        "message": {"text": f"constraint replay decision: {decision}"},
        "properties": properties,
    }
    return {
        "$schema": "https://json.schemastore.org/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {
                "name": "constraint-replay",
                "informationUri": "https://github.com/danteacosta/agent-smell-degradation-harness",
                "rules": [{"id": rule_id, "name": rule_id}],
            }},
            "results": [result],
        }],
    }
