# tool-agent-evals

[![CI](https://github.com/<your-github-username>/tool-agent-evals/actions/workflows/ci.yml/badge.svg)](https://github.com/<your-github-username>/tool-agent-evals/actions)

A small tool-using LLM agent in Python, built around the part most demo agents skip: **measuring whether it works**.

## What's inside

- **Agent loop** (`src/toolagent/agent.py`): call the model, run requested tools, return results, repeat, with a step limit.
- **Tools** (`src/toolagent/tools.py`): a safe arithmetic calculator (AST-based, no `eval`) and a forex position-size calculator.
- **Tracing** (`src/toolagent/tracing.py`): every model response and tool call is logged to JSONL.
- **Evals** (`evals/`): a case file, a runner, and a scorer that checks both the final answer and which tools were used.
- **Tests + CI**: the agent loop is tested with a scripted fake client, so CI needs no API key.

## Architecture

```
prompt ──▶ Agent.run ──▶ model ──▶ tool_use? ──yes──▶ run_tool ──▶ tool_result ─┐
                           ▲                                                      │
                           └──────────────────────────────────────────────────────┘
                              no ──▶ final answer ──▶ AgentResult (text, tools, steps)
```

## Quickstart

```bash
pip install -e ".[dev]"
pytest -q                       # offline unit tests
export ANTHROPIC_API_KEY=...    # for live evals
python evals/run_evals.py       # prints PASS/FAIL per case, writes evals/report.json
```

Set `AGENT_MODEL` or pass `--model` to compare models on the same cases.

## Design decisions

- **Tool errors go back to the model.** A failing tool call becomes a `tool_result` with `is_error: true`, so the agent can explain the problem instead of crashing.
- **Evals score behavior, not just text.** A case passes only if the answer matches *and* the right tools were called, which catches "right answer, guessed instead of calculating".
- **No `eval()`.** The calculator walks the AST and allows only arithmetic nodes, with a cap on exponents.
- **Fake client for tests.** The loop's logic (retries, errors, step limit) is verified deterministically.

## Results

Run `python evals/run_evals.py` and paste your pass rate and per-case table here, ideally for more than one model.

## Roadmap

- More tools (web fetch, file search) and harder multi-step eval cases
- Per-case token and cost tracking
- Compare models side by side in a report table
