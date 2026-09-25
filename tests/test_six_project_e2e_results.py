import json
from pathlib import Path
import shutil

import pytest

from scripts import six_project_e2e_results as results


def test_public_result_bundle_revalidates() -> None:
    summary = results.validate(results.RESULTS_DIRECTORY)
    assert summary == {
        "planned": 72,
        "executable": 8,
        "unknown": 64,
        "pass": 6,
        "target_only_failure": 2,
    }


def test_changed_or_resealed_result_is_rejected(tmp_path: Path) -> None:
    copied = tmp_path / "results"
    shutil.copytree(results.RESULTS_DIRECTORY, copied)
    rows = json.loads((copied / "rows.json").read_text())
    rows[0]["category"] = "pass"
    (copied / "rows.json").write_text(json.dumps(rows) + "\n")
    with pytest.raises(ValueError, match="receipt|canonical"):
        results.validate(copied)
