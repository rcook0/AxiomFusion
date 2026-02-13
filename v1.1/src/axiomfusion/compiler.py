from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Set, Dict, Any

from .parser import parse
from .typecheck import typecheck
from .ir import lower, IRModule
from .optimizer import optimize
from .targets import Target, get_target
from .contracts.registry import get_contract
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
    try:
        c = get_contract(target_name)
        default_allow = set(c.allow_caps)
    except Exception:
        default_allow = set(t.allow_caps)
    allowed = allow_caps if allow_caps is not None else default_allow
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


def emit_compile_artifacts(src: str, target: str, *, opt: str="O2", out_prefix: str="out", allow_caps=None, strict: bool=True):
    """Compile and return emitted code plus artifact blobs: report.json, deps.dot, map.json (prototype)."""
    rep = compile_to_target(src, target, opt=opt, allow_caps=allow_caps, strict=strict)
    # deps: bindings DAG as DOT
    deps = bindings_deps_dot(src)
    # map: prototype maps binding names to fake node ids; full IR map is future
    smap = {"note":"prototype", "required_caps": sorted(rep.required_caps), "target": rep.target, "opt": rep.opt}
    report = {
        "target": rep.target,
        "opt": rep.opt,
        "required_caps": sorted(rep.required_caps),
        "allowed_caps": sorted(rep.allowed_caps),
        "notes": ["v0.9 report prototype"],
    }
    return rep.emitted, report, deps, smap

def bindings_deps_dot(src: str) -> str:
    # Parse core and build a simple dependency graph over let/signal names.
    from .parser import parse
    import re
    ast = parse(src)
    lets = {}
    sigs = {}
    for d in ast.decls:
        if hasattr(d, "name") and d.__class__.__name__ in {"LetDecl","SignalDecl"}:
            lets[d.name] = d.expr
    # naive: scan variable tokens in repr of expr
    def vars_in_expr(e):
        s = repr(e)
        return set(re.findall(r"Var\(name='([A-Za-z_][A-Za-z0-9_]*)'\)", s))
    edges = []
    for name, expr in lets.items():
        for v in vars_in_expr(expr):
            if v in lets:
                edges.append((v, name))
    # signals
    for d in ast.decls:
        if d.__class__.__name__ == "SignalDecl":
            for v in vars_in_expr(d.expr):
                if v in lets:
                    edges.append((v, d.name))
    lines = ["digraph deps {", "rankdir=LR;"]
    for a,b in edges:
        lines.append(f"\"{a}\" -> \"{b}\";")
    lines.append("}")
    return "\n".join(lines)
