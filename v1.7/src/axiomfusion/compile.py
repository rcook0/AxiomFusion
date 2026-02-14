from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Set, Tuple, Dict

from .parser import parse, parse_with_meta
from .typecheck import typecheck
from .ir import lower, IRModule

@dataclass
class CompileResult:
    ast_meta: object | None = None
    ir: IRModule
    capabilities: Set[str]

def compile_source(src: str) -> CompileResult:
    ast, meta = parse_with_meta(src)
    _, types = typecheck(ast)
    irm = lower(ast, types)
    return CompileResult(
        ast_meta=meta,
ir=irm, capabilities=set(irm.capabilities))
