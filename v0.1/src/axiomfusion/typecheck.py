from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple, Optional, List, Union
from . import ast as A

class TypeError_(Exception): ...

@dataclass(frozen=True)
class T:
    kind: str  # 'scalar' or 'series'
    base: str  # 'bool'|'int'|'float'|'string'

def Scalar(base: str) -> T: return T("scalar", base)
def Series(base: str) -> T: return T("series", base)

def is_num(t: T) -> bool:
    return t.base in {"int","float"} and t.kind in {"scalar","series"}

def promote_num(a: T, b: T) -> str:
    # base promotion int->float if any float
    if "float" in (a.base, b.base):
        return "float"
    return "int"

BUILTIN_SERIES = {"open","high","low","close","volume"}

# Builtin function signatures (very small)
# return type computed dynamically for some
def builtin_sig(name: str, arg_types: List[T]) -> T:
    n = name
    if n in {"sma","ema"}:
        # (series<float>, int|float) -> series<float>
        if len(arg_types) != 2: raise TypeError_(f"{n} expects 2 args")
        if arg_types[0].kind != "series" or arg_types[0].base not in {"int","float"}:
            raise TypeError_(f"{n}: first arg must be series<num>")
        if arg_types[1].kind != "scalar" or arg_types[1].base not in {"int","float"}:
            raise TypeError_(f"{n}: second arg must be scalar<num>")
        return Series("float")
    if n == "rsi":
        if len(arg_types) != 2: raise TypeError_("rsi expects 2 args")
        if arg_types[0].kind != "series": raise TypeError_("rsi: first arg must be series")
        return Series("float")
    if n == "atr":
        if len(arg_types) != 1: raise TypeError_("atr expects 1 arg")
        if arg_types[0].kind != "scalar" or arg_types[0].base not in {"int","float"}:
            raise TypeError_("atr: arg must be scalar<num>")
        return Series("float")
    if n == "vwap":
        if len(arg_types) != 0: raise TypeError_("vwap expects 0 args")
        return Series("float")
    if n in {"cross_over","cross_under"}:
        if len(arg_types) != 2: raise TypeError_(f"{n} expects 2 args")
        if arg_types[0].kind != "series" or arg_types[1].kind != "series":
            raise TypeError_(f"{n}: both args must be series")
        return Series("bool")
    if n in {"abs"}:
        if len(arg_types) != 1: raise TypeError_(f"{n} expects 1 arg")
        t = arg_types[0]
        if not is_num(t): raise TypeError_("abs: expects num")
        return t if t.base == "float" else T(t.kind, "int")
    if n in {"min","max"}:
        if len(arg_types) != 2: raise TypeError_(f"{n} expects 2 args")
        a,b = arg_types
        if a.kind != b.kind: raise TypeError_(f"{n}: kinds must match")
        if not is_num(a) or not is_num(b): raise TypeError_(f"{n}: expects num")
        base = promote_num(a,b)
        return T(a.kind, base)
    if n == "nz":
        if len(arg_types) != 2: raise TypeError_("nz expects 2 args")
        a,b = arg_types
        if a.kind != b.kind: raise TypeError_("nz: kinds must match")
        if a.base != b.base: raise TypeError_("nz: base must match")
        return a
    if n == "risk_qty":
        if len(arg_types) != 2: raise TypeError_("risk_qty expects 2 args")
        a,b = arg_types
        if a.kind != "scalar" or a.base not in {"int","float"}: raise TypeError_("risk_qty: risk must be scalar<num>")
        if b.kind != "scalar" or b.base not in {"int","float"}: raise TypeError_("risk_qty: sl must be scalar<num>")
        return Scalar("float")
    # trade.* are checked in statement validation, not here
    raise TypeError_(f"Unknown function '{name}'")

def typecheck(mod: A.Module) -> Tuple[A.Module, Dict[int, T]]:
    env: Dict[str, T] = {}
    expr_types: Dict[int, T] = {}

    # predeclare built-in series
    for s in BUILTIN_SERIES:
        env[s] = Series("float")

    # inputs and lets/signals must come before on bar in v0.1 (not enforced hard, but recommended)
    for d in mod.decls:
        if isinstance(d, A.InputDecl):
            t = parse_type_str(d.typ)
            et = tc_expr(d.expr, env, expr_types)
            if not can_assign(t, et):
                raise TypeError_(f"input {d.name}: cannot assign {et} to {t}")
            env[d.name] = t
        elif isinstance(d, A.LetDecl):
            et = tc_expr(d.expr, env, expr_types)
            env[d.name] = et
        elif isinstance(d, A.SignalDecl):
            et = tc_expr(d.expr, env, expr_types)
            # force boolean kind with lifting allowed
            if et.base != "bool":
                raise TypeError_(f"signal {d.name} must be bool/series<bool>, got {et}")
            env[d.name] = et
        elif isinstance(d, A.OnBar):
            # validate stmts (effects only trade.* calls)
            for s in d.stmts:
                tc_stmt(s, env, expr_types)
        else:
            raise TypeError_(f"Unknown decl {d}")
    return mod, expr_types

