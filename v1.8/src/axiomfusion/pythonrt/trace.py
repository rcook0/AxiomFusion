from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any, Iterable
import json

@dataclass
class TraceEvent:
    t: int
    time: str
    kind: str
    data: Dict[str, Any]

class TraceWriter:
    def __init__(self, path: str):
        self.path = path
        self.f = open(path, "w", encoding="utf-8")

    def write(self, ev: TraceEvent):
        self.f.write(json.dumps({
            "t": ev.t,
            "time": ev.time,
            "kind": ev.kind,
            **ev.data,
        }) + "\n")

    def close(self):
        self.f.close()
