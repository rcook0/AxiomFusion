from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple, List, Set
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
    return "float" if "float" in (a.base, b.base) else "int"

BUILTIN_SERIES = {"open","high","low","close","volume"}
TICK_BUILTINS = {"bid","ask","last","tick_volume"}

def builtin_sig(name: str, arg_types: List[T]) -> T:
    n = name
    if n in {"sma","ema"}:
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
    if n == "abs":
        if len(arg_types) != 1: raise TypeError_(f"{n} expects 1 arg")
        t = arg_types[0]
        if not is_num(t): raise TypeError_("abs: expects num")
        return t if t.base == "float" else T(t.kind, "int")
    if n in {"min","max"}:
        if len(arg_types) != 2: raise TypeError_(f"{n} expects 2 args")
        a,b = arg_types
        if a.kind != b.kind: raise TypeError_(f"{n}: kinds must match")
        if not is_num(a) or not is_num(b): raise TypeError_(f"{n}: expects num")
        return T(a.kind, promote_num(a,b))
    if n == "nz":
        if len(arg_types) != 2: raise TypeError_("nz expects 2 args")
        a,b = arg_types
        if a.kind != b.kind: raise TypeError_("nz: kinds must match")
        if a.base != b.base and not (is_num(a) and is_num(b)):
            raise TypeError_("nz: base must match (or both numeric)")
        base = promote_num(a,b) if (is_num(a) and is_num(b)) else a.base
        return T(a.kind, base)
    if n == "series_from":
    if len(arg_types) != 3: raise TypeError_("series_from expects 3 args")
    a,b,c = arg_types
    if a.kind != "scalar" or a.base != "string": raise TypeError_("series_from: symbol must be string")
    if b.kind != "scalar" or b.base != "string": raise TypeError_("series_from: tf must be string")
    if c.kind != "scalar" or c.base != "string": raise TypeError_("series_from: field must be string")
    return Series("float")

    if n == "risk_qty":
        if len(arg_types) != 2: raise TypeError_("risk_qty expects 2 args")
        a,b = arg_types
        if a.kind != "scalar" or a.base not in {"int","float"}: raise TypeError_("risk_qty: risk must be scalar<num>")
        if b.kind != "scalar" or b.base not in {"int","float"}: raise TypeError_("risk_qty: sl must be scalar<num>")
        return Scalar("float")
    if n in {"hl2","ohlc4"}:
    if len(arg_types) != 0: raise TypeError_(f"{n} expects 0 args")
    return Series("float")
if n in {"wma","highest","lowest","stddev"}:
    if len(arg_types) != 2: raise TypeError_(f"{n} expects 2 args")
    if arg_types[0].kind != "series" or arg_types[0].base not in {"int","float"}:
        raise TypeError_(f"{n}: first arg must be series<num>")
    if arg_types[1].kind != "scalar" or arg_types[1].base not in {"int","float"}:
        raise TypeError_(f"{n}: len must be scalar<num>")
    return Series("float")
if n in {"bb_middle"}:
    if len(arg_types) != 2: raise TypeError_("bb_middle expects 2 args")
    if arg_types[0].kind != "series": raise TypeError_("bb_middle: src must be series")
    return Series("float")
if n in {"bb_upper","bb_lower"}:
    if len(arg_types) != 3: raise TypeError_(f"{n} expects 3 args")
    if arg_types[0].kind != "series" or arg_types[0].base not in {"int","float"}:
        raise TypeError_(f"{n}: src must be series<num>")
    if arg_types[1].kind != "scalar" or arg_types[1].base not in {"int","float"}:
        raise TypeError_(f"{n}: len must be scalar<num>")
    if arg_types[2].kind != "scalar" or arg_types[2].base not in {"int","float"}:
        raise TypeError_(f"{n}: mult must be scalar<num>")
    return Series("float")
if n == "roc":
    if len(arg_types) != 2: raise TypeError_("roc expects 2 args")
    if arg_types[0].kind != "series" or arg_types[0].base not in {"int","float"}:
        raise TypeError_("roc: src must be series<num>")
    if arg_types[1].kind != "scalar" or arg_types[1].base not in {"int","float"}:
        raise TypeError_("roc: len must be scalar<num>")
    return Series("float")
