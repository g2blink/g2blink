"""Agent loop tests using a scripted fake client, so no API key or network is needed."""

from types import SimpleNamespace as NS

from toolagent import Agent, AgentResult, score_case


class FakeClient:
    def __init__(self, responses):
        self._responses = iter(responses)
        self.messages = self
        self.calls = []

    def create(self, **kwargs):
        # snapshot messages: the agent keeps appending to the same list
        self.calls.append({**kwargs, "messages": list(kwargs["messages"])})
        return next(self._responses)


def text(t):
    return NS(type="text", text=t)


def tool_use(name, args, id="tu_1"):
    return NS(type="tool_use", name=name, input=args, id=id)


def resp(stop, *blocks):
    return NS(stop_reason=stop, content=list(blocks))


def test_tool_roundtrip():
    client = FakeClient([
        resp("tool_use", tool_use("calculator", {"expression": "2+2"})),
        resp("end_turn", text("The answer is 4.")),
    ])
    result = Agent(client=client).run("What is 2+2?")
    assert result.text == "The answer is 4."
    assert result.tool_calls == ["calculator"]
    assert result.steps == 2
    tool_result = client.calls[1]["messages"][-1]["content"][0]
    assert tool_result["content"] == "4" and tool_result["is_error"] is False


def test_tool_error_is_returned_to_model():
    client = FakeClient([
        resp("tool_use", tool_use("calculator", {"expression": "1/0"})),
        resp("end_turn", text("Division by zero is undefined.")),
    ])
    result = Agent(client=client).run("1/0?")
    tool_result = client.calls[1]["messages"][-1]["content"][0]
    assert tool_result["is_error"] is True
    assert "undefined" in result.text


def test_step_limit():
    looping = [resp("tool_use", tool_use("calculator", {"expression": "1+1"})) for _ in range(5)]
    result = Agent(client=FakeClient(looping), max_steps=3).run("loop")
    assert result.stopped == "max_steps"
    assert result.steps == 3


def test_score_case():
    case = {"id": "x", "expect_regex": "434", "expect_tools": ["calculator"]}
    good = AgentResult("It is 434.", ["calculator"], 2)
    bad_tools = AgentResult("It is 434.", [], 1)
    assert score_case(case, good)["passed"] is True
    assert score_case(case, bad_tools)["passed"] is False
