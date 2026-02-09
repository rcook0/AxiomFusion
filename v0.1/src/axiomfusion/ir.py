from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union, Set
from . import ast as A
from .typecheck import T

# ---- IR nodes ----
@dataclass
class IRModule:
    inputs: List["IRInput"]
    bindings: List["IRBinding"]
    handlers: List["IRHandler"]
    capabilities: Set[str]

@dataclass
class IRInput:
    name: str
    typ: str
    expr: "IRExpr"

@dataclass
class IRBinding:
    kind: str   # 'let'|'signal'
    name: str
    expr: "IRExpr"
    typ: Optional[T] = None

@dataclass
class IRHandler:
    kind: str   # 'bar'
    stmts: List["IRStmt"]

# expressions
@dataclass
class Lit: value: Any
@dataclass
class Var: name: str
@dataclass
class BinOp: op: str; left: "IRExpr"; right: "IRExpr"
@dataclass
class UnOp: op: str; expr: "IRExpr"
@dataclass
class Call: name: str; args: List[Tuple[Optional[str], "IRExpr"]]
@dataclass
class Index: base: "IRExpr"; k: int

IRExpr = Union[Lit,Var,BinOp,UnOp,Call,Index]

# statements (effects only)
@dataclass
class IfStmt: cond: IRExpr; block: List["IRStmt"]
@dataclass
class TradeIntent: kind: str; kwargs: Dict[str, IRExpr]

IRStmt = Union[IfStmt, TradeIntent]

def lower(mod: A.Module, expr_types: Dict[int, T]) -> IRModule:
    inputs: List[IRInput] = []
    binds: List[IRBinding] = []
    handlers: List[IRHandler] = []
    caps: Set[str] = set()

    for d in mod.decls:
        if isinstance(d, A.InputDecl):
            inputs.append(IRInput(d.name, d.typ, lower_expr(d.expr)))
        elif isinstance(d, A.LetDecl):
            binds.append(IRBinding("let", d.name, lower_expr(d.expr), expr_types.get(id(d.expr))))
        elif isinstance(d, A.SignalDecl):
            binds.append(IRBinding("signal", d.name, lower_expr(d.expr), expr_types.get(id(d.expr))))
        elif isinstance(d, A.OnBar):
            stmts = [lower_stmt(s) for s in d.stmts]
            # detect capabilities
            if any(isinstance(s, TradeIntent) or contains_trade(s) for s in stmts):
                caps.add("trade")
            handlers.append(IRHandler("bar", stmts))
        else:
            raise ValueError(f"Unknown decl {d}")
    return IRModule(inputs, binds, handlers, caps)

def contains_trade(s: IRStmt) -> bool:
    if isinstance(s, TradeIntent): return True
    if isinstance(s, IfStmt):
        return any(contains_trade(x) for x in s.block)
    return False

def lower_stmt(s: A.Stmt) -> IRStmt:
    if isinstance(s, A.IfStmt):
        return IfStmt(lower_expr(s.cond), [lower_stmt(x) for x in s.block])
    if isinstance(s, A.CallStmt):
        c = s.call
        assert isinstance(c, A.Call)
        if not c.name.startswith("trade."):
            raise ValueError("Only trade.* allowed in statements")
        kind = c.name.split(".",1)[1]
        kwargs = {}
        # accept positional by mapping common signatures in order
        pos = [ex for kw,ex in c.args if kw is None]
        kwd = {kw: ex for kw,ex in c.args if kw is not None}
        if kind in {"enter_long","enter_short"}:
            order = ["qty","sl_points","tp_points","tag"]
            for i,ex in enumerate(pos):
                if i < len(order):
                    kwargs[order[i]] = lower_expr(ex)
            for k,ex in kwd.items():
                kwargs[k] = lower_expr(ex)
        elif kind in {"exit"}:
            if pos: kwargs["tag"] = lower_expr(pos[0])
            for k,ex in kwd.items(): kwargs[k] = lower_expr(ex)
        elif kind in {"set_be","trail"}:
            order = ["tag","be_points" if kind=="set_be" else "trail_points"]
            for i,ex in enumerate(pos):
                if i < len(order):
                    kwargs[order[i]] = lower_expr(ex)
            for k,ex in kwd.items(): kwargs[k] = lower_expr(ex)
        else:
            # unknown intent still preserved
            for k,ex in kwd.items(): kwargs[k] = lower_expr(ex)
        return TradeIntent(kind, kwargs)
    raise ValueError(f"Unknown stmt {s}")

def lower_expr(e: A.Expr) -> IRExpr:
    if isinstance(e, A.Lit): return Lit(e.value)
    if isinstance(e, A.Var): return Var(e.name)
    if isinstance(e, A.BinOp): return BinOp(e.op, lower_expr(e.left), lower_expr(e.right))
    if isinstance(e, A.UnOp): return UnOp(e.op, lower_expr(e.expr))
    if isinstance(e, A.Call): return Call(e.name, [(kw, lower_expr(ex)) for kw,ex in e.args])
    if isinstance(e, A.Index): return Index(lower_expr(e.base), e.k)
    raise ValueError(f"Unknown expr {e}")
