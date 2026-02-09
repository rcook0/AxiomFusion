from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union, Set
from . import ast as A
from .typecheck import T

@dataclass
class IRModule:
    inputs: List["IRInput"]
    bindings: List["IRBinding"]
    states: List["IRState"]
    handlers: List["IRHandler"]
    capabilities: Set[str]

@dataclass
class IRInput:
    name: str
    typ: str
    expr: "IRExpr"

@dataclass
class IRBinding:
    kind: str
    name: str
    expr: "IRExpr"
    typ: Optional[T] = None

@dataclass
class IRStateField:
    name: str
    typ: str
    init: "IRExpr"

@dataclass
class IRState:
    name: str
    version: int
    fields: List[IRStateField]

@dataclass
class IRHandler:
    kind: str  # bar|tick
    stmts: List["IRStmt"]

# expr
@dataclass
class Lit: value: Any
@dataclass
class Var: name: str
@dataclass
class Member: obj: "IRExpr"; field: str
@dataclass
class BinOp: op: str; left: "IRExpr"; right: "IRExpr"
@dataclass
class UnOp: op: str; expr: "IRExpr"
@dataclass
class Call: name: str; args: List[Tuple[Optional[str], "IRExpr"]]
@dataclass
class Index: base: "IRExpr"; k: int
IRExpr = Union[Lit,Var,Member,BinOp,UnOp,Call,Index]

# stmts
@dataclass
class IfStmt: cond: IRExpr; block: List["IRStmt"]
@dataclass
class SetStmt: target: Member; expr: IRExpr
@dataclass
class ReduceStmt: target: Member; expr: IRExpr; op: str
@dataclass
class TradeIntent: kind: str; kwargs: Dict[str, IRExpr]
IRStmt = Union[IfStmt, SetStmt, ReduceStmt, TradeIntent]

def lower(mod: A.Module, expr_types: Dict[int, T]) -> IRModule:
    inputs: List[IRInput] = []
    binds: List[IRBinding] = []
    states: List[IRState] = []
    handlers: List[IRHandler] = []
    caps: Set[str] = set()

    for d in mod.decls:
        if isinstance(d, A.InputDecl):
            inputs.append(IRInput(d.name, d.typ, lower_expr(d.expr)))
        elif isinstance(d, A.LetDecl):
            binds.append(IRBinding("let", d.name, lower_expr(d.expr), expr_types.get(id(d.expr))))
        elif isinstance(d, A.SignalDecl):
            binds.append(IRBinding("signal", d.name, lower_expr(d.expr), expr_types.get(id(d.expr))))
        elif isinstance(d, A.StateDecl):
            fields = [IRStateField(f.name, f.typ, lower_expr(f.expr)) for f in d.fields]
            states.append(IRState(d.name, d.version, fields))
        elif isinstance(d, A.OnBar):
            stmts = [lower_stmt(s) for s in d.stmts]
            if any(contains_trade(s) for s in stmts): caps.add("trade")
            handlers.append(IRHandler("bar", stmts))
        elif isinstance(d, A.OnTick):
            stmts = [lower_stmt(s) for s in d.stmts]
            if any(contains_trade(s) for s in stmts): caps.add("trade")
            handlers.append(IRHandler("tick", stmts))
        else:
            raise ValueError(f"Unknown decl {d}")

    return IRModule(inputs, binds, states, handlers, caps)

def contains_trade(s: IRStmt) -> bool:
    if isinstance(s, TradeIntent): return True
    if isinstance(s, IfStmt):
        return any(contains_trade(x) for x in s.block)
    return False

def lower_stmt(s: A.Stmt) -> IRStmt:
    if isinstance(s, A.IfStmt):
        return IfStmt(lower_expr(s.cond), [lower_stmt(x) for x in s.block])
    if isinstance(s, A.SetStmt):
        tgt = lower_expr(s.target); assert isinstance(tgt, Member)
        return SetStmt(tgt, lower_expr(s.expr))
    if isinstance(s, A.ReduceStmt):
        tgt = lower_expr(s.target); assert isinstance(tgt, Member)
        return ReduceStmt(tgt, lower_expr(s.expr), s.op)
    if isinstance(s, A.CallStmt):
        c = s.call
        if not c.name.startswith("trade."):
            raise ValueError("Only trade.* allowed in handlers")
        kind = c.name.split(".",1)[1]
        kwargs: Dict[str, IRExpr] = {}
        pos = [ex for kw,ex in c.args if kw is None]
        kwd = {kw: ex for kw,ex in c.args if kw is not None}
        if kind in {"enter_long","enter_short"}:
            order = ["qty","sl_points","tp_points","tag"]
            for i,ex in enumerate(pos):
                if i < len(order): kwargs[order[i]] = lower_expr(ex)
            for k,ex in kwd.items(): kwargs[k] = lower_expr(ex)
        elif kind == "exit":
            if pos: kwargs["tag"] = lower_expr(pos[0])
            for k,ex in kwd.items(): kwargs[k] = lower_expr(ex)
        else:
            for k,ex in kwd.items(): kwargs[k] = lower_expr(ex)
        return TradeIntent(kind, kwargs)
    raise ValueError(f"Unknown stmt {s}")

def lower_expr(e: A.Expr) -> IRExpr:
    if isinstance(e, A.Lit): return Lit(e.value)
    if isinstance(e, A.Var): return Var(e.name)
    if isinstance(e, A.Member): return Member(lower_expr(e.obj), e.field)
    if isinstance(e, A.BinOp): return BinOp(e.op, lower_expr(e.left), lower_expr(e.right))
    if isinstance(e, A.UnOp): return UnOp(e.op, lower_expr(e.expr))
    if isinstance(e, A.Call): return Call(e.name, [(kw, lower_expr(ex)) for kw,ex in e.args])
    if isinstance(e, A.Index): return Index(lower_expr(e.base), e.k)
    raise ValueError(f"Unknown expr {e}")
