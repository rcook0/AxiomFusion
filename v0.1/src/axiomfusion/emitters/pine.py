from __future__ import annotations
from typing import List, Dict, Optional, Tuple
from ..ir import IRModule, IRExpr, Lit, Var, BinOp, UnOp, Call, Index, IRStmt, IfStmt, TradeIntent

def emit(mod: IRModule) -> str:
    uses_trade = "trade" in mod.capabilities
    lines: List[str] = []
    if uses_trade:
        lines.append("//@version=5")
        lines.append('strategy("AxiomFusion Strategy", overlay=true, initial_capital=10000)')
    else:
        lines.append("//@version=5")
        lines.append('indicator("AxiomFusion Indicator", overlay=true)')
    lines.append("")
    # inputs
    for inp in mod.inputs:
        # map types
        t = inp.typ
        if t == "int":
            lines.append(f"{inp.name} = input.int({emit_expr(inp.expr)}, "{inp.name}")")
        elif t == "float":
            lines.append(f"{inp.name} = input.float({emit_expr(inp.expr)}, "{inp.name}")")
        elif t == "bool":
            v = "true" if str(emit_expr(inp.expr)).lower() == "true" else "false"
            lines.append(f"{inp.name} = input.bool({v}, "{inp.name}")")
        else:
            lines.append(f"// TODO input type {t} for {inp.name}")
            lines.append(f"{inp.name} = {emit_expr(inp.expr)}")
    lines.append("")
    # bindings
    for b in mod.bindings:
        lines.append(f"{b.name} = {emit_expr(b.expr)}")
    lines.append("")
    # handlers: v0.1 assumes bar-close, so just use current bar evaluation
    for h in mod.handlers:
        for st in h.stmts:
            lines.extend(emit_stmt(st, indent=""))
    lines.append("")
    # minimal plot suggestion
    lines.append("// plot(close)")
    return "\n".join(lines).strip() + "\n"

def emit_stmt(st: IRStmt, indent: str) -> List[str]:
    out: List[str] = []
    if isinstance(st, IfStmt):
        out.append(f"{indent}if {emit_expr(st.cond)}")
        out.append(f"{indent}    ")
        for s in st.block:
            out.extend(emit_stmt(s, indent=indent))
        return out
    if isinstance(st, TradeIntent):
        k = st.kind
        tag = emit_expr(st.kwargs.get("tag", Lit("AF")))
        qty = emit_expr(st.kwargs.get("qty", Lit(0.1)))
        if k == "enter_long":
            out.append(f'{indent}strategy.entry({tag}, strategy.long, qty={qty})')
        elif k == "enter_short":
            out.append(f'{indent}strategy.entry({tag}, strategy.short, qty={qty})')
        elif k == "exit":
            out.append(f'{indent}strategy.close({tag})')
        else:
            out.append(f"{indent}// TODO trade intent: {k} {st.kwargs}")
        return out
    out.append(f"{indent}// TODO stmt {st}")
    return out

def emit_expr(e: IRExpr) -> str:
    if isinstance(e, Lit):
        if isinstance(e.value, str): return f'"{e.value}"'
        if isinstance(e.value, bool): return "true" if e.value else "false"
        return str(e.value)
    if isinstance(e, Var):
        # map builtin series
        if e.name in {"open","high","low","close","volume"}:
            return e.name
        return e.name
    if isinstance(e, BinOp):
        op = e.op
        if op in {"and","or"}:
            op = "and" if op == "and" else "or"
        return f"({emit_expr(e.left)} {op} {emit_expr(e.right)})"
    if isinstance(e, UnOp):
        if e.op == "not": return f"(not {emit_expr(e.expr)})"
        return f"(-{emit_expr(e.expr)})"
    if isinstance(e, Index):
        # Pine uses history like x[k] with k>=0
        return f"{emit_expr(e.base)}[{e.k}]"
    if isinstance(e, Call):
        n = e.name
        args = [emit_expr(x) for _,x in e.args]
        if n == "ema": return f"ta.ema({args[0]}, {args[1]})"
        if n == "sma": return f"ta.sma({args[0]}, {args[1]})"
        if n == "rsi": return f"ta.rsi({args[0]}, {args[1]})"
        if n == "atr": return f"ta.atr({args[0]})"
        if n == "vwap": return "ta.vwap(close)"
        if n == "cross_over": return f"ta.crossover({args[0]}, {args[1]})"
        if n == "cross_under": return f"ta.crossunder({args[0]}, {args[1]})"
        if n == "abs": return f"math.abs({args[0]})"
        if n == "min": return f"math.min({args[0]}, {args[1]})"
        if n == "max": return f"math.max({args[0]}, {args[1]})"
        if n == "risk_qty": return args[0]  # placeholder
        return f"{n}({', '.join(args)})"
    return "na"
