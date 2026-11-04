"""Run the agent against evals/cases.jsonl and write a JSON report.

Usage:  ANTHROPIC_API_KEY=... python evals/run_evals.py [--model MODEL]
"""

import argparse
import json
import time
from pathlib import Path

from toolagent import Agent, score_case
from toolagent.tracing import Tracer

ROOT = Path(__file__).parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=None)
    parser.add_argument("--cases", default=str(ROOT / "cases.jsonl"))
    args = parser.parse_args()

    cases = [json.loads(line) for line in Path(args.cases).read_text().splitlines() if line.strip()]
    rows = []
    for case in cases:
        trace_path = ROOT.parent / "traces" / f"{case['id']}.jsonl"
        agent = Agent(model=args.model, tracer=Tracer(trace_path))
        start = time.time()
        result = agent.run(case["prompt"])
        row = score_case(case, result)
        row["latency_s"] = round(time.time() - start, 2)
        rows.append(row)
        print(f"{'PASS' if row['passed'] else 'FAIL'}  {row['id']:<10} "
              f"steps={row['steps']} tools={row['tools_called']} {row['latency_s']}s")

    passed = sum(r["passed"] for r in rows)
    summary = {"pass_rate": passed / len(rows), "passed": passed, "total": len(rows), "cases": rows}
    (ROOT / "report.json").write_text(json.dumps(summary, indent=2))
    print(f"\n{passed}/{len(rows)} passed ({summary['pass_rate']:.0%})")
    raise SystemExit(0 if passed == len(rows) else 1)


if __name__ == "__main__":
    main()
