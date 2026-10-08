import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from agents.tau2_subscription import SubscriptionBridge, quota_gate, install

class Transport:
    def __init__(self, answer):
        self.answer, self.requests = answer, []
        self.last_call_metadata = {"usage": {"input_tokens": 10, "output_tokens": 4}}
    def complete(self, request):
        self.requests.append(request)
        if isinstance(self.answer, Exception): raise self.answer
        return self.answer

TOOL = {"type": "function", "function": {"name": "lookup",
        "parameters": {"type": "object", "properties": {"id": {"type": "string"}}}}}

class SubscriptionTests(unittest.TestCase):
    def bridge(self, answer, max_calls=3):
        transport = Transport(answer)
        return SubscriptionBridge({"sub": transport}, before_call=lambda alias: None,
                                  max_calls=max_calls), transport

    def test_history_tool_result_round_trip(self):
        bridge, transport = self.bridge('{"content":null,"tool_calls":[{"name":"lookup","arguments":{"id":"x"}}]}')
        history = [{"role":"system","content":"Policy A"},{"role":"user","content":"Lookup x"}]
        result = bridge.complete(model="sub", messages=history, tools=[TOOL], seed=4,
                                 temperature=0, num_retries=3)
        call = result["choices"][0]["message"]["tool_calls"][0]
        self.assertEqual(json.loads(call["function"]["arguments"]), {"id":"x"})
        self.assertIn('"Policy A"', transport.requests[0].prompt)
        self.assertIn('"lookup"', transport.requests[0].prompt)
        self.assertEqual(bridge.receipts[0]["unenforced"], {"seed":4,"temperature":0})
        self.assertIsNone(bridge.receipts[0]["cost_usd"])
        history += [result["choices"][0]["message"], {"role":"tool",
                    "tool_call_id":call["id"],"content":"Found x"}]
        transport.answer = '{"content":"Found x","tool_calls":[]}'
        reply = bridge.complete(model="sub", messages=history)
        self.assertEqual(reply["choices"][0]["message"]["content"],"Found x")
        self.assertIn(call["id"], transport.requests[1].prompt)

    def test_unknown_route_and_unsupported_options_make_no_call(self):
        bridge, transport = self.bridge('{"content":"ok","tool_calls":[]}')
        for args in [{"model":"api/model"},{"model":"sub","max_tokens":30}]:
            with self.assertRaises(ValueError): bridge.complete(messages=[],**args)
        self.assertEqual(transport.requests,[])

    def test_invalid_outputs_stop_without_retry(self):
        for answer in ["not JSON",'{"content":null,"tool_calls":[]}',
            '{"content":null,"tool_calls":[{"name":"shell","arguments":{}}]}',
            '{"content":"x","tool_calls":[],"extra":1}']:
            bridge, transport = self.bridge(answer)
            with self.assertRaises(ValueError): bridge.complete(model="sub",messages=[],tools=[TOOL])
            self.assertEqual(len(transport.requests),1)
            self.assertEqual(bridge.receipts[0]["status"],"failed")
            with self.assertRaises(RuntimeError): bridge.complete(model="sub",messages=[])
            self.assertEqual(len(transport.requests),1)

    def test_budget_and_transport_failure_do_not_retry(self):
        bridge, transport = self.bridge('{"content":"ok","tool_calls":[]}',max_calls=1)
        bridge.complete(model="sub",messages=[])
        with self.assertRaises(RuntimeError): bridge.complete(model="sub",messages=[])
        self.assertEqual(len(transport.requests),1)
        bridge, transport = self.bridge(TimeoutError("ambiguous"))
        with self.assertRaises(TimeoutError): bridge.complete(model="sub",messages=[])
        self.assertEqual(len(transport.requests),1)

    def test_tool_choice_is_enforced(self):
        for answer, choice in [('{"content":"ok","tool_calls":[]}',"required"),
            ('{"content":null,"tool_calls":[{"name":"lookup","arguments":{}}]}',"none")]:
            bridge, _ = self.bridge(answer)
            with self.assertRaises(ValueError):
                bridge.complete(model="sub",messages=[],tools=[TOOL],tool_choice=choice)

    def test_quota_blocks_missing_stale_and_reserve_before_transport(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/"quota.json"; gate=quota_gate(file,
                expected_windows={"sub":["five_hour","weekly"]},now=lambda:1000)
            with self.assertRaises(RuntimeError): gate("sub")
            snapshot={"sampled_at":990,"routes":{"sub":{"status":"allowed","extra_usage":False,
                "windows":[{"name":"five_hour","remaining_percent":40,"reset_at":2000},
                           {"name":"weekly","remaining_percent":31,"reset_at":3000}]}}}
            file.write_text(json.dumps(snapshot)); gate("sub")
            weekly_only={"sampled_at":990,"routes":{"sub":{"status":"allowed","extra_usage":False,
                "windows":[{"name":"weekly","remaining_percent":93,"reset_at":3000}]}}}
            file.write_text(json.dumps(weekly_only))
            quota_gate(file,expected_windows={"sub":["weekly"]},now=lambda:1000)("sub")
            file.write_text(json.dumps(snapshot))
            strict=quota_gate(file,expected_windows={"sub":["five_hour","weekly","model_weekly"]},
                              now=lambda:1000)
            with self.assertRaises(RuntimeError): strict("sub")
            snapshot["routes"]["sub"]["windows"][1]["remaining_percent"]=30
            file.write_text(json.dumps(snapshot))
            with self.assertRaises(RuntimeError): gate("sub")
            snapshot["sampled_at"]=900; file.write_text(json.dumps(snapshot))
            with self.assertRaises(RuntimeError): gate("sub")
            bridge, transport=self.bridge('{"content":"ok","tool_calls":[]}')
            bridge.before_call=gate
            with self.assertRaises(RuntimeError): bridge.complete(model="sub",messages=[])
            self.assertEqual(transport.requests,[])

    def test_hook_never_calls_api_and_restores(self):
        bridge,_=self.bridge('{"content":"ok","tool_calls":[]}')
        def forbidden(**kw): raise AssertionError("API called")
        module=SimpleNamespace(completion=forbidden,get_response_cost=lambda r:9)
        with install(bridge,module=module,response_factory=lambda **kw:kw):
            reply=module.completion(model="sub",messages=[])
            self.assertIsNone(module.get_response_cost(reply))
            with self.assertRaises(ValueError): module.completion(model="api/model",messages=[])
        self.assertIs(module.completion,forbidden)
        self.assertEqual(module.get_response_cost({}),9)

if __name__ == "__main__": unittest.main()
