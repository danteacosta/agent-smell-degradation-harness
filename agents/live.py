from __future__ import annotations

import os
from typing import Any


class NotConfiguredError(Exception):
    """Raised when live LLM adapter dependencies or credentials are missing."""


def _resolve_api_key() -> str | None:
    return os.environ.get("AGENT_LIVE_API_KEY") or os.environ.get("OPENAI_API_KEY")


def _openai_available() -> bool:
    try:
        import openai  # noqa: F401

        return True
    except ImportError:
        return False


class LiveAgent:
    """Optional live LLM adapter; requires `[live]` extra and an API key."""

    def __init__(self, *, model: str = "gpt-4o-mini", provider: str = "openai") -> None:
        if not _openai_available():
            raise NotConfiguredError(
                "openai package not installed; install with pip install -e '.[live]'"
            )
        api_key = _resolve_api_key()
        if not api_key:
            raise NotConfiguredError(
                "Missing API key; set OPENAI_API_KEY or AGENT_LIVE_API_KEY"
            )
        self.model = model
        self.provider = provider
        self._api_key = api_key

    def generate(self, pair: dict, variant: str, task_family: str) -> dict[str, Any]:
        raise NotConfiguredError(
            "LiveAgent.generate is not implemented for offline Tier 2; "
            "use StubAgent or enable live experiment mode"
        )