def parse_type_str(s: str) -> T:
    s = s.strip()
    if s in {"bool","int","float","string"}:
        return Scalar(s)
    if s.startswith("series<") and s.endswith(">"):
        inner = s[len("series<"):-1].strip()
        if inner not in {"bool","int","float","string"}:
            raise TypeError_(f"Bad series inner type: {inner}")
        return Series(inner)
    raise TypeError_(f"Bad type: {s}")

def can_assign(dst: T, src: T) -> bool:
    if dst.kind != src.kind:
        return False
    if dst.base == src.base:
        return True
    # allow int->float
    if dst.base == "float" and src.base == "int":
        return True
    return False

def lift_kind(a: T, b: T) -> str:
    return "series" if (a.kind == "series" or b.kind == "series") else "scalar"

def tc_expr(e: A.Expr, env: Dict[str,T], out: Dict[int,T]) -> T:
    t: T
    if isinstance(e, A.Lit):
        if isinstance(e.value, bool): t = Scalar("bool")
        elif isinstance(e.value, int): t = Scalar("int")
        elif isinstance(e.value, float): t = Scalar("float")
        elif isinstance(e.value, str): t = Scalar("string")
        else: raise TypeError_(f"Unsupported literal {e.value!r}")
    elif isinstance(e, A.Var):
        if e.name not in env:
            raise TypeError_(f"Unknown identifier '{e.name}'")
        t = env[e.name]
    elif isinstance(e, A.UnOp):
        a = tc_expr(e.expr, env, out)
        if e.op == "not":
            if a.base != "bool": raise TypeError_("not expects bool")
            t = a
        elif e.op == "-":
            if not is_num(a): raise TypeError_("- expects num")
            t = a if a.base == "float" else T(a.kind, "int")
        else:
            raise TypeError_(f"Unknown unary op {e.op}")
    elif isinstance(e, A.BinOp):
        a = tc_expr(e.left, env, out)
        b = tc_expr(e.right, env, out)
        op = e.op
        if op in {"+","-","*","/"}:
            if not is_num(a) or not is_num(b): raise TypeError_(f"{op} expects nums")
            kind = lift_kind(a,b)
            base = promote_num(a,b)
            t = T(kind, base if op != "/" else "float")
        elif op in {"<","<=",">",">=","==","!="}:
            # comparisons allowed on numeric or string for == !=
            kind = lift_kind(a,b)
            if op in {"==","!="}:
                # allow matching base or numeric promotion
                if a.base == b.base:
                    t = T(kind, "bool")
                elif is_num(a) and is_num(b):
                    t = T(kind, "bool")
                else:
                    raise TypeError_(f"{op} incompatible {a} vs {b}")
            else:
                if not is_num(a) or not is_num(b): raise TypeError_(f"{op} expects nums")
                t = T(kind, "bool")
        elif op in {"and","or"}:
            if a.base != "bool" or b.base != "bool": raise TypeError_(f"{op} expects bools")
            kind = lift_kind(a,b)
            t = T(kind, "bool")
        else:
            raise TypeError_(f"Unknown binop {op}")
    elif isinstance(e, A.Call):
        # trade.* not allowed in expressions
        if e.name.startswith("trade."):
            raise TypeError_("trade.* calls are statements only (effects)")
        arg_ts = [tc_expr(x, env, out) for _,x in e.args]
        t = builtin_sig(e.name, arg_ts)
    elif isinstance(e, A.Index):
        bt = tc_expr(e.base, env, out)
        if bt.kind != "series": raise TypeError_("Indexing requires series")
        # returns scalar base
        t = Scalar(bt.base)
    else:
        raise TypeError_(f"Unknown expr {e}")
    out[id(e)] = t
    return t

def tc_stmt(s: A.Stmt, env: Dict[str,T], out: Dict[int,T]) -> None:
    if isinstance(s, A.IfStmt):
        ct = tc_expr(s.cond, env, out)
        if ct.base != "bool": raise TypeError_("if condition must be bool/series<bool>")
        # allow series<bool> in v0.1; emitters will interpret as current bar boolean
        for st in s.block:
            tc_stmt(st, env, out)
        return
    if isinstance(s, A.CallStmt):
        c = s.call
        if not isinstance(c, A.Call):
            raise TypeError_("call stmt must be Call")
        if not c.name.startswith("trade."):
            raise TypeError_("Only trade.* calls are allowed as statements in on bar")
        # Validate minimal required args presence; types numeric/string
        # We allow both positional and keyword for simplicity.
        # Detailed validation in lowering.
        return
    raise TypeError_(f"Unknown stmt {s}")
