from .provenance import Provenance
from __future__ import annotations
from dataclasses import replace
from typing import Dict, List, Set, Tuple, Optional
from .ir import (
    IRModule, IRInput, IRBinding, IRState, IRHandler,
    IRExpr, Lit, Var, Member, BinOp, UnOp, Call, Index,
    IRStmt, IfStmt, SetStmt, ReduceStmt, TradeIntent
)

class OptError(Exception): ...

def optimize(mod: IRModule, level: str = "O2") -> IRModule:
    if level.upper() == "O0":
        return mod
    m = mod
    m = const_fold_module(m)
    m = simplify_module(m)
    if level.upper() in {"O2","O3"}:
        m = dce_module(m)
        m = inline_trivial_module(m)
    if level.upper() == "O3":
        m = cse_module(m)
    return m

# -------- constant folding + simplify --------
def const_fold_module(m: IRModule) -> IRModule:
    binds = [replace(b, expr=const_fold_expr(b.expr)) for b in m.bindings]
    inputs = [replace(i, expr=const_fold_expr(i.expr)) for i in m.inputs]
    states = [
        replace(s, fields=[replace(f, init=const_fold_expr(f.init)) for f in s.fields])
        for s in m.states
    ]
    handlers = [replace(h, stmts=[const_fold_stmt(s) for s in h.stmts]) for h in m.handlers]
    return replace(m, inputs=inputs, bindings=binds, states=states, handlers=handlers)

def const_fold_stmt(s: IRStmt) -> IRStmt:
    if isinstance(s, IfStmt):
        return replace(s, cond=const_fold_expr(s.cond), block=[const_fold_stmt(x) for x in s.block])
    if isinstance(s, SetStmt):
        return replace(s, expr=const_fold_expr(s.expr))
    if isinstance(s, ReduceStmt):
        return replace(s, expr=const_fold_expr(s.expr))
    if isinstance(s, TradeIntent):
        return replace(s, kwargs={k: const_fold_expr(v) for k,v in s.kwargs.items()})
    return s

def const_fold_expr(e: IRExpr) -> IRExpr:
    if isinstance(e, (Lit, Var, Member)):
        return e
    if isinstance(e, Index):
        return replace(e, base=const_fold_expr(e.base))
    if isinstance(e, UnOp):
        ex = const_fold_expr(e.expr)
        if isinstance(ex, Lit):
            if e.op == "not" and isinstance(ex.value, bool):
                return Lit(not ex.value)
            if e.op == "-" and isinstance(ex.value, (int,float)):
                return Lit(-ex.value)
        return replace(e, expr=ex)
    if isinstance(e, BinOp):
        a = const_fold_expr(e.left); b = const_fold_expr(e.right)
        if isinstance(a, Lit) and isinstance(b, Lit):
            return Lit(eval_bin(e.op, a.value, b.value))
        return replace(e, left=a, right=b)
    if isinstance(e, Call):
        args = [(kw, const_fold_expr(ex)) for kw,ex in e.args]
        # Only fold a tiny set of safe pure ops
        if all(isinstance(ex, Lit) for _,ex in args) and e.name in {"abs","min","max","nz"}:
            vals = [ex.value for _,ex in args]
            if e.name == "abs": return Lit(abs(vals[0]))
            if e.name == "min": return Lit(min(vals[0], vals[1]))
            if e.name == "max": return Lit(max(vals[0], vals[1]))
            if e.name == "nz": return Lit(vals[0] if vals[0] is not None else vals[1])
        return replace(e, args=args)
    return e

def eval_bin(op: str, a, b):
    if op in {"+","-","*","/","<","<=",">",">=","==","!="}:
        return eval(f"a {op} b", {"a":a,"b":b})
    if op == "and": return bool(a) and bool(b)
    if op == "or": return bool(a) or bool(b)
    raise OptError(f"unknown op {op}")

def simplify_module(m: IRModule) -> IRModule:
    binds = [replace(b, expr=simplify_expr(b.expr)) for b in m.bindings]
    inputs = [replace(i, expr=simplify_expr(i.expr)) for i in m.inputs]
    states = [
        replace(s, fields=[replace(f, init=simplify_expr(f.init)) for f in s.fields])
        for s in m.states
    ]
    handlers = [replace(h, stmts=[simplify_stmt(s) for s in h.stmts]) for h in m.handlers]
    return replace(m, inputs=inputs, bindings=binds, states=states, handlers=handlers)

