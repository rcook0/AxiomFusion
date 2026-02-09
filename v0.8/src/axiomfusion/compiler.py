from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Set, Dict, Any

from .parser import parse
from .typecheck import typecheck
from .ir import lower, IRModule
from .optimizer import optimize
from .targets import Target, get_target
from .sandbox import CapabilityGate

from .emitters import pine as pine_emitter
from .emitters import mql5 as mql5_emitter
from .emitters import python_rt as py_emitter

@dataclass
class CompileReport:
    target: str
    opt: str
    required_caps: Set[str]
    allowed_caps: Set[str]
    emitted: str

def compile_to_target(src: str, target_name: str, *, opt: str = "O2", allow_caps: Optional[Set[str]] = None, strict: bool = True) -> CompileReport:
    t = get_target(target_name)
    ast = parse(src)
    _, types = typecheck(ast)
    irm = lower(ast, types)
    required = set(irm.capabilities)
    allowed = allow_caps if allow_caps is not None else set(t.allow_caps)
    gate = CapabilityGate(allowed=allowed, strict=strict)
    gate.check(required)
    irm2 = optimize(irm, opt)
    emitted = emit_for_target(irm2, t)
    return CompileReport(target=target_name, opt=opt, required_caps=required, allowed_caps=allowed, emitted=emitted)

def emit_for_target(irm: IRModule, t: Target) -> str:
    if t.emitter == "pine":
        # pass mode via capabilities/options by tagging trade capability
        if t.options.get("force_indicator"):
            irm = replace_caps(irm, discard={"trade"})
        if t.options.get("force_strategy"):
            irm = replace_caps(irm, add={"trade"})
        return pine_emitter.emit(irm)
    if t.emitter == "mql5":
        return mql5_emitter.emit(irm)
    if t.emitter == "python_rt":
        return py_emitter.emit(irm)
    raise ValueError(f"Unknown emitter {t.emitter}")

def replace_caps(irm: IRModule, add=set(), discard=set()) -> IRModule:
    # shallow replace
    from dataclasses import replace as _r
    caps = set(irm.capabilities)
    caps |= set(add)
    caps -= set(discard)
    return _r(irm, capabilities=caps)
