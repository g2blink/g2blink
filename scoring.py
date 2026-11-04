"""Scoring for eval cases. Kept separate from the runner so it can be unit tested."""

import re


def score_case(case: dict, result) -> dict:
    """A case passes when the answer matches the regex AND the set of tools used matches."""
    answer_ok = bool(re.search(case["expect_regex"], result.text, re.IGNORECASE))
    tools_ok = set(result.tool_calls) == set(case.get("expect_tools", []))
    return {
        "id": case["id"],
        "passed": answer_ok and tools_ok,
        "answer_ok": answer_ok,
        "tools_ok": tools_ok,
        "tools_called": result.tool_calls,
        "steps": result.steps,
    }
