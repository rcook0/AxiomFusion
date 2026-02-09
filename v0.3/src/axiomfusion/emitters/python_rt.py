from __future__ import annotations
from typing import List, Dict
from ..ir import IRModule, IRExpr, Lit, Var, Member, BinOp, UnOp, Call, Index, IRStmt, IfStmt, TradeIntent, SetStmt, ReduceStmt

def emit(mod: IRModule) -> str:
    lines: List[str] = []
    lines.append('"""AxiomFusion v0.3 - Python skeleton (bar + tick + state + reducers)"""')
    lines.append("import pandas as pd")
    lines.append("")
    lines.append("def run(df: pd.DataFrame):")
    lines.append("    state = {}")
    for st in mod.states:
        lines.append(f"    state['{st.name}'] = {{'__v': {st.version}}}")
        for f in st.fields:
            lines.append(f"    state['{st.name}']['{f.name}'] = {lit0(f.init)}")
    lines.append("    intents = []")
    lines.append("    for t in range(len(df)):")
    lines.append("        ctx = {k: df[k].iloc[t] for k in ['open','high','low','close','volume']}")
    lines.append("        ctx['bid']=ctx['close']; ctx['ask']=ctx['close']; ctx['last']=ctx['close']; ctx['tick_volume']=ctx['volume']")
    for h in mod.handlers:
        if h.kind == "tick":
            lines.append("        # on tick (stub: once per bar row)")
            for st in h.stmts:
                lines.extend(emit_stmt(st, "        "))
    for h in mod.handlers:
        if h.kind == "bar":
            lines.append("        # on bar")
            for st in h.stmts:
                lines.extend(emit_stmt(st, "        "))
    lines.append("    return intents, state")
    return "\n".join(lines) + "\n"

def lit0(e: IRExpr) -> str:
    if isinstance(e, Lit):
        if isinstance(e.value, str): return repr(e.value)
        return str(e.value).lower() if isinstance(e.value,bool) else str(e.value)
    return "0"

def emit_stmt(st: IRStmt, ind: str) -> List[str]:
    out: List[str] = []
    if isinstance(st, IfStmt):
        out.append(f"{ind}if {emit_value(st.cond)}:")
        for s in st.block:
            out.extend(emit_stmt(s, ind+'    '))
        return out
    if isinstance(st, SetStmt):
        out.append(f"{ind}{emit_lvalue(st.target)} = {emit_value(st.expr)}")
        return out
    if isinstance(st, ReduceStmt):
        tgt = emit_lvalue(st.target); ex = emit_value(st.expr)
        if st.op == 'sum': out.append(f"{ind}{tgt} += {ex}")
        elif st.op == 'min': out.append(f"{ind}{tgt} = min({tgt}, {ex})")
        elif st.op == 'max': out.append(f"{ind}{tgt} = max({tgt}, {ex})")
        elif st.op == 'last': out.append(f"{ind}{tgt} = {ex}")
        return out
    if isinstance(st, TradeIntent):
        out.append(f"{ind}intents.append({{'t': t, 'kind': '{st.kind}', 'kwargs': {emit_kwargs(st.kwargs)}}})")
        return out
    out.append(f"{ind}# TODO {st}")
    return out

def emit_kwargs(kwargs: Dict[str, IRExpr]) -> str:
    parts=[]
    for k,v in kwargs.items():
        parts.append(f"'{k}': {emit_value(v)}")
    return '{' + ', '.join(parts) + '}'

def emit_lvalue(m: Member) -> str:
    if isinstance(m.obj, Var):
        return f"state['{m.obj.name}']['{m.field}']"
    return "None"

def emit_value(e: IRExpr) -> str:
    if isinstance(e, Lit):
        if isinstance(e.value, str): return repr(e.value)
        return str(e.value).lower() if isinstance(e.value,bool) else str(e.value)
    if isinstance(e, Var):
        if e.name in {'open','high','low','close','volume','bid','ask','last','tick_volume'}:
            return f"ctx['{e.name}']"
        return e.name
    if isinstance(e, Member):
        return emit_lvalue(e)
    if isinstance(e, BinOp):
        op = 'and' if e.op=='and' else 'or' if e.op=='or' else e.op
        return f"({emit_value(e.left)} {op} {emit_value(e.right)})"
    if isinstance(e, UnOp):
        return f"(not {emit_value(e.expr)})" if e.op=='not' else f"(-{emit_value(e.expr)})"
    return "0"
