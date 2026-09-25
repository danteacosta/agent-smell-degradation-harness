import shutil

import pytest

from scripts import three_project_scaffold_results as results


def test_canonical_successor_results_validate() -> None:
    assert results.validate(results.RESULTS_DIRECTORY) == {
        "planned": 54,
        "executable": 53,
        "unknown": 1,
        "pass": 42,
        "target_only_failure": 11,
    }


def test_public_bundle_rejects_tampering(tmp_path) -> None:
    copy = tmp_path / "results"
    shutil.copytree(results.RESULTS_DIRECTORY, copy)
    (copy / "analysis.json").write_text("{}\n")
    with pytest.raises(ValueError, match="receipt inventory drift"):
        results.validate(copy)
