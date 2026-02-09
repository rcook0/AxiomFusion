from __future__ import annotations
from typing import List
from ..ir import IRModule, IRExpr, Lit, Var, Member, BinOp, UnOp, Call, Index, IRStmt, IfStmt, TradeIntent, SetStmt, ReduceStmt

def emit(mod: IRModule) -> str:
    lines: List[str] = []
    lines.append("// AxiomFusion v0.3 - MQL5 EA skeleton (bar + tick + state + reducers)")
    lines.append("#property strict")
    lines.append("#include <Trade/Trade.mqh>")
    lines.append("CTrade trade;")
    lines.append("")

    if mod.states:
        lines.append("// ---- Persistent state (in-memory) ----")
        for st in mod.states:
            lines.append(f"// state {st.name} v{st.version}")
            for f in st.fields:
                lines.append(f"{map_scalar_type(f.typ)} {st.name}_{f.name} = {emit_expr(f.init)};")
        lines.append("")

    for inp in mod.inputs:
        lines.append(f"input {map_type(inp.typ)} {inp.name} = {emit_expr(inp.expr)};")
    lines.append("")
    lines.append("datetime __lastBarTime = 0;")
    lines.append("bool IsNewBar(){ datetime t=iTime(_Symbol,_Period,0); if(t==0) return false; if(t!=__lastBarTime){__lastBarTime=t; return true;} return false; }")
    lines.append("")

    if mod.states:
        lines.append("void __ResetReducers(){")
        for st in mod.states:
            for f in st.fields:
                lines.append(f"  {st.name}_{f.name} = {emit_expr(f.init)};")
        lines.append("}")
        lines.append("")

    lines.append("int OnInit(){")
    if mod.states:
        lines.append("  __ResetReducers();")
    lines.append("  return(INIT_SUCCEEDED);")
    lines.append("}")
    lines.append("")
    lines.append("void OnTick(){")
    lines.append("  bool newBar = IsNewBar();")
    lines.append("")

    for b in mod.bindings:
        lines.append(f"  // {b.kind} {b.name}")
        lines.append(f"  auto {b.name} = {emit_expr(b.expr)};")
    lines.append("")

    for h in mod.handlers:
        if h.kind != "tick": 
            continue
        lines.append("  // ---- on tick ----")
        for st in h.stmts:
            lines.extend(emit_stmt(st, indent="  "))
        lines.append("")

    lines.append("  if(newBar){")
    for h in mod.handlers:
        if h.kind != "bar": 
            continue
        lines.append("    // ---- on bar ----")
        for st in h.stmts:
            lines.extend(emit_stmt(st, indent="    "))
    if mod.states:
        lines.append("    __ResetReducers();")
    lines.append("  }")
    lines.append("}")
    lines.append("")
    lines.append("// TODO: persist state across restarts + version migration policy.")
    return "\n".join(lines).strip() + "\n"

def map_scalar_type(t: str) -> str:
    return {"int":"int","float":"double","bool":"bool","string":"string"}.get(t,"double")

def map_type(t: str) -> str:
    return "double" if t.startswith("series<") else map_scalar_type(t)

def emit_stmt(st: IRStmt, indent: str) -> List[str]:
    out: List[str] = []
    if isinstance(st, IfStmt):
        out.append(f"{indent}if({emit_expr(st.cond)})"+" {")
        for s in st.block:
            out.extend(emit_stmt(s, indent=indent+"  "))
        out.append(f"{indent}"+"}")
        return out
    if isinstance(st, SetStmt):
        out.append(f"{indent}{emit_member(st.target)} = {emit_expr(st.expr)};")
        return out
    if isinstance(st, ReduceStmt):
        tgt = emit_member(st.target); ex = emit_expr(st.expr)
        if st.op == "sum": out.append(f"{indent}{tgt} += {ex};")
        elif st.op == "min": out.append(f"{indent}{tgt} = MathMin({tgt}, {ex});")
        elif st.op == "max": out.append(f"{indent}{tgt} = MathMax({tgt}, {ex});")
        elif st.op == "last": out.append(f"{indent}{tgt} = {ex};")
        else: out.append(f"{indent}// TODO reduce op {st.op}")
        return out
    if isinstance(st, TradeIntent):
        tag = emit_expr(st.kwargs.get("tag", Lit("AF")))
        qty = emit_expr(st.kwargs.get("qty", Lit(0.1)))
        if st.kind == "enter_long":
            out.append(f"{indent}trade.Buy({qty}, _Symbol, 0.0, 0.0, 0.0, {tag});")
        elif st.kind == "enter_short":
            out.append(f"{indent}trade.Sell({qty}, _Symbol, 0.0, 0.0, 0.0, {tag});")
        elif st.kind == "exit":
            out.append(f"{indent}// TODO: close by tag {tag}")
        else:
            out.append(f"{indent}// TODO intent {st.kind}")
        return out
    out.append(f"{indent}// TODO stmt")
    return out

