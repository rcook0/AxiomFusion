from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple, Any, Optional
import hashlib

Span = Tuple[int,int]

@dataclass(frozen=True)
class NodeMeta:
    node_id: str
    span: Span

class MetaTable:
    def __init__(self):
        self.by_obj: Dict[int, NodeMeta] = {}

    def add(self, obj: Any, span: Span, salt: str = ""):
        nid = stable_id(span, salt)
        self.by_obj[id(obj)] = NodeMeta(nid, span)

def stable_id(span: Span, salt: str = "") -> str:
    h = hashlib.sha1(f"{span[0]}:{span[1]}:{salt}".encode("utf-8")).hexdigest()
    return h[:12]
