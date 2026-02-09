from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union, Tuple

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
class OnBar:
    stmts: List["Stmt"]

Decl = Union[InputDecl, LetDecl, SignalDecl, OnBar]

# ---- Stmts ----
@dataclass
class IfStmt:
    cond: "Expr"
    block: List["Stmt"]

@dataclass
class CallStmt:
    call: "Call"

Stmt = Union[IfStmt, CallStmt]

# ---- Expr ----
@dataclass
class Lit:
    value: Any

@dataclass
class Var:
    name: str

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
    args: List[Tuple[Optional[str], "Expr"]]  # (kw, expr)

@dataclass
class Index:
    base: "Expr"
    k: int  # positive meaning bars ago (parsed from [-k])

Expr = Union[Lit, Var, BinOp, UnOp, Call, Index]

@dataclass
class Module:
    decls: List[Decl]