if n == "macd_line":
    if len(arg_types) != 3: raise TypeError_("macd_line expects 3 args")
    if arg_types[0].kind != "series": raise TypeError_("macd_line: src must be series")
    return Series("float")
if n == "macd_signal":
    if len(arg_types) != 4: raise TypeError_("macd_signal expects 4 args")
    if arg_types[0].kind != "series": raise TypeError_("macd_signal: src must be series")
    return Series("float")
if n == "macd_hist":
    if len(arg_types) != 4: raise TypeError_("macd_hist expects 4 args")
    if arg_types[0].kind != "series": raise TypeError_("macd_hist: src must be series")
    return Series("float")

raise TypeError_(f"Unknown function '{name}'")

def typecheck(mod: A.Module) -> Tuple[A.Module, Dict[int, T]]:
    env: Dict[str, T] = {}
    states: Dict[str, Dict[str, T]] = {}
    expr_types: Dict[int, T] = {}

    for s in BUILTIN_SERIES:
        env[s] = Series("float")

    # collect states
    for d in mod.decls:
        if isinstance(d, A.StateDecl):
            if d.name in states:
                raise TypeError_(f"Duplicate state {d.name}")
            fmap: Dict[str,T] = {}
            for f in d.fields:
                if f.typ not in {"bool","int","float","string"}:
                    raise TypeError_(f"State field must be scalar, got {f.typ}")
                fmap[f.name] = Scalar(f.typ)
            states[d.name] = fmap
            env[d.name] = Scalar("string")  # placeholder; member access resolves via states

    for d in mod.decls:
        if isinstance(d, A.InputDecl):
            t = parse_type_str(d.typ)
            et = tc_expr(d.expr, env, states, expr_types, in_tick=False)
            if not can_assign(t, et):
                raise TypeError_(f"input {d.name}: cannot assign {et} to {t}")
            env[d.name] = t
        elif isinstance(d, A.LetDecl):
            et = tc_expr(d.expr, env, states, expr_types, in_tick=False)
            env[d.name] = et
        elif isinstance(d, A.SignalDecl):
            et = tc_expr(d.expr, env, states, expr_types, in_tick=False)
            if et.base != "bool":
                raise TypeError_(f"signal {d.name} must be bool/series<bool>, got {et}")
            env[d.name] = et
        elif isinstance(d, A.StateDecl):
            for f in d.fields:
                et = tc_expr(f.expr, env, states, expr_types, in_tick=False)
                ft = states[d.name][f.name]
                if not can_assign(ft, et):
                    raise TypeError_(f"state {d.name}.{f.name}: cannot assign {et} to {ft}")
        elif isinstance(d, A.OnBar):
            for s in d.stmts:
                tc_stmt(s, env, states, expr_types, in_tick=False)
        elif isinstance(d, A.OnTick):
            for s in d.stmts:
                tc_stmt(s, env, states, expr_types, in_tick=True)
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
    if dst.base == "float" and src.base == "int":
        return True
    return False

def lift_kind(a: T, b: T) -> str:
    return "series" if (a.kind == "series" or b.kind == "series") else "scalar"

