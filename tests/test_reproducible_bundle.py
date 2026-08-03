from __future__ import annotations

import json
from pathlib import Path

from protocol.packaging import build_dissertation_bundle


def test_dissertation_bundle_declares_reproducibility_inputs(tmp_path: Path) -> None:
    bundle = build_dissertation_bundle(
        Path(__file__).parents[1],
        tmp_path / "work",
    )

    assert bundle["reproducibility"]["offline"] is True
    assert bundle["reproducibility"]["required_files"]
    assert bundle["reproducibility"]["analysis_version"]
