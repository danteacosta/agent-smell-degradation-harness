"""Optional integration with the actual pinned tau2/LiteLLM, no model calls."""
import os
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest
from agents.tau2_subscription import SubscriptionBridge, install
from scripts.tau2_subscription import preflight

@pytest.mark.skipif(not os.environ.get("TAU2_CHECKOUT"),reason="pinned tau2 runtime required")
def test_native_tau2_generate_content_tools_usage_and_cost():
    root=Path(os.environ["TAU2_CHECKOUT"]); preflight(root)
    sys.path.insert(0,str(root/"src"))
    from tau2.utils.llm_utils import generate
    from tau2.data_model.message import UserMessage, ToolMessage
    class Replay:
        last_call_metadata={"usage":{"input_tokens":3,"output_tokens":2}}
        def complete(self, request):
            return '{"content":null,"tool_calls":[{"name":"lookup","arguments":{"id":"x"}}]}'
    bridge=SubscriptionBridge({"sub":Replay()},before_call=lambda alias:None,max_calls=1)
    schema={"type":"function","function":{"name":"lookup","parameters":{"type":"object"}}}
    with install(bridge):
        reply=generate(model="sub",messages=[UserMessage(role="user",content="Lookup x")],
                       tools=[SimpleNamespace(openai_schema=schema)],num_retries=0)
    assert reply.tool_calls[0].name=="lookup"
    assert reply.tool_calls[0].arguments=={"id":"x"}
    assert reply.cost is None
    assert reply.usage=={"completion_tokens":2,"prompt_tokens":3}
    assert ToolMessage(role="tool",id=reply.tool_calls[0].id,content="found").content=="found"
