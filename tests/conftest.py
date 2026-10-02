"""Shared pytest configuration.

The files in SLOW_FILES belong to completed evaluator-development studies
(qualification, addressed comparison, exploratory pre-pilot).  Together they
took about 90% of a full run's test time in a 2026-10-02 timing run, so they
carry the ``slow`` marker: ``make test-fast`` skips them for everyday work,
while ``make test`` and CI still run everything.
"""
from __future__ import annotations

import pytest

SLOW_FILES = frozenset({
    "test_qualification_live.py",
    "test_qualification_custody.py",
    "test_qualification_plan.py",
    "test_addressed_comparison_live.py",
    "test_exploratory_prepilot.py",
    "test_addressed_comparison_custody.py",
    "test_addressed_comparison_audit.py",
    "test_addressed_comparison_plan.py",
    "test_pilot_runtime.py",
})


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        if item.path.name in SLOW_FILES:
            item.add_marker(pytest.mark.slow)
