from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class RewriteEdge:
    pass_name: str
    src_id: str
    dst_id: str
    note: str = ""

@dataclass
class Provenance:
    edges: List[RewriteEdge] = field(default_factory=list)

    def add(self, pass_name: str, src_id: str, dst_id: str, note: str = ""):
        self.edges.append(RewriteEdge(pass_name, src_id, dst_id, note))

    def to_json(self) -> Dict[str, Any]:
        return {"edges":[{"pass":e.pass_name,"src":e.src_id,"dst":e.dst_id,"note":e.note} for e in self.edges]}
