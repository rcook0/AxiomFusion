from __future__ import annotations
from typing import List
from ..ir import IRModule, IRExpr, Lit, Var, BinOp, UnOp, Call, Index, IRStmt, IfStmt, TradeIntent

def emit(mod: IRModule) -> str:
    lines: List[str] = []
    lines.append("// AxiomFusion v0.1 - MQL5 EA skeleton")
    lines.append("#property strict")
    lines.append("")
    lines.append("#include <Trade/Trade.mqh>")
    lines.append("CTrade trade;")
    lines.append("")
    # inputs -> input vars
    for inp in mod.inputs:
        mql_t = map_type(inp.typ)
        lines.append(f"input {mql_t} {inp.name} = {emit_expr(inp.expr)};")
    lines.append("")
    lines.append("datetime __lastBarTime = 0;")
    lines.append("")
    lines.append("bool IsNewBar() {")
    lines.append("  datetime t = iTime(_Symbol, _Period, 0);")
    lines.append("  if(t == 0) return false;")
    lines.append("  if(t != __lastBarTime) { __lastBarTime = t; return true; }")
    lines.append("  return false;")
    lines.append("}")
    lines.append("")
    # bindings - compute on demand in functions
    lines.append("// ---- Core bindings (computed at bar close) ----")
    for b in mod.bindings:
        # declare as local in OnTick in v0.1
        pass
    lines.append("")
    lines.append("int OnInit(){ return(INIT_SUCCEEDED); }")
    lines.append("")
    lines.append("void OnTick(){")
    lines.append("  if(!IsNewBar()) return; // v0.1 bar-close evaluation")
    lines.append("")
    # compute bindings as local doubles/bools (very stubby)
    for b in mod.bindings:
        lines.append(f"  // {b.kind} {b.name}")
        lines.append(f"  auto {b.name} = {emit_expr(b.expr)};")
    lines.append("")
    # handlers
    for h in mod.handlers:
        for st in h.stmts:
            lines.extend(emit_stmt(st, indent="  "))
    lines.append("}")
    lines.append("")
    lines.append("// NOTE: This is a stub emitter. TODO:")
    lines.append("// - Map ema/sma/rsi to iMA/iRSI handles or custom computation")
    lines.append("// - Implement cross_over/cross_under robustly")
    lines.append("// - Implement risk_qty() sizing using AccountInfoDouble and SymbolInfoDouble tick value")
    lines.append("// - Add magic number + position tagging")
    return "\n".join(lines).strip() + "\n"

def map_type(t: str) -> str:
    return {
        "int": "int",
        "float": "double",
        "bool": "bool",
        "string": "string",
    }.get(t, "double")

def emit_stmt(st: IRStmt, indent: str) -> List[str]:
    out: List[str] = []
    if isinstance(st, IfStmt):
        out.append(f"{indent}if({emit_expr(st.cond)})"+" {")
        for s in st.block:
            out.extend(emit_stmt(s, indent=indent+"  "))
        out.append(f"{indent}"+"}")
        return out
    if isinstance(st, TradeIntent):
        k = st.kind
        tag = emit_expr(st.kwargs.get("tag", Lit("AF")))
        qty = emit_expr(st.kwargs.get("qty", Lit(0.1)))
        slp = emit_expr(st.kwargs.get("sl_points", Lit(0)))
        tpp = emit_expr(st.kwargs.get("tp_points", Lit(0)))
        out.append(f"{indent}// intent: {k} tag={tag}")
        if k == "enter_long":
            out.append(f"{indent}trade.Buy({qty}, _Symbol, 0.0, 0.0, 0.0, {tag}); // TODO SL/TP points {slp}/{tpp}")
        elif k == "enter_short":
            out.append(f"{indent}trade.Sell({qty}, _Symbol, 0.0, 0.0, 0.0, {tag}); // TODO SL/TP points {slp}/{tpp}")
        elif k == "exit":
            out.append(f"{indent}// TODO: close by tag {tag} (positions filter + trade.PositionClose)")
        else:
            out.append(f"{indent}// TODO intent {k}")
        return out
    out.append(f"{indent}// TODO stmt")
    return out

def emit_expr(e: IRExpr) -> str:
    if isinstance(e, Lit):
        if isinstance(e.value, str): return f"\"{e.value}\""
        if isinstance(e.value, bool): return "true" if e.value else "false"
        return str(e.value)
    if isinstance(e, Var):
        # Built-in OHLCV access at bar close (index 1 = closed bar, 0 = forming bar)
        if e.name == "close": return "iClose(_Symbol,_Period,1)"
        if e.name == "open": return "iOpen(_Symbol,_Period,1)"
        if e.name == "high": return "iHigh(_Symbol,_Period,1)"
        if e.name == "low": return "iLow(_Symbol,_Period,1)"
        if e.name == "volume": return "iVolume(_Symbol,_Period,1)"
        return e.name
    if isinstance(e, BinOp):
        op = e.op
        if op == "and": op = "&&"
        if op == "or": op = "||"
        return f"({emit_expr(e.left)} {op} {emit_expr(e.right)})"
    if isinstance(e, UnOp):
        if e.op == "not": return f"(!{emit_expr(e.expr)})"
        return f"(-{emit_expr(e.expr)})"
    if isinstance(e, Index):
        # series[-k] means k bars ago; use iClose with shift (1+k-1?) here simplistic:
        return f"/*idx*/({emit_expr(e.base)})"
    if isinstance(e, Call):
        n = e.name
        args = [emit_expr(x) for _,x in e.args]
        # Stub mappings:
        if n == "ema": return f"/*ema*/({args[0]})"
        if n == "sma": return f"/*sma*/({args[0]})"
        if n == "rsi": return f"/*rsi*/(50.0)"
        if n == "atr": return f"/*atr*/(0.0)"
        if n == "vwap": return f"/*vwap*/({emit_expr(Var('close'))})"
        if n == "cross_over": return f"/*cross_over*/(false)"
        if n == "cross_under": return f"/*cross_under*/(false)"
        if n == "abs": return f"MathAbs({args[0]})"
        if n == "min": return f"MathMin({args[0]}, {args[1]})"
        if n == "max": return f"MathMax({args[0]}, {args[1]})"
        if n == "risk_qty": return f"/*risk_qty*/({args[0]})"
        return f"{n}({', '.join(args)})"
    return "0"