def emit_member(m: Member) -> str:
    if isinstance(m.obj, Var):
        return f"{m.obj.name}_{m.field}"
    return "/*member*/"

def emit_expr(e: IRExpr) -> str:
    if isinstance(e, Lit):
        if isinstance(e.value, str): return f"\"{e.value}\""
        if isinstance(e.value, bool): return "true" if e.value else "false"
        return str(e.value)
    if isinstance(e, Var):
        if e.name == "close": return "iClose(_Symbol,_Period,1)"
        if e.name == "open": return "iOpen(_Symbol,_Period,1)"
        if e.name == "high": return "iHigh(_Symbol,_Period,1)"
        if e.name == "low": return "iLow(_Symbol,_Period,1)"
        if e.name == "volume": return "iVolume(_Symbol,_Period,1)"
        if e.name == "bid": return "SymbolInfoDouble(_Symbol, SYMBOL_BID)"
        if e.name == "ask": return "SymbolInfoDouble(_Symbol, SYMBOL_ASK)"
        if e.name == "last": return "SymbolInfoDouble(_Symbol, SYMBOL_LAST)"
        if e.name == "tick_volume": return "iVolume(_Symbol,_Period,0)"
        return e.name
    if isinstance(e, Member):
        return emit_member(e)
    if isinstance(e, BinOp):
        op = e.op
        op = "&&" if op == "and" else "||" if op == "or" else op
        return f"({emit_expr(e.left)} {op} {emit_expr(e.right)})"
    if isinstance(e, UnOp):
        return f"(!{emit_expr(e.expr)})" if e.op == "not" else f"(-{emit_expr(e.expr)})"
    if isinstance(e, Index):
        return f"/*idx*/({emit_expr(e.base)})"
    if isinstance(e, Call):
        n = e.name; args = [emit_expr(x) for _,x in e.args]
        if n == "abs": return f"MathAbs({args[0]})"
        if n == "min": return f"MathMin({args[0]}, {args[1]})"
        if n == "max": return f"MathMax({args[0]}, {args[1]})"
        if n == "series_from":
            sym = args[0]
            tf = args[1]
            fld = args[2]
            return mql_series_from(sym, tf, fld)
        return f"/*{n}*/({args[0] if args else 0})"
    return "0"


def mql_series_from(sym: str, tf: str, fld: str) -> str:
    # Best-effort mapping for literal tf/fld. If non-literal, fall back to iClose on current period.
    tf_map = {
        '"1"': 'PERIOD_M1',
        '"5"': 'PERIOD_M5',
        '"15"': 'PERIOD_M15',
        '"30"': 'PERIOD_M30',
        '"60"': 'PERIOD_H1',
        '"240"': 'PERIOD_H4',
        '"D"': 'PERIOD_D1',
        '"W"': 'PERIOD_W1',
        '"MN"': 'PERIOD_MN1',
    }
    fld_map = {
        '"open"': 'iOpen',
        '"high"': 'iHigh',
        '"low"': 'iLow',
        '"close"': 'iClose',
        '"volume"': 'iVolume',
    }
    period = tf_map.get(tf, "_Period")
    fn = fld_map.get(fld, "iClose")
    # shift=1 => latest completed bar for that timeframe
    if fn == "iVolume":
        return f"{fn}({sym}, {period}, 1)"
    return f"{fn}({sym}, {period}, 1)"