def simplify_stmt(s: IRStmt) -> IRStmt:
    if isinstance(s, IfStmt):
        cond = simplify_expr(s.cond)
        block = [simplify_stmt(x) for x in s.block]
        # prune always-false
        if isinstance(cond, Lit) and cond.value is False:
            return IfStmt(Lit(False), [])
        return replace(s, cond=cond, block=block)
    if isinstance(s, SetStmt):
        return replace(s, expr=simplify_expr(s.expr))
    if isinstance(s, ReduceStmt):
        return replace(s, expr=simplify_expr(s.expr))
    if isinstance(s, TradeIntent):
        return replace(s, kwargs={k: simplify_expr(v) for k,v in s.kwargs.items()})
    return s

def simplify_expr(e: IRExpr) -> IRExpr:
    if isinstance(e, (Lit, Var, Member)):
        return e
    if isinstance(e, Index):
        return replace(e, base=simplify_expr(e.base))
    if isinstance(e, UnOp):
        ex = simplify_expr(e.expr)
        if e.op == "not" and isinstance(ex, UnOp) and ex.op == "not":
            return ex.expr
        return replace(e, expr=ex)
    if isinstance(e, BinOp):
        a = simplify_expr(e.left); b = simplify_expr(e.right)
        op = e.op
        # bool identities
        if op == "and":
            if isinstance(a, Lit) and isinstance(a.value, bool):
                return b if a.value else Lit(False)
            if isinstance(b, Lit) and isinstance(b.value, bool):
                return a if b.value else Lit(False)
        if op == "or":
            if isinstance(a, Lit) and isinstance(a.value, bool):
                return Lit(True) if a.value else b
            if isinstance(b, Lit) and isinstance(b.value, bool):
                return Lit(True) if b.value else a
        # numeric identities
        if op == "+":
            if isinstance(b, Lit) and b.value == 0: return a
            if isinstance(a, Lit) and a.value == 0: return b
        if op == "*":
            if isinstance(b, Lit) and b.value == 1: return a
            if isinstance(a, Lit) and a.value == 1: return b
            if (isinstance(a, Lit) and a.value == 0) or (isinstance(b, Lit) and b.value == 0):
                return Lit(0)
        return replace(e, left=a, right=b)
    if isinstance(e, Call):
        return replace(e, args=[(kw, simplify_expr(ex)) for kw,ex in e.args])
    return e

# -------- DCE + inlining --------
def dce_module(m: IRModule) -> IRModule:
    # liveness over bindings: starting from handlers and inputs
    uses: Set[str] = set()
    def use_expr(e: IRExpr):
        if isinstance(e, Var):
            uses.add(e.name)
        elif isinstance(e, Member):
            use_expr(e.obj)
        elif isinstance(e, BinOp):
            use_expr(e.left); use_expr(e.right)
        elif isinstance(e, UnOp):
            use_expr(e.expr)
        elif isinstance(e, Call):
            for _,ex in e.args: use_expr(ex)
        elif isinstance(e, Index):
            use_expr(e.base)
        else:
            return
    def use_stmt(s: IRStmt):
        if isinstance(s, IfStmt):
            use_expr(s.cond)
            for x in s.block: use_stmt(x)
        elif isinstance(s, SetStmt):
            use_expr(s.expr); use_expr(s.target.obj)
        elif isinstance(s, ReduceStmt):
            use_expr(s.expr); use_expr(s.target.obj)
        elif isinstance(s, TradeIntent):
            for _,ex in s.kwargs.items(): use_expr(ex)

    for inp in m.inputs:
        use_expr(inp.expr)
    for h in m.handlers:
        for s in h.stmts:
            use_stmt(s)

    # fixpoint: any binding used makes its expr live too
    live = set(uses)
    changed = True
    bind_map = {b.name: b for b in m.bindings}
    while changed:
        changed = False
        for name in list(live):
            b = bind_map.get(name)
            if b:
                before = set(live)
                use_expr(b.expr)
                if not set(uses).issubset(before):
                    live = set(uses)
                    changed = True

    new_binds = [b for b in m.bindings if b.name in live]
    return replace(m, bindings=new_binds)