def tc_expr(e: A.Expr, env: Dict[str,T], states: Dict[str,Dict[str,T]], out: Dict[int,T], in_tick: bool) -> T:
    if isinstance(e, A.Lit):
        if isinstance(e.value, bool): t = Scalar("bool")
        elif isinstance(e.value, int): t = Scalar("int")
        elif isinstance(e.value, float): t = Scalar("float")
        elif isinstance(e.value, str): t = Scalar("string")
        else: raise TypeError_(f"Unsupported literal {e.value!r}")
    elif isinstance(e, A.Var):
        if e.name in TICK_BUILTINS:
            if not in_tick:
                raise TypeError_(f"'{e.name}' only available inside on tick")
            t = Scalar("float")
        else:
            if e.name not in env:
                raise TypeError_(f"Unknown identifier '{e.name}'")
            t = env[e.name]
    elif isinstance(e, A.Member):
        if isinstance(e.obj, A.Var) and e.obj.name in states:
            st = states[e.obj.name]
            if e.field not in st:
                raise TypeError_(f"Unknown state field {e.obj.name}.{e.field}")
            t = st[e.field]
        else:
            raise TypeError_("Member access only supported on state objects in v0.3")
    elif isinstance(e, A.UnOp):
        a = tc_expr(e.expr, env, states, out, in_tick)
        if e.op == "not":
            if a.base != "bool": raise TypeError_("not expects bool")
            t = a
        elif e.op == "-":
            if not is_num(a): raise TypeError_("- expects num")
            t = a if a.base == "float" else T(a.kind, "int")
        else:
            raise TypeError_(f"Unknown unary op {e.op}")
    elif isinstance(e, A.BinOp):
        a = tc_expr(e.left, env, states, out, in_tick)
        b = tc_expr(e.right, env, states, out, in_tick)
        op = e.op
        if op in {"+","-","*","/"}:
            if not is_num(a) or not is_num(b): raise TypeError_(f"{op} expects nums")
            kind = lift_kind(a,b)
            base = promote_num(a,b)
            t = T(kind, base if op != "/" else "float")
        elif op in {"<","<=",">",">=","==","!="}:
            kind = lift_kind(a,b)
            if op in {"==","!="}:
                if a.base == b.base or (is_num(a) and is_num(b)):
                    t = T(kind, "bool")
                else:
                    raise TypeError_(f"{op} incompatible {a} vs {b}")
            else:
                if not is_num(a) or not is_num(b): raise TypeError_(f"{op} expects nums")
                t = T(kind, "bool")
        elif op in {"and","or"}:
            if a.base != "bool" or b.base != "bool": raise TypeError_(f"{op} expects bools")
            t = T(lift_kind(a,b), "bool")
        else:
            raise TypeError_(f"Unknown binop {op}")
    elif isinstance(e, A.Call):
        if e.name.startswith("trade."):
            raise TypeError_("trade.* calls are statements only")
        arg_ts = [tc_expr(x, env, states, out, in_tick) for _,x in e.args]
        t = builtin_sig(e.name, arg_ts)
    elif isinstance(e, A.Index):
        bt = tc_expr(e.base, env, states, out, in_tick)
        if bt.kind != "series": raise TypeError_("Indexing requires series")
        t = Scalar(bt.base)
    else:
        raise TypeError_(f"Unknown expr {e}")
    out[id(e)] = t
    return t

def tc_stmt(s: A.Stmt, env: Dict[str,T], states: Dict[str,Dict[str,T]], out: Dict[int,T], in_tick: bool) -> None:
    if isinstance(s, A.IfStmt):
        ct = tc_expr(s.cond, env, states, out, in_tick)
        if ct.base != "bool": raise TypeError_("if condition must be bool/series<bool>")
        for st in s.block:
            tc_stmt(st, env, states, out, in_tick)
        return
    if isinstance(s, A.SetStmt):
        tt = tc_expr(s.target, env, states, out, in_tick)
        et = tc_expr(s.expr, env, states, out, in_tick)
        if not can_assign(tt, et):
            raise TypeError_(f"set: cannot assign {et} to {tt}")
        return
    if isinstance(s, A.ReduceStmt):
        if not in_tick:
            raise TypeError_("reduce only allowed inside on tick")
        tt = tc_expr(s.target, env, states, out, in_tick)
        et = tc_expr(s.expr, env, states, out, in_tick)
        if not (tt.kind == "scalar" and tt.base in {"int","float"}):
            raise TypeError_("reduce target must be numeric scalar state field")
        if not (et.kind == "scalar" and et.base in {"int","float"}):
            raise TypeError_("reduce expr must be numeric scalar")
        return
    if isinstance(s, A.CallStmt):
        if not s.call.name.startswith("trade."):
            raise TypeError_("Only trade.* calls are allowed as statements")
        return
    raise TypeError_(f"Unknown stmt {s}")
