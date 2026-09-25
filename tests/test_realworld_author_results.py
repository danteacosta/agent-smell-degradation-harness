import hashlib
import json
from pathlib import Path
import shutil

import pytest

from scripts import realworld_author_results as results


PUBLIC = (
    results.ROOT
    / "data/behavioral-expansion/realworld-author-ui-results-20260925"
)


def _reseal(directory: Path) -> None:
    receipt = {"files": results.inventory(directory, exclude={"receipt.json"})}
    (directory / "receipt.json").write_bytes(results.json_bytes(receipt))


def test_checked_in_public_bundle_validates_without_private_source() -> None:
    manifest = results.validate_public(PUBLIC)
    assert manifest["status"] == "bounded_exploratory_second_project_e2e"
    assert manifest["claims"]["finding"] == "heterogeneous_effect"
    assert manifest["claims"]["h1_supported"] is False
    assert manifest["claims"]["h2_supported"] is False
    assert manifest["audit"]["models"] == {
        "gpt-5.6-luna": 9,
        "gpt-5.6-sol": 9,
    }


def test_public_surface_excludes_private_generation_material() -> None:
    files = set(results.inventory(PUBLIC))
    assert files == {
        "analysis.json", "ledger.json", "manifest.json", "receipt.json",
        "screenshots/luna-b-unknown-author.png",
        "screenshots/luna-c-failure-nonauthor.png",
        "screenshots/sol-a-failure-nonauthor.png",
        "screenshots/sol-c-pass-nonauthor.png",
    }
    assert not files & {"prompt-bundle.json", "app.html", "stdout.jsonl"}
    text = "\n".join(
        path.read_text()
        for path in PUBLIC.glob("*.json")
    )
    assert "/Users/" not in text
    assert "private-research-evidence" not in text


@pytest.mark.parametrize("attack", ["claim", "denominator", "screenshot"])
def test_self_consistent_public_tampering_fails_approved_receipt(
    tmp_path: Path, attack: str
) -> None:
    target = tmp_path / "results"
    shutil.copytree(PUBLIC, target)
    if attack == "claim":
        path = target / "manifest.json"
        value = json.loads(path.read_text())
        value["claims"]["h1_supported"] = True
        path.write_bytes(results.json_bytes(value))
    elif attack == "denominator":
        ledger_path = target / "ledger.json"
        ledger = json.loads(ledger_path.read_text())
        ledger["rows"].pop()
        ledger["recorded_rows"] = 17
        ledger_path.write_bytes(results.json_bytes(ledger))
        manifest_path = target / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["ledger_sha256"] = hashlib.sha256(ledger_path.read_bytes()).hexdigest()
        manifest_path.write_bytes(results.json_bytes(manifest))
    else:
        sample = target / "screenshots/luna-c-failure-nonauthor.png"
        sample.write_bytes(sample.read_bytes() + b"tamper")
        manifest_path = target / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["samples"][0]["sha256"] = results.digest(sample)
        manifest_path.write_bytes(results.json_bytes(manifest))
    _reseal(target)
    with pytest.raises(ValueError, match="approved public receipt"):
        results.validate_public(target)


@pytest.mark.parametrize("attack", ["denominator", "models", "contrast", "unknown"])
def test_claim_validator_rejects_fixed_denominator_and_claim_drift(attack: str) -> None:
    ledger = json.loads((PUBLIC / "ledger.json").read_text())
    analysis = json.loads((PUBLIC / "analysis.json").read_text())
    if attack == "denominator":
        ledger["rows"].pop()
    elif attack == "models":
        ledger["rows"][0]["model"] = "gpt-5.6-sol"
    elif attack == "contrast":
        next(
            row for row in analysis["contrasts"]
            if row["model"] == "gpt-5.6-luna" and row["comparison"] == "C-A"
        )["difference_bounds"] = [0.0, 0.0]
    else:
        row = next(row for row in ledger["rows"] if row["target_failed"] is None)
        row["slot_id"] = "rw-forged"
    with pytest.raises(ValueError, match="denominator|allocation|contrast|unknown"):
        results._validate_claims(ledger, analysis)
