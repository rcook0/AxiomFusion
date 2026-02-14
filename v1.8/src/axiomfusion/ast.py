from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Any, Union, Tuple

# ---- Decls ----
@dataclass
class InputDecl:
    name: str
    typ: str
    expr: "Expr"

@dataclass
class LetDecl:
    name: str
    expr: "Expr"

@dataclass
class SignalDecl:
    name: str
    expr: "Expr"

@dataclass
class StateField:
    name: str
    typ: str
    expr: "Expr"

@dataclass
class StateDecl:
    name: str
    version: int
    fields: List[StateField]

@dataclass
class OnBar:
    stmts: List["Stmt"]

@dataclass
class OnTick:
    stmts: List["Stmt"]

Decl = Union[InputDecl, LetDecl, SignalDecl, StateDecl, OnBar, OnTick]

# ---- Stmts ----
@dataclass
class IfStmt:
    cond: "Expr"
    block: List["Stmt"]

@dataclass
class CallStmt:
    call: "Call"

@dataclass
class SetStmt:
    target: "Member"
    expr: "Expr"

@dataclass
class ReduceStmt:
    target: "Member"
    expr: "Expr"
    op: str  # sum|min|max|last

Stmt = Union[IfStmt, CallStmt, SetStmt, ReduceStmt]

# ---- Expr ----
@dataclass
class Lit:
    value: Any

@dataclass
class Var:
    name: str

@dataclass
class Member:
    obj: "Expr"
    field: str

@dataclass
class BinOp:
    op: str
    left: "Expr"
    right: "Expr"

@dataclass
class UnOp:
    op: str
    expr: "Expr"

@dataclass
class Call:
    name: str
    args: List[Tuple[Optional[str], "Expr"]]

@dataclass
class Index:
    base: "Expr"
    k: int

Expr = Union[Lit, Var, Member, BinOp, UnOp, Call, Index]

@dataclass
class Module:
    decls: List[Decl]
