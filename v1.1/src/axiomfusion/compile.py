from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Set, Tuple, Dict

from .parser import parse
from .typecheck import typecheck
from .ir import lower, IRModule

@dataclass
class CompileResult:
    ir: IRModule
    capabilities: Set[str]

def compile_source(src: str) -> CompileResult:
    ast = parse(src)
    _, types = typecheck(ast)
    irm = lower(ast, types)
    return CompileResult(ir=irm, capabilities=set(irm.capabilities))