def inline_trivial_module(m: IRModule) -> IRModule:
    # inline let bindings used once and that are Lit/Var/Member only
    counts: Dict[str,int] = {}
    def count_expr(e: IRExpr):
        if isinstance(e, Var):
            counts[e.name] = counts.get(e.name,0)+1
        elif isinstance(e, Member):
            count_expr(e.obj)
        elif isinstance(e, BinOp):
            count_expr(e.left); count_expr(e.right)
        elif isinstance(e, UnOp):
            count_expr(e.expr)
        elif isinstance(e, Call):
            for _,ex in e.args: count_expr(ex)
        elif isinstance(e, Index):
            count_expr(e.base)
    def count_stmt(s: IRStmt):
        if isinstance(s, IfStmt):
            count_expr(s.cond); [count_stmt(x) for x in s.block]
        elif isinstance(s, SetStmt):
            count_expr(s.expr); count_expr(s.target.obj)
        elif isinstance(s, ReduceStmt):
            count_expr(s.expr); count_expr(s.target.obj)
        elif isinstance(s, TradeIntent):
            for ex in s.kwargs.values(): count_expr(ex)

    for b in m.bindings:
        count_expr(b.expr)
    for h in m.handlers:
        for s in h.stmts:
            count_stmt(s)

    inline: Dict[str, IRExpr] = {}
    for b in m.bindings:
        if b.kind == "let" and counts.get(b.name,0) <= 1 and isinstance(b.expr, (Lit,Var,Member)):
            inline[b.name] = b.expr

    def subst_expr(e: IRExpr) -> IRExpr:
        if isinstance(e, Var) and e.name in inline:
            return inline[e.name]
        if isinstance(e, Member):
            return replace(e, obj=subst_expr(e.obj))
        if isinstance(e, BinOp):
            return replace(e, left=subst_expr(e.left), right=subst_expr(e.right))
        if isinstance(e, UnOp):
            return replace(e, expr=subst_expr(e.expr))
        if isinstance(e, Call):
            return replace(e, args=[(kw, subst_expr(ex)) for kw,ex in e.args])
        if isinstance(e, Index):
            return replace(e, base=subst_expr(e.base))
        return e

    new_binds = [b for b in m.bindings if b.name not in inline]
    new_binds = [replace(b, expr=subst_expr(b.expr)) for b in new_binds]
    handlers = [replace(h, stmts=[subst_stmt(s, subst_expr) for s in h.stmts]) for h in m.handlers]
    inputs = [replace(i, expr=subst_expr(i.expr)) for i in m.inputs]
    return replace(m, bindings=new_binds, handlers=handlers, inputs=inputs)

def subst_stmt(s: IRStmt, subst_expr):
    if isinstance(s, IfStmt):
        return replace(s, cond=subst_expr(s.cond), block=[subst_stmt(x, subst_expr) for x in s.block])
    if isinstance(s, SetStmt):
        return replace(s, expr=subst_expr(s.expr))
    if isinstance(s, ReduceStmt):
        return replace(s, expr=subst_expr(s.expr))
    if isinstance(s, TradeIntent):
        return replace(s, kwargs={k: subst_expr(v) for k,v in s.kwargs.items()})
    return s

# -------- limited CSE --------
def cse_module(m: IRModule) -> IRModule:
    # Very conservative: only hoist identical Lit/Var/Member/BinOp trees in bindings.
    # Creates synthetic lets __cseN and replaces occurrences.
    seen: Dict[str, str] = {}
    new_bindings: List[IRBinding] = []
    counter = 0

    def key(e: IRExpr) -> Optional[str]:
        if isinstance(e, (Lit,Var,Member,BinOp,UnOp,Index,Call)):
            return repr(e)
        return None

    def rewrite(e: IRExpr) -> IRExpr:
        nonlocal counter
        k = key(e)
        if k is None:
            return e
        if k in seen:
            return Var(seen[k])
        # only hoist if somewhat complex
        if isinstance(e, BinOp) or isinstance(e, Call):
            name = f"__cse{counter}"
            counter += 1
            seen[k] = name
            new_bindings.append(IRBinding("let", name, e, None))
            return Var(name)
        return e

    # rewrite existing bindings
    for b in m.bindings:
        expr = rewrite(b.expr)
        new_bindings.append(replace(b, expr=expr))
    # rewrite handlers
    handlers = [replace(h, stmts=[cse_stmt(s, rewrite) for s in h.stmts]) for h in m.handlers]
    return replace(m, bindings=new_bindings, handlers=handlers)

def cse_stmt(s: IRStmt, rw):
    if isinstance(s, IfStmt):
        return replace(s, cond=rw(s.cond), block=[cse_stmt(x, rw) for x in s.block])
    if isinstance(s, SetStmt):
        return replace(s, expr=rw(s.expr))
    if isinstance(s, ReduceStmt):
        return replace(s, expr=rw(s.expr))
    if isinstance(s, TradeIntent):
        return replace(s, kwargs={k: rw(v) for k,v in s.kwargs.items()})
    return s


def _id_for_ir(node) -> str:
    import hashlib
    return hashlib.sha1(repr(node).encode("utf-8")).hexdigest()[:12]
