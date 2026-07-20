from __future__ import annotations

from typing import Any


class MockTransport:
    """Offline transport that returns queued string responses."""

    def __init__(self, responses: list[str] | dict[str, list[str]]) -> None:
        if isinstance(responses, dict):
            self._queues: dict[str, list[str]] = {
                key: list(queue) for key, queue in responses.items()
            }
            self._mode = "dict"
        else:
            self._queue = list(responses)
            self._mode = "list"
        self._call_index = 0

    def complete(self, prompt: str) -> str:
        if self._mode == "list":
            if self._call_index >= len(self._queue):
                raise RuntimeError("MockTransport exhausted queued responses")
            response = self._queue[self._call_index]
            self._call_index += 1
            return response

        for key, queue in self._queues.items():
            if key in prompt and queue:
                return queue.pop(0)
        raise RuntimeError(f"MockTransport: no queued response for prompt containing known keys")

    @property
    def calls_made(self) -> int:
        if self._mode == "list":
            return self._call_index
        return sum(
            len(original) - len(remaining)
            for original, remaining in zip(
                self._queues.values(),
                [q for q in self._queues.values()],
                strict=False,
            )
        )
