"""The agent loop: call the model, run any requested tools, feed results back, repeat."""

import os
from dataclasses import dataclass, field

from .tools import TOOL_SCHEMAS, run_tool
from .tracing import Tracer

DEFAULT_MODEL = "claude-sonnet-5-5"
SYSTEM = (
    "You are a precise assistant. Use the provided tools for any arithmetic or "
    "position-sizing calculation instead of computing in your head. If a tool returns "
    "an error, explain the problem to the user plainly. Answer briefly."
)


@dataclass
class AgentResult:
    text: str
    tool_calls: list[str] = field(default_factory=list)
    steps: int = 0
    stopped: str = "end_turn"


def _text(content) -> str:
    return "".join(b.text for b in content if getattr(b, "type", None) == "text").strip()


class Agent:
    def __init__(self, client=None, model: str | None = None, max_steps: int = 8,
                 tracer: Tracer | None = None, system: str = SYSTEM):
        if client is None:
            import anthropic

            client = anthropic.Anthropic()
        self.client = client
        self.model = model or os.environ.get("AGENT_MODEL", DEFAULT_MODEL)
        self.max_steps = max_steps
        self.tracer = tracer or Tracer()
        self.system = system

    def run(self, prompt: str) -> AgentResult:
        messages = [{"role": "user", "content": prompt}]
        called: list[str] = []
        self.tracer.log("run_start", prompt=prompt, model=self.model)

        for step in range(1, self.max_steps + 1):
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=self.system,
                tools=TOOL_SCHEMAS,
                messages=messages,
            )
            self.tracer.log("model_response", step=step, stop_reason=resp.stop_reason)
            messages.append({"role": "assistant", "content": resp.content})

            if resp.stop_reason != "tool_use":
                text = _text(resp.content)
                self.tracer.log("run_end", steps=step, stopped="end_turn")
                return AgentResult(text, called, step, "end_turn")

            results = []
            for block in resp.content:
                if getattr(block, "type", None) != "tool_use":
                    continue
                called.append(block.name)
                try:
                    output, is_error = run_tool(block.name, block.input), False
                except Exception as exc:  # tool failures go back to the model, not the caller
                    output, is_error = f"Error: {exc}", True
                self.tracer.log("tool_call", name=block.name, input=block.input,
                                output=output, is_error=is_error)
                results.append({"type": "tool_result", "tool_use_id": block.id,
                                "content": output, "is_error": is_error})
            messages.append({"role": "user", "content": results})

        self.tracer.log("run_end", steps=self.max_steps, stopped="max_steps")
        return AgentResult("Stopped: step limit reached.", called, self.max_steps, "max_steps")
