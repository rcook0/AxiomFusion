from __future__ import annotations
from typing import List
from ..ir import IRModule, IRExpr, Lit, Var, BinOp, UnOp, Call, Index, IRStmt, IfStmt, TradeIntent

def emit(mod: IRModule) -> str:
    lines: List[str] = []
    lines.append('"""AxiomFusion v0.1 - Python/pandas skeleton"""')
    lines.append("import pandas as pd")
    lines.append("import numpy as np")
    lines.append("")
    lines.append("def ema(series: pd.Series, n: int) -> pd.Series:")
    lines.append("    return series.ewm(span=int(n), adjust=False).mean()")
    lines.append("")
    lines.append("def sma(series: pd.Series, n: int) -> pd.Series:")
    lines.append("    return series.rolling(int(n)).mean()")
    lines.append("")
    lines.append("def cross_over(a: pd.Series, b: pd.Series) -> pd.Series:")
    lines.append("    return (a > b) & (a.shift(1) <= b.shift(1))")
    lines.append("")
    lines.append("def cross_under(a: pd.Series, b: pd.Series) -> pd.Series:")
    lines.append("    return (a < b) & (a.shift(1) >= b.shift(1))")
    lines.append("")
    lines.append("def risk_qty(risk_frac: float, sl_points: float, equity: float=10000.0, point_value: float=1.0) -> float:")
    lines.append("    # TODO: instrument-specific mapping")
    lines.append("    risk_money = equity * float(risk_frac)")
    lines.append("    return max(0.0, risk_money / (float(sl_points) * point_value))")
    lines.append("")
    lines.append("def compile_signals(df: pd.DataFrame):")
    # inputs
    for inp in mod.inputs:
        lines.append(f"    {inp.name} = {emit_expr(inp.expr)}")
    lines.append("")
    # bindings
    for b in mod.bindings:
        lines.append(f"    {b.name} = {emit_expr_py(b.expr)}")
    lines.append("")
    lines.append("    out = {}")
    for b in mod.bindings:
        lines.append(f"    out['{b.name}'] = {b.name}")
    lines.append("    return out")
    lines.append("")
    lines.append("def generate_intents(df: pd.DataFrame):")
    lines.append("    sig = compile_signals(df)")
    lines.append("    intents = []")
    lines.append("    # v0.1: evaluate intents at bar close, iterate rows")
    lines.append("    for t in range(len(df)):")
    lines.append("        ctx = {k: (v.iloc[t] if hasattr(v,'iloc') else v) for k,v in sig.items()}")
    for h in mod.handlers:
        for st in h.stmts:
            lines.extend(emit_stmt(st, indent='        '))
    lines.append("    return intents")
    lines.append("")
    lines.append("# Expected df columns: open, high, low, close, volume")
    return "\n".join(lines).strip() + "\n"

def emit_expr(e: IRExpr) -> str:
    # inputs init expressions are scalar literals only in examples; keep simple
    if isinstance(e, Lit):
        if isinstance(e.value, str): return repr(e.value)
        return str(e.value).lower() if isinstance(e.value, bool) else str(e.value)
    return "None"

def emit_expr_py(e: IRExpr) -> str:
    if isinstance(e, Lit):
        if isinstance(e.value, str): return repr(e.value)
        return str(e.value).lower() if isinstance(e.value, bool) else str(e.value)
    if isinstance(e, Var):
        if e.name in {"open","high","low","close","volume"}:
            return f"df['{e.name}']"
        return e.name
    if isinstance(e, BinOp):
        op = e.op
        if op == "and": op = "&"
        if op == "or": op = "|"
        return f"({emit_expr_py(e.left)} {op} {emit_expr_py(e.right)})"
    if isinstance(e, UnOp):
        if e.op == "not": return f"(~{emit_expr_py(e.expr)})"
        return f"(-{emit_expr_py(e.expr)})"
    if isinstance(e, Index):
        # series[-k] => shift(k)
        return f"({emit_expr_py(e.base)}.shift({e.k}))"
    if isinstance(e, Call):
        n = e.name
        args = [emit_expr_py(x) for _,x in e.args]
        if n in {"ema","sma","cross_over","cross_under","risk_qty"}:
            return f"{n}({', '.join(args)})"
        if n == "abs": return f"({args[0]}).abs()"
        if n == "min": return f"np.minimum({args[0]}, {args[1]})"
        if n == "max": return f"np.maximum({args[0]}, {args[1]})"
        if n == "vwap": return "df['close']"  # placeholder
        if n == "rsi": return "pd.Series(np.nan, index=df.index)  # TODO rsi"
        if n == "atr": return "pd.Series(np.nan, index=df.index)  # TODO atr"
        return f"{n}({', '.join(args)})"
    return "None"

def emit_stmt(st: IRStmt, indent: str) -> List[str]:
    out: List[str] = []
    if isinstance(st, IfStmt):
        out.append(f"{indent}if {emit_cond(st.cond)}:")
        for s in st.block:
            out.extend(emit_stmt(s, indent=indent+'    '))
        return out
    if isinstance(st, TradeIntent):
        k = st.kind
        tag = expr_in_ctx(st.kwargs.get('tag', Lit('AF')))
        qty = expr_in_ctx(st.kwargs.get('qty', Lit(0.1)))
        slp = expr_in_ctx(st.kwargs.get('sl_points', Lit(0)))
        tpp = expr_in_ctx(st.kwargs.get('tp_points', Lit(0)))
        out.append(f"{indent}intents.append({{'t': t, 'kind': '{k}', 'tag': {tag}, 'qty': {qty}, 'sl_points': {slp}, 'tp_points': {tpp}}})")
        return out
    out.append(f"{indent}# TODO stmt")
    return out

def emit_cond(e: IRExpr) -> str:
    # evaluate on current bar in ctx
    return expr_in_ctx(e)

def expr_in_ctx(e: IRExpr) -> str:
    if isinstance(e, Lit):
        if isinstance(e.value, str): return repr(e.value)
        return str(e.value).lower() if isinstance(e.value, bool) else str(e.value)
    if isinstance(e, Var):
        return f"ctx['{e.name}']"
    if isinstance(e, BinOp):
        op = e.op
        if op == "and": op = "and"
        if op == "or": op = "or"
        return f"({expr_in_ctx(e.left)} {op} {expr_in_ctx(e.right)})"
    if isinstance(e, UnOp):
        if e.op == "not": return f"(not {expr_in_ctx(e.expr)})"
        return f"(-{expr_in_ctx(e.expr)})"
    if isinstance(e, Call):
        # in ctx we assume signals are precomputed, so calls won't appear often
        return "False"
    if isinstance(e, Index):
        return "None"
    return "None"
