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

@pytest.mark.skipif(not os.environ.get("TAU2_CHECKOUT"),reason="pinned tau2 runtime required")
def test_native_airline_simulation_executes_tool_and_evaluates_without_api():
    import json
    root=Path(os.environ["TAU2_CHECKOUT"]); preflight(root)
    sys.path.insert(0,str(root/"src"))
    from tau2.run import get_tasks, run_single_task
    from tau2.data_model.simulation import TextRunConfig
    from tau2.domains.airline.environment import get_environment
    env=get_environment()
    user_id=next(iter(env.tools.db.users))
    class Replay:
        last_call_metadata={"usage":{"input_tokens":3,"output_tokens":2}}
        def __init__(self,answers): self.answers=iter(answers)
        def complete(self,request): return json.dumps(next(self.answers))
    routes={
        "agent":Replay([{"content":None,"tool_calls":[{"name":"get_user_details",
            "arguments":{"user_id":user_id}}]},{"content":"Lookup done.","tool_calls":[]}]),
        "user":Replay([{"content":"Please look up my profile.","tool_calls":[]},
                       {"content":"###STOP###","tool_calls":[]}])}
    bridge=SubscriptionBridge(routes,before_call=lambda alias:None,max_calls=4)
    config=TextRunConfig(domain="airline",agent="llm_agent",user="user_simulator",
        llm_agent="agent",llm_user="user",llm_args_agent={"num_retries":0},
        llm_args_user={"num_retries":0},max_concurrency=1,max_retries=0,
        auto_resume=False,auto_review=False,hallucination_retries=0,max_steps=8)
    with install(bridge):
        result=run_single_task(config,get_tasks("airline")[0],seed=42)
    assert len(bridge.receipts)==4
    assert all(r["status"]=="completed" for r in bridge.receipts)
    assert any(m.role=="tool" for m in result.messages)
    assert result.reward_info is not None
    assert result.termination_reason.value=="user_stop"
