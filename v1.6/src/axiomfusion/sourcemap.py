from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import re
import hashlib
from .meta import MetaTable
from .provenance import Provenance

@dataclass
class SourceMap:
    version: str
    source_sha1: str
    nodes: List[Dict[str, Any]]
    provenance: Dict[str, Any]
    emitted_map: Dict[str, Any]

def _sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()

def build_sourcemap(src: str, meta: Optional[MetaTable], prov: Optional[Provenance], emitted: str) -> Dict[str, Any]:
    nodes: List[Dict[str, Any]] = []
    if meta is not None:
        for nm in meta.by_obj.values():
            nodes.append({
                "id": nm.node_id,
                "kind": nm.kind,
                "span": {"start": nm.span[0], "end": nm.span[1]},
                "loc": {"start": {"line": nm.start_line, "col": nm.start_col},
                        "end": {"line": nm.end_line, "col": nm.end_col}},
            })
    # heuristic emitted mapping: first occurrence line for any symbol
    first_line: Dict[str,int] = {}
    for i, line in enumerate(emitted.splitlines(), start=1):
        for m in re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*)\b", line):
            sym = m.group(1)
            first_line.setdefault(sym, i)
    return SourceMap(
        version="1.4.0",
        source_sha1=_sha1(src),
        nodes=sorted(nodes, key=lambda x: (x["kind"], x["id"])),
        provenance=(prov.to_json() if prov else {"edges":[]}),
        emitted_map={"emitted_sha1": _sha1(emitted), "first_symbol_line": first_line},
    ).__dict__
