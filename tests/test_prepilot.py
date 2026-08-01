from __future__ import annotations

import pytest

from eval.prepilot import _twelve_intents, run_pre_pilot


def test_prepilot_rejects_seed_with_fewer_than_twelve_independent_intents():
    with pytest.raises(ValueError, match="12 independent source intents"):
        _twelve_intents()


def test_offline_prepilot_rejects_incomplete_seed_before_execution(tmp_path):
    with pytest.raises(ValueError, match="12 independent source intents"):
        run_pre_pilot(output_root=tmp_path, run_id="prepilot-fixed")
