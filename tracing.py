"""Minimal JSONL tracer: one event per line, easy to grep or load into pandas."""

import json
import time
from pathlib import Path


class Tracer:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None
        self.events: list[dict] = []
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: str, **fields) -> None:
        record = {"t": round(time.time(), 3), "event": event, **fields}
        self.events.append(record)
        if self.path:
            with self.path.open("a") as f:
                f.write(json.dumps(record, default=str) + "\n")
