from __future__ import annotations
from typing import List
from ..ir import IRModule, IRExpr, Lit, Var, Member, BinOp, UnOp, Call, Index, IRStmt, IfStmt, TradeIntent, SetStmt, ReduceStmt

def emit(mod: IRModule) -> str:
    uses_trade = "trade" in mod.capabilities
    lines: List[str] = []
    lines.append("//@version=5")
    lines.append('strategy("AxiomFusion Strategy", overlay=true)' if uses_trade else 'indicator("AxiomFusion Indicator", overlay=true)')
    lines.append("")

    if mod.states:
        lines.append("// --- state (approximated in Pine) ---")
        for st in mod.states:
            lines.append(f"// state {st.name} v{st.version}")
            for f in st.fields:
                lines.append(f"var {st.name}_{f.name} = {emit_expr(f.init)}")
        lines.append("")

    for inp in mod.inputs:
        t = inp.typ
        if t == "int":
            lines.append(f"{inp.name} = input.int({emit_expr(inp.expr)}, "{inp.name}")")
        elif t == "float":
            lines.append(f"{inp.name} = input.float({emit_expr(inp.expr)}, "{inp.name}")")
        elif t == "bool":
            lines.append(f"{inp.name} = input.bool({emit_expr(inp.expr)}, "{inp.name}")")
        else:
            lines.append(f"// TODO input type {t} for {inp.name}")
            lines.append(f"{inp.name} = {emit_expr(inp.expr)}")
    lines.append("")

    for b in mod.bindings:
        lines.append(f"{b.name} = {emit_expr(b.expr)}")
    lines.append("")

    for h in mod.handlers:
        if h.kind == "tick":
            lines.append("// NOTE: on tick not supported in Pine; reducer/state updates omitted.")
            continue
        for st in h.stmts:
            lines.extend(emit_stmt(st, indent=""))
    lines.append("")
    return "\n".join(lines).strip() + "\n"

def emit_stmt(st: IRStmt, indent: str) -> List[str]:
    out: List[str] = []
    if isinstance(st, IfStmt):
        out.append(f"{indent}if {emit_expr(st.cond)}")
        for s in st.block:
            out.extend(emit_stmt(s, indent=indent))
        return out
    if isinstance(st, TradeIntent):
        tag = emit_expr(st.kwargs.get("tag", Lit("AF")))
        qty = emit_expr(st.kwargs.get("qty", Lit(0.1)))
        if st.kind == "enter_long":
            out.append(f'{indent}strategy.entry({tag}, strategy.long, qty={qty})')
        elif st.kind == "enter_short":
            out.append(f'{indent}strategy.entry({tag}, strategy.short, qty={qty})')
        elif st.kind == "exit":
            out.append(f'{indent}strategy.close({tag})')
        else:
            out.append(f"{indent}// TODO trade intent: {st.kind}")
        return out
    if isinstance(st, (SetStmt, ReduceStmt)):
        out.append(f"{indent}// TODO shell stmt not emitted in Pine: {st}")
        return out
    out.append(f"{indent}// TODO stmt {st}")
    return out

def emit_expr(e: IRExpr) -> str:
    if isinstance(e, Lit):
        if isinstance(e.value, str): return f'"{e.value}"'
        if isinstance(e.value, bool): return "true" if e.value else "false"
        return str(e.value)
    if isinstance(e, Var):
        if e.name in {"bid","ask","last","tick_volume"}:
            return "na"
        return e.name
    if isinstance(e, Member):
        if isinstance(e.obj, Var):
            return f"{e.obj.name}_{e.field}"
        return "na"
    if isinstance(e, BinOp):
        op = e.op
        return f"({emit_expr(e.left)} {op} {emit_expr(e.right)})"
    if isinstance(e, UnOp):
        return f"(not {emit_expr(e.expr)})" if e.op == "not" else f"(-{emit_expr(e.expr)})"
    if isinstance(e, Index):
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
        if n == "series_from":
            sym, tf, fld = args[0], args[1], args[2]
            return f"request.security({sym}, {tf}, {fld_to_expr(fld)})"
        if n == "risk_qty": return args[0]
if n == "wma": return f"ta.wma({args[0]}, {args[1]})"
if n == "highest": return f"ta.highest({args[0]}, {args[1]})"
if n == "lowest": return f"ta.lowest({args[0]}, {args[1]})"
if n == "stddev": return f"ta.stdev({args[0]}, {args[1]})"
if n == "bb_middle": return f"ta.sma({args[0]}, {args[1]})"
if n == "bb_upper":
    basis = f"ta.sma({args[0]}, {args[1]})"
    dev = f"(ta.stdev({args[0]}, {args[1]}) * {args[2]})"
    return f"({basis} + {dev})"
if n == "bb_lower":
    basis = f"ta.sma({args[0]}, {args[1]})"
    dev = f"(ta.stdev({args[0]}, {args[1]}) * {args[2]})"
    return f"({basis} - {dev})"
if n == "roc": return f"ta.roc({args[0]}, {args[1]})"
if n == "hl2": return "hl2"
if n == "ohlc4": return "ohlc4"
if n == "macd_line":
    return f"(ta.ema({args[0]}, {args[1]}) - ta.ema({args[0]}, {args[2]}))"
if n == "macd_signal":
    line = f"(ta.ema({args[0]}, {args[1]}) - ta.ema({args[0]}, {args[2]}))"
    return f"ta.ema({line}, {args[3]})"
if n == "macd_hist":
    line = f"(ta.ema({args[0]}, {args[1]}) - ta.ema({args[0]}, {args[2]}))"
    sig = f"ta.ema({line}, {args[3]})"
    return f"({line} - {sig})"

        return f"{n}({', '.join(args)})"
    return "na"


# field string -> Pine series expr
def fld_to_expr(fld: str) -> str:
    m = fld.strip()
    if len(m) >= 2 and m[0] == '"' and m[-1] == '"':
        m = m[1:-1]
    m = m.lower()
    if m in {"open","high","low","close","volume"}:
        return m
    return "close"
