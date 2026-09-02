from __future__ import annotations

from types import SimpleNamespace

import pytest

from agents.providers import (
    DeepSeekProvider,
    OpenAIProvider,
    ProviderRequest,
    estimate_provider_cost,
    normalize_provider_usage,
)


def _request() -> ProviderRequest:
    return ProviderRequest(
        prompt="return json",
        pair={"requirement": "bounded", "task_family": "test_gen", "output_keys": []},
        variant="opaque",
        task_family="test_gen",
    )


def _client(response):
    calls = []

    def create(**kwargs):
        calls.append(kwargs)
        return response

    return (
        SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(create=create),
            )
        ),
        calls,
    )


def test_openai_compatible_metadata_normalizes_usage_and_cost() -> None:
    response = SimpleNamespace(
        id="chatcmpl-test",
        model="resolved-model",
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content='{"ok": true}'),
            )
        ],
        usage=SimpleNamespace(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            prompt_tokens_details=SimpleNamespace(cached_tokens=10),
            completion_tokens_details=SimpleNamespace(reasoning_tokens=4),
        ),
    )
    client, calls = _client(response)
    provider = DeepSeekProvider(
        api_key="private",
        model="configured-model",
        client=client,
        input_usd_per_1k=0.01,
        cached_input_usd_per_1k=0.005,
        output_usd_per_1k=0.02,
    )

    assert provider.complete(_request()) == '{"ok": true}'
    assert calls[0]["model"] == "configured-model"
    assert calls[0]["temperature"] == 0.0
    assert calls[0]["max_tokens"] == 4096
    assert provider.last_call_metadata["usage"] == {
        "cached_tokens": 10,
        "completion_tokens": 50,
        "input_tokens": 100,
        "output_tokens": 50,
        "prompt_tokens": 100,
        "reasoning_tokens": 4,
        "total_tokens": 150,
    } or provider.last_call_metadata["usage"] == {
        "cached_tokens": 10,
        "input_tokens": 100,
        "output_tokens": 50,
        "reasoning_tokens": 4,
        "total_tokens": 150,
    }
    assert provider.last_call_metadata["response_model"] == "resolved-model"
    assert provider.last_call_metadata["response_id"] == "chatcmpl-test"
    assert provider.last_call_metadata["cost_usd"] == pytest.approx(0.00195)
    assert provider.base_url == "https://api.deepseek.com"


def test_usage_and_cost_are_provider_neutral() -> None:
    usage = normalize_provider_usage(
        {
            "input_tokens": 200,
            "output_tokens": 20,
            "input_tokens_details": {"cached_tokens": 50},
        }
    )
    assert usage == {
        "cached_tokens": 50,
        "input_tokens": 200,
        "output_tokens": 20,
        "total_tokens": 220,
    }
    assert estimate_provider_cost(
        usage,
        input_usd_per_1k=0.01,
        cached_input_usd_per_1k=0.005,
        output_usd_per_1k=0.02,
    ) == pytest.approx(0.00215)


def test_openai_default_does_not_pass_none_base_url_to_sdk() -> None:
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="{}"))],
        usage={"input_tokens": 1, "output_tokens": 1},
    )
    client, calls = _client(response)
    provider = OpenAIProvider(api_key="private", model="gpt-test", client=client)

    provider.complete(_request())

    assert provider.configuration_metadata()["base_url"] is None
    assert calls[0]["model"] == "gpt-test"


def test_openai_provider_uses_completion_token_parameter_for_current_models() -> None:
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="{}"))],
        usage={"input_tokens": 1, "output_tokens": 1},
    )
    client, calls = _client(response)
    provider = OpenAIProvider(
        api_key="private",
        model="gpt-5.4-mini-2026-03-17",
        client=client,
    )

    provider.complete(_request())

    assert calls[0]["max_completion_tokens"] == 4096
    assert "max_tokens" not in calls[0]
    assert calls[0]["response_format"] == {"type": "json_object"}


def test_openai_gpt56_luna_uses_default_temperature() -> None:
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="{}"))],
        usage={"input_tokens": 1, "output_tokens": 1},
    )
    client, calls = _client(response)
    provider = OpenAIProvider(
        api_key="private",
        model="gpt-5.6-luna",
        client=client,
    )

    provider.complete(_request())

    assert "temperature" not in calls[0]


def test_deepseek_v4_defaults_to_explicitly_disabled_thinking() -> None:
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="{}"))],
        usage={"input_tokens": 1, "output_tokens": 1},
    )
    client, calls = _client(response)
    provider = DeepSeekProvider(
        api_key="private",
        model="deepseek-v4-flash",
        client=client,
    )

    provider.complete(_request())

    assert calls[0]["extra_body"] == {"thinking": {"type": "disabled"}}
    assert calls[0]["response_format"] == {"type": "json_object"}


def test_empty_compatible_response_fails_closed_but_keeps_usage() -> None:
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=""))],
        usage={"input_tokens": 3, "output_tokens": 0},
    )
    client, _calls = _client(response)
    provider = OpenAIProvider(api_key="private", model="gpt-test", client=client)

    with pytest.raises(ValueError, match="message content"):
        provider.complete(_request())

    assert provider.last_call_metadata["usage"]["total_tokens"] == 3
