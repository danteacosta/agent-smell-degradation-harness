"""Executable v8 screening round for natural requirements-smell data.

The runner is intentionally conservative: it can complete an offline
source-label screening run, but it fails closed rather than pretending that
source markers, a stub, or a simulation are expert/model evidence.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from baselines.natural_smell import (
    BASELINE_VERSION,
    SUPPORTED_FAMILIES,
    evaluate_source_label_screening,
)
from eval.splits import build_grouped_split_manifest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "requirements-smell-natural-screening/v1"
_REQUIRED_FIELDS = (
    "case_id",
    "source_dataset",
    "source_dataset_commit",
    "source_file",
    "source_row",
    "source_file_sha256",
    "source_file_ref",
    "license_status",
    "redistribution_allowed",
    "derivative_use_allowed",
    "permission_record",
    "source_intent_id",
    "project_id",
    "requirement_text",
    "target_family",
    "source_label",
    "source_label_type",
    "source_smell_markers",
    "expert_annotation_status",
    "paraphrase_status",
)
_PARAPHRASE_REPLACEMENTS = (
    ("quickly", "in a short amount of time"),
    ("easily", "without specialist training"),
    ("appropriate", "suitable for the intended context"),
    ("regularly", "at a recurring interval"),
    ("normally", "under ordinary operating conditions"),
    ("possible", "feasible under the stated conditions"),
    ("sufficient", "meeting the stated minimum threshold"),
    ("may", "is permitted to"),
    ("might", "is permitted to"),
    ("could", "is capable of"),
    ("should", "is required to"),
    ("support", "provide the stated capability for"),
    ("handle", "process according to the stated rule"),
    ("provide", "make available"),
)


def load_validation_cases(
    path: str | Path, *, allow_private_source: bool = False
) -> list[dict[str, Any]]:
    """Load strict JSONL cases and enforce provenance/label boundaries."""

    target = Path(path)
    if not target.is_file():
        raise ValueError(f"validation corpus does not exist: {target}")
    cases: list[dict[str, Any]] = []
    seen: set[str] = set()
    for line_number, line in enumerate(target.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON at corpus line {line_number}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"corpus line {line_number} must be an object")
        missing = [field for field in _REQUIRED_FIELDS if field not in value]
        if missing:
            raise ValueError(f"corpus line {line_number} missing required field(s): {', '.join(missing)}")
        case_id = str(value["case_id"]).strip()
        if not case_id:
            raise ValueError(f"corpus line {line_number} has empty case_id")
        if case_id in seen:
            raise ValueError(f"duplicate case_id: {case_id}")
        seen.add(case_id)
        if not str(value["project_id"]).strip():
            raise ValueError(f"case {case_id} has empty project_id")
        if not str(value["requirement_text"]).strip():
            raise ValueError(f"case {case_id} has empty requirement_text")
        if value["source_label"] not in {"clean", "smelly"}:
            raise ValueError(f"case {case_id} has invalid source_label")
        if not isinstance(value["source_smell_markers"], list):
            raise ValueError(f"case {case_id} source_smell_markers must be a list")
        if not str(value["source_label_type"]).strip():
            raise ValueError(f"case {case_id} has empty source_label_type")
        license_status = str(value["license_status"]).strip()
        can_redistribute = value["redistribution_allowed"] is True
        can_transform = value["derivative_use_allowed"] is True
        has_permission_record = bool(str(value["permission_record"]).strip())
        if not can_redistribute or not can_transform:
            if not allow_private_source or license_status != "private_use_only":
                raise ValueError(
                    f"case {case_id} lacks redistribution/derivative-use permission; "
                    "use an approved source or explicit private-source execution"
                )
        elif license_status not in {"redistributable", "permission_recorded"} or not has_permission_record:
            raise ValueError(f"case {case_id} has incomplete license permission record")
        cases.append(dict(value))
    if not cases:
        raise ValueError("validation corpus is empty")
    return cases


def validate_case_set(
    cases: Sequence[Mapping[str, Any]],
    *,
    supported_families: Sequence[str] = SUPPORTED_FAMILIES,
    minimum_per_family: int = 10,
    minimum_clean_per_family: int = 10,
) -> dict[str, Any]:
    """Validate family quotas and return descriptive corpus counts."""

    if minimum_per_family < 1 or minimum_clean_per_family < 1:
        raise ValueError("minimum family quotas must be positive")
    families = tuple(supported_families)
    if not cases:
        raise ValueError("validation corpus is empty")
    counts: dict[str, dict[str, Any]] = {}
    for family in families:
        selected = [case for case in cases if case.get("target_family") == family]
        positives = sum(case.get("source_label") == "smelly" for case in selected)
        clean_controls = sum(case.get("source_label") == "clean" for case in selected)
        projects = sorted({str(case.get("project_id")) for case in selected})
        counts[family] = {
            "positive": positives,
            "clean_control": clean_controls,
            "case_count": len(selected),
            "project_count": len(projects),
            "projects": projects,
        }
        for case in selected:
            marker_count = len(case.get("source_smell_markers", []))
            if case.get("source_label") == "clean" and marker_count:
                raise ValueError(f"{case['case_id']} is not a clean control: source markers are present")
            if case.get("source_label") == "smelly" and marker_count != 1:
                raise ValueError(f"{case['case_id']} is not a single-marker positive")
        if positives < minimum_per_family:
            raise ValueError(
                f"{family} positive quota is {positives}; requires at least {minimum_per_family} positive quota cases"
            )
        if clean_controls < minimum_clean_per_family:
            raise ValueError(
                f"{family} clean quota is {clean_controls}; requires at least {minimum_clean_per_family} clean controls"
            )
    return {
        "supported_families": list(families),
        "minimum_positive_per_family": minimum_per_family,
        "minimum_clean_per_family": minimum_clean_per_family,
        "family_counts": counts,
        "case_count": len(cases),
        "project_count": len({str(case["project_id"]) for case in cases}),
        "underrepresented_families": [
            "comparative",
            "negative",
            "superlative",
            "loophole",
        ],
    }


def build_validation_split(cases: Sequence[Mapping[str, Any]], *, seed: int = 20260826) -> dict[str, Any]:
    """Build a deterministic project-disjoint train/calibration/test manifest."""

    manifest = build_grouped_split_manifest(
        cases,
        seed=seed,
        train_fraction=0.3,
        calibration_fraction=0.2,
        test_fraction=0.5,
        min_groups_per_split=1,
    )
    projects_by_split: dict[str, set[str]] = {"train": set(), "calibration": set(), "test": set()}
    for row in manifest["assignments"]:
        projects_by_split[str(row["split"])].add(str(row["project_id"]))
    overlaps = [
        {"left": left, "right": right, "projects": sorted(projects_by_split[left] & projects_by_split[right])}
        for index, left in enumerate(("train", "calibration", "test"))
        for right in ("train", "calibration", "test")[index + 1 :]
        if projects_by_split[left] & projects_by_split[right]
    ]
    if overlaps:
        raise ValueError(f"project-disjoint split violated: {overlaps}")
    manifest["project_assignments"] = {split: sorted(projects) for split, projects in projects_by_split.items()}
    return manifest


def _split_cases(cases: Sequence[Mapping[str, Any]], manifest: Mapping[str, Any]) -> list[dict[str, Any]]:
    assignments = {
        (str(row["source_intent_id"]), str(row["project_id"])): str(row["split"])
        for row in manifest.get("assignments", [])
    }
    result: list[dict[str, Any]] = []
    for case in cases:
        key = (str(case["source_intent_id"]), str(case["project_id"]))
        split = assignments.get(key)
        if split is None:
            raise ValueError(f"case {case['case_id']} has no project split assignment")
        result.append({**dict(case), "_split": split})
    return result


def _replace_once(text: str, old: str, new: str) -> str:
    return re.sub(rf"(?<![A-Za-z0-9]){re.escape(old)}(?![A-Za-z0-9])", new, text, count=1, flags=re.IGNORECASE)


def generate_paraphrase_probe(cases: Sequence[Mapping[str, Any]], *, max_cases: int = 40) -> list[dict[str, Any]]:
    """Generate controlled probes that are explicitly excluded from primary metrics."""

    probes: list[dict[str, Any]] = []
    for case in list(cases)[:max_cases]:
        original = str(case["requirement_text"])
        paraphrase = original
        replacement_used = None
        for old, new in _PARAPHRASE_REPLACEMENTS:
            candidate = _replace_once(original, old, new)
            if candidate != original:
                paraphrase = candidate
                replacement_used = {"from": old, "to": new}
                break
        if paraphrase == original:
            paraphrase = re.sub(r"\bsystem\b", "service", original, count=1, flags=re.IGNORECASE)
        probes.append(
            {
                "probe_id": f"paraphrase-{case['case_id']}",
                "case_id": case["case_id"],
                "target_family": case["target_family"],
                "original_text": original,
                "paraphrase_text": paraphrase,
                "replacement": replacement_used,
                "paraphrase_status": "controlled_probe_unvalidated",
                "primary_metric_eligible": False,
                "exclusion_reason": "no independent label for rewritten text",
            }
        )
    return probes


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def summarize_v7_agent_conditions(v7_bundle: str | Path | None = None) -> dict[str, Any]:
    """Summarize observed v7 outcomes as a simulation-only condition control."""

    bundle = Path(v7_bundle) if v7_bundle else REPO_ROOT / "artifacts" / "experiments" / "runs" / "discovery-20260826-v7"
    episodes = _load_jsonl(bundle / "episodes.jsonl")
    labels = _load_jsonl(bundle / "verification" / "labels.jsonl")
    if not episodes or not labels:
        return {
            "status": "not_available",
            "simulation_only": True,
            "reason": "v7 behavior or verification artifacts were not found",
        }
    episode_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    label_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in episodes:
        if row.get("task_family") == "behavior_codegen":
            key = (str(row.get("workload_id")), str(row.get("variant")), str(row.get("task_family")))
            episode_by_key.setdefault(key, row)
    for row in labels:
        if row.get("task_family") == "behavior_codegen":
            workload = row.get("workload_id", row.get("intent_id"))
            key = (str(workload), str(row.get("variant")), str(row.get("task_family")))
            label_by_key.setdefault(key, row)
    rows = []
    for key, episode in sorted(episode_by_key.items()):
        label = label_by_key.get(key, {})
        rows.append(
            {
                "workload_id": key[0],
                "variant": key[1],
                "observed_oracle_passed": bool(episode.get("oracle_passed")),
                "verifier_decision": label.get("decision"),
                "alert": label.get("decision") not in {None, "approve"},
            }
        )
    if not rows:
        return {"status": "not_available", "simulation_only": True, "reason": "no v7 behavior rows"}

    observed_successes = sum(row["observed_oracle_passed"] for row in rows)
    flagged_failures = sum(row["alert"] and not row["observed_oracle_passed"] for row in rows)
    total = len(rows)
    conditions = {
        "no_verifier": {
            "observed_successes": observed_successes,
            "total_cases": total,
            "success_rate": observed_successes / total,
            "alert_count": 0,
            "simulation_only": True,
        },
        "verifier_alert": {
            "observed_successes": observed_successes,
            "total_cases": total,
            "success_rate": observed_successes / total,
            "alert_count": sum(row["alert"] for row in rows),
            "simulation_only": True,
            "interpretation": "alert was observed but was not connected to a revision action",
        },
        "verifier_alert_plus_revision": {
            "observed_successes": observed_successes + flagged_failures,
            "total_cases": total,
            "success_rate": (observed_successes + flagged_failures) / total,
            "alert_count": sum(row["alert"] for row in rows),
            "hypothetical_repaired_failures": flagged_failures,
            "simulation_only": True,
            "interpretation": "upper-bound control assuming every flagged failed case is perfectly repaired",
        },
    }
    return {
        "status": "simulation_only",
        "simulation_only": True,
        "source_run": bundle.name,
        "unique_behavior_cases": total,
        "conditions": conditions,
    }


def readiness_report(model_runs: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    """Report whether external prerequisites for confirmatory evidence exist."""

    runs = list(model_runs or [])
    model_slots = [
        {"model_id": "openai-primary", "provider": "openai", "status": "not_run"},
        {"model_id": "anthropic-primary", "provider": "anthropic", "status": "not_run"},
    ]
    if runs:
        model_slots = [dict(run) for run in runs]
    blocking_reasons: list[str] = []
    if not all(slot.get("status") == "completed" for slot in model_slots):
        blocking_reasons.append("real_models")
    blocking_reasons.append("expert_annotation")
    return {
        "confirmatory_ready": not blocking_reasons,
        "status": "blocked_until_external_validation" if blocking_reasons else "confirmatory_ready",
        "expert_annotation_status": "pending",
        "required_annotators": 2,
        "duplicate_subset_fraction": 0.20,
        "real_model_runs": sum(slot.get("status") == "completed" for slot in model_slots),
        "model_slots": model_slots,
        "blocking_reasons": blocking_reasons,
    }


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.write_text("".join(json.dumps(dict(row), sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _write_metrics_csv(path: Path, screening: Mapping[str, Mapping[str, Any]]) -> None:
    lines = ["family,split,n,tp,fp,tn,fn,precision,recall,specificity,f1,evaluable\n"]
    for family in SUPPORTED_FAMILIES:
        result = screening[family]
        confusion = result["confusion"]
        metrics = result["metrics"]
        stratum = result["test_stratum"]
        values = [
            family,
            result["split"],
            result["case_count"],
            confusion["tp"],
            confusion["fp"],
            confusion["tn"],
            confusion["fn"],
            metrics["precision"],
            metrics["recall"],
            metrics["specificity"],
            metrics["f1"],
            stratum["evaluable"],
        ]
        lines.append(",".join(str(value) for value in values) + "\n")
    path.write_text("".join(lines), encoding="utf-8")


def _write_baseline_svg(path: Path, screening: Mapping[str, Mapping[str, Any]]) -> None:
    width, height = 900, 390
    left, top, chart_width, chart_height = 180, 45, 660, 260
    bar_width = chart_width / len(SUPPORTED_FAMILIES) / 2.8
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="20" y="25" font-family="sans-serif" font-size="18" font-weight="bold">ARTA source-label screening: precision and recall</text>',
    ]
    for tick in range(0, 6):
        y = top + chart_height - tick * chart_height / 5
        value = tick / 5
        elements.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + chart_width}" y2="{y:.1f}" stroke="#dddddd"/>')
        elements.append(f'<text x="{left - 12}" y="{y + 4:.1f}" text-anchor="end" font-family="sans-serif" font-size="11">{value:.1f}</text>')
    for index, family in enumerate(SUPPORTED_FAMILIES):
        result = screening[family]
        x = left + (index + 0.5) * chart_width / len(SUPPORTED_FAMILIES)
        precision = result["metrics"]["precision"] or 0.0
        recall = result["metrics"]["recall"] or 0.0
        for offset, value, color in ((-bar_width / 2, precision, "#4472c4"), (bar_width / 2, recall, "#ed7d31")):
            bar_height = value * chart_height
            elements.append(f'<rect x="{x + offset - bar_width / 2:.1f}" y="{top + chart_height - bar_height:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" fill="{color}"/>')
        label = family.replace("_", " ")
        elements.append(f'<text x="{x:.1f}" y="{top + chart_height + 18}" text-anchor="middle" font-family="sans-serif" font-size="10" transform="rotate(25 {x:.1f} {top + chart_height + 18})">{label}</text>')
    elements.extend([
        f'<rect x="{left + chart_width - 150}" y="{top - 25}" width="12" height="12" fill="#4472c4"/><text x="{left + chart_width - 132}" y="{top - 14}" font-family="sans-serif" font-size="11">precision</text>',
        f'<rect x="{left + chart_width - 70}" y="{top - 25}" width="12" height="12" fill="#ed7d31"/><text x="{left + chart_width - 52}" y="{top - 14}" font-family="sans-serif" font-size="11">recall</text>',
        '<text x="20" y="375" font-family="sans-serif" font-size="11">Descriptive agreement with ARTA source markers; not expert-validated detector efficacy.</text>',
        '</svg>',
    ])
    path.write_text("\n".join(elements) + "\n", encoding="utf-8")


def _write_report(
    path: Path,
    *,
    run: Mapping[str, Any],
    corpus_summary: Mapping[str, Any],
    split_manifest: Mapping[str, Any],
    screening: Mapping[str, Mapping[str, Any]],
    readiness: Mapping[str, Any],
) -> None:
    rows = [
        "# Requirements-smell validation round v8",
        "",
        "## Em linguagem simples",
        "",
        "Este experimento pega requisitos naturais do corpus ARTA e testa um baseline simples baseado em palavras/expressões. Ele serve para verificar se o pipeline consegue carregar dados, manter projetos separados, calcular métricas e deixar claro o que ainda não foi validado.",
        "",
        "Ele não prova que o detector entende o requisito, porque os rótulos usados nesta rodada são os marcadores do próprio ARTA e não uma anotação independente de especialistas.",
        "",
        "## O que foi executado",
        "",
        f"- Casos processados: **{run['case_count']}**, em **{run['project_count']} projetos**.",
        f"- Famílias: {', '.join(run['supported_families'])}.",
        "- Cada família tem 12 positivos de fonte e 12 controles sem marcador; controles podem ser reutilizados entre famílias.",
        f"- Split por projeto: treino={', '.join(split_manifest['project_assignments']['train'])}; calibração={', '.join(split_manifest['project_assignments']['calibration'])}; teste={', '.join(split_manifest['project_assignments']['test'])}.",
        "- Texto original: executado a partir de um arquivo privado local e redigido dos artefatos versionados.",
        "",
        "## Resultado do baseline no teste",
        "",
        "A tabela CSV e o gráfico SVG mostram a concordância com os marcadores da fonte. Use os denominadores e os intervalos Wilson no JSON; eles são intervalos binomiais descritivos e não corrigem dependência entre requisitos do mesmo projeto.",
        "",
        "| Família | TP | FP | TN | FN | Precisão | Recall | Avaliável |",
        "|---|---:|---:|---:|---:|---:|---:|:---:|",
    ]
    for family in SUPPORTED_FAMILIES:
        result = screening[family]
        confusion = result["confusion"]
        metrics = result["metrics"]
        rows.append(
            f"| {family} | {confusion['tp']} | {confusion['fp']} | {confusion['tn']} | {confusion['fn']} | {metrics['precision']} | {metrics['recall']} | {result['test_stratum']['evaluable']} |"
        )
    rows.extend([
        "",
        "## Condições do agente",
        "",
        "O artefato `agent_conditions.json` reaproveita o fixture comportamental v7 para comparar sem alerta, com alerta e com uma revisão hipotética perfeita. Isso é uma simulação/upper bound do pipeline; não é uma nova execução de agente nem uma chamada a modelo real.",
        "",
        "## O que falta para relevância",
        "",
        "- obter permissão escrita de redistribuição/transformação ou usar fontes explicitamente licenciadas;",
        "- substituir os marcadores ARTA por rótulos binários independentes, com dois anotadores, amostra duplicada e adjudicação;",
        "- executar pelo menos dois modelos reais, com prompts/versionamento, repetições, tokens, custo, latência e taxa de erro;",
        "- comparar agente sem verificador, com alerta e com oportunidade real de revisão em requisitos novos;",
        "- ampliar a diversidade de projetos e manter projetos inteiros fora da calibração.",
        "",
        f"**Status:** `{readiness['status']}`. O bundle está completo como triagem offline, mas bloqueado para evidência confirmatória.",
    ])
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def run_validation_round(
    corpus_path: str | Path,
    *,
    output_root: str | Path = REPO_ROOT / "artifacts" / "experiments" / "runs",
    run_id: str = "discovery-20260826-v8-screening",
    seed: int = 20260826,
    supported_families: Sequence[str] = SUPPORTED_FAMILIES,
    minimum_per_family: int = 10,
    minimum_clean_per_family: int = 10,
    v7_bundle: str | Path | None = None,
    allow_private_source: bool = False,
) -> dict[str, Any]:
    """Execute the offline screening round and materialize its artifact bundle."""

    cases = load_validation_cases(corpus_path, allow_private_source=allow_private_source)
    corpus_summary = validate_case_set(
        cases,
        supported_families=supported_families,
        minimum_per_family=minimum_per_family,
        minimum_clean_per_family=minimum_clean_per_family,
    )
    split_manifest = build_validation_split(cases, seed=seed)
    split_cases = _split_cases(cases, split_manifest)
    screening = evaluate_source_label_screening(split_cases, split="test")
    for family, result in screening.items():
        test_cases = [
            case
            for case in split_cases
            if case.get("target_family") == family and case.get("_split") == "test"
        ]
        test_positive = sum(case.get("source_label") == "smelly" for case in test_cases)
        test_clean = sum(case.get("source_label") == "clean" for case in test_cases)
        result["test_stratum"] = {
            "positive": test_positive,
            "clean_control": test_clean,
            "evaluable": test_positive >= 2 and test_clean >= 2,
            "minimum_per_class_for_evaluation": 2,
        }
    paraphrase_probe = generate_paraphrase_probe(split_cases)
    agent_conditions = summarize_v7_agent_conditions(v7_bundle)
    readiness = readiness_report()
    now = datetime.now(timezone.utc).isoformat()
    bundle = Path(output_root) / run_id
    bundle.mkdir(parents=True, exist_ok=True)
    redacted_cases = []
    for case in split_cases:
        redacted = {key: value for key, value in case.items() if key != "requirement_text"}
        redacted["requirement_text_sha256"] = hashlib.sha256(
            str(case["requirement_text"]).encode("utf-8")
        ).hexdigest()
        redacted_cases.append(redacted)
    _write_jsonl(bundle / "cases.jsonl", redacted_cases)
    _write_json(bundle / "corpus-manifest.json", {
        "schema_version": SCHEMA_VERSION,
        "status": "source_label_screening_not_expert_validated",
        "corpus_path": str(Path(corpus_path)),
        "summary": corpus_summary,
        "split_policy": "complete project held out",
        "source_dataset": str(cases[0]["source_dataset"]),
        "source_dataset_commit": str(cases[0]["source_dataset_commit"]),
        "source_file": str(cases[0]["source_file"]),
        "source_file_sha256": str(cases[0]["source_file_sha256"]),
        "source_label_type": "arta_dataset_marker",
        "expert_annotation_status": "pending",
        "source_text_redacted": True,
        "private_source_execution": allow_private_source,
        "license_statuses": sorted({str(case["license_status"]) for case in cases}),
    })
    _write_json(bundle / "splits.json", split_manifest)
    _write_json(bundle / "baseline_results.json", {
        "status": "descriptive_source_label_screening",
        "baseline_version": BASELINE_VERSION,
        "primary_split": "test",
        "results": screening,
        "estimand": "agreement_with_arta_source_labels",
        "primary_metric_exclusion": "source markers are not independent expert labels",
    })
    _write_json(bundle / "paraphrase_probe.json", {
        "status": "secondary_unvalidated_probe",
        "case_count": len(paraphrase_probe),
        "primary_metric_eligible_count": 0,
        "probes": paraphrase_probe,
    })
    _write_json(bundle / "agent_conditions.json", agent_conditions)
    _write_json(bundle / "readiness.json", readiness)
    run = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": now,
        "mode": "offline_screening",
        "status": readiness["status"],
        "evidence_level": "screening_only",
        "case_count": len(cases),
        "project_count": corpus_summary["project_count"],
        "supported_families": list(SUPPORTED_FAMILIES),
        "source_label_screening": True,
        "expert_annotation_status": "pending",
        "real_model_runs": 0,
        "private_source_execution": allow_private_source,
        "source_text_redacted_from_artifacts": True,
        "baseline_version": BASELINE_VERSION,
        "split_manifest": "splits.json",
        "artifacts": [
            "cases.jsonl",
            "corpus-manifest.json",
            "splits.json",
            "baseline_results.json",
            "paraphrase_probe.json",
            "agent_conditions.json",
            "readiness.json",
            "metrics.csv",
            "baseline-metrics.svg",
            "report.md",
        ],
    }
    _write_metrics_csv(bundle / "metrics.csv", screening)
    _write_baseline_svg(bundle / "baseline-metrics.svg", screening)
    _write_report(
        bundle / "report.md",
        run=run,
        corpus_summary=corpus_summary,
        split_manifest=split_manifest,
        screening=screening,
        readiness=readiness,
    )
    _write_json(bundle / "run.json", run)
    return run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", required=True, type=Path)
    parser.add_argument("--run-id", default="discovery-20260826-v8-screening")
    parser.add_argument("--output-root", default=REPO_ROOT / "artifacts" / "experiments" / "runs", type=Path)
    parser.add_argument("--v7-bundle", type=Path)
    parser.add_argument("--allow-private-source", action="store_true")
    args = parser.parse_args()
    result = run_validation_round(
        args.corpus,
        output_root=args.output_root,
        run_id=args.run_id,
        v7_bundle=args.v7_bundle,
        allow_private_source=args.allow_private_source,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
