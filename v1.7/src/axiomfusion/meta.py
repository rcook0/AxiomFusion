from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple, Any, Optional
import hashlib
from .linemap import LineMap

Span = Tuple[int,int]

@dataclass(frozen=True)
class NodeMeta:
    node_id: str
    span: Span
    start_line: int
    start_col: int
    end_line: int
    end_col: int
    kind: str

def stable_id(kind: str, span: Span, snippet: str = "", salt: str = "") -> str:
    h = hashlib.sha1(f"{kind}:{span[0]}:{span[1]}:{salt}:{snippet}".encode("utf-8")).hexdigest()
    return h[:12]

class MetaTable:
    def __init__(self, src: str):
        self.src = src
        self.lm = LineMap(src)
        self.by_obj: Dict[int, NodeMeta] = {}

    def add(self, obj: Any, span: Span, kind: str, salt: str = ""):
        snippet = self.src[span[0]:min(span[1], span[0]+80)]
        nid = stable_id(kind, span, snippet=snippet, salt=salt)
        a, b = self.lm.span_to_linecols(span[0], span[1])
        self.by_obj[id(obj)] = NodeMeta(
            node_id=nid,
            span=span,
            start_line=a.line, start_col=a.col,
            end_line=b.line, end_col=b.col,
            kind=kind,
        )

    def get(self, obj: Any) -> Optional[NodeMeta]:
        return self.by_obj.get(id(obj))
