\
from __future__ import annotations
from typing import List, Dict, Tuple
from ..ir import (
    IRModule, IRExpr, Lit, Var, Member, BinOp, UnOp, Call, Index,
    IRStmt, IfStmt, TradeIntent, SetStmt, ReduceStmt
)

def emit(mod: IRModule) -> str:
    lines: List[str] = []
    lines.append("// AxiomFusion v1.7 - MQL5 EA (robust order plumbing, tags->magic, volume normalize, trace)")
    lines.append("#property strict")
    lines.append("#include <Trade/Trade.mqh>")
    lines.append("CTrade trade;")
    lines.append("")
    lines.append("// ---- Inputs / policies ----")
    lines.append("input int    AF_SlippagePoints = 20;")
    lines.append("input int    AF_Retries        = 3;")
    lines.append("input int    AF_RetryDelayMs   = 250;")
    lines.append("input int    AF_MaxSpreadPoints= 0;   // 0 disables")
    lines.append("input bool   AF_Trace          = false;")
    lines.append('input string AF_TraceFile      = "axiomfusion_trace.csv";')
    lines.append("")

    # user-defined inputs
    for inp in mod.inputs:
        lines.append(f"input {map_type(inp.typ)} {inp.name} = {emit_expr(inp.expr)};")
    lines.append("")

    # state
    if mod.states:
        lines.append("// ---- Persistent state (in-memory) ----")
        for st in mod.states:
            lines.append(f"// state {st.name} v{st.version}")
            for f in st.fields:
                lines.append(f"{map_scalar_type(f.typ)} {st.name}_{f.name} = {emit_expr(f.init)};")
        lines.append("")

    lines.append("// ---- Time / bar detection ----")
    lines.append("datetime __lastBarTime = 0;")
    lines.append("bool IsNewBar(){ datetime t=iTime(_Symbol,_Period,0); if(t==0) return false; if(t!=__lastBarTime){__lastBarTime=t; return true;} return false; }")
    lines.append("")

    # trace
    lines.append("// ---- Trace (best-effort) ----")
    lines.append("int __traceH = INVALID_HANDLE;")
    lines.append("void TraceOpen(){ if(!AF_Trace) return; if(__traceH!=INVALID_HANDLE) return; __traceH = FileOpen(AF_TraceFile, FILE_WRITE|FILE_CSV|FILE_COMMON); if(__traceH!=INVALID_HANDLE){ FileWrite(__traceH, \"ts\",\"symbol\",\"evt\",\"tag\",\"kind\",\"price\",\"qty\",\"note\"); } }")
    lines.append("void TraceClose(){ if(__traceH==INVALID_HANDLE) return; FileClose(__traceH); __traceH=INVALID_HANDLE; }")
    lines.append("void Trace(string evt, string tag, string kind, double price, double qty, string note){ if(!AF_Trace) return; TraceOpen(); if(__traceH==INVALID_HANDLE) return; FileWrite(__traceH, TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS), _Symbol, evt, tag, kind, DoubleToString(price,_Digits), DoubleToString(qty,2), note); }")
    lines.append("")

    # helpers: hashing tag -> magic
    lines.append("// ---- Tag/Magic helpers ----")
    lines.append("uint AF_Fnv1a(string s){ uint h=2166136261; for(int i=0;i<StringLen(s);i++){ h ^= (uchar)StringGetCharacter(s,i); h *= 16777619; } return h; }")
    lines.append("int AF_Magic(string tag){ return (int)(AF_Fnv1a(tag) & 0x7fffffff); }")
    lines.append("string AF_Comment(string tag){ return \"AF:\"+tag; }")
    lines.append("")

    # helpers: broker constraints + spread
    lines.append("// ---- Broker constraints ----")
    lines.append("double AF_Point(){ return SymbolInfoDouble(_Symbol, SYMBOL_POINT); }")
    lines.append("int AF_StopsLevelPoints(){ return (int)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL); }")
    lines.append("int AF_FreezeLevelPoints(){ return (int)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_FREEZE_LEVEL); }")
    lines.append("double AF_SpreadPoints(){ return (SymbolInfoDouble(_Symbol,SYMBOL_ASK)-SymbolInfoDouble(_Symbol,SYMBOL_BID)) / AF_Point(); }")
    lines.append("bool AF_SpreadOk(){ if(AF_MaxSpreadPoints<=0) return true; return AF_SpreadPoints() <= AF_MaxSpreadPoints; }")
    lines.append("")
    lines.append("double AF_VolMin(){ return SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN); }")
    lines.append("double AF_VolMax(){ return SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX); }")
    lines.append("double AF_VolStep(){ return SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP); }")
    lines.append("double AF_NormalizeLots(double lots){ double mn=AF_VolMin(), mx=AF_VolMax(), st=AF_VolStep(); if(st<=0) st=0.01; if(lots<mn) lots=mn; if(lots>mx) lots=mx; double k = MathFloor(lots/st + 0.5); double v = k*st; v = MathMax(mn, MathMin(mx, v)); return v; }")
    lines.append("")

    # helpers: position lookup by tag
    lines.append("// ---- Position lookup by tag ----")
    lines.append("bool AF_FindPosition(string sym, string tag, ulong &ticket, long &type){")
    lines.append("  int magic = AF_Magic(tag);")
    lines.append("  string cmt = AF_Comment(tag);")
    lines.append("  int n = PositionsTotal();")
    lines.append("  for(int i=0;i<n;i++){")
    lines.append("    ulong t = PositionGetTicket(i);")
    lines.append("    if(!PositionSelectByTicket(t)) continue;")
    lines.append("    if(PositionGetString(POSITION_SYMBOL)!=sym) continue;")
    lines.append("    if((int)PositionGetInteger(POSITION_MAGIC)!=magic) continue;")
    lines.append("    string pc = PositionGetString(POSITION_COMMENT);")
    lines.append("    if(pc!=cmt) continue;")
    lines.append("    ticket=t; type=PositionGetInteger(POSITION_TYPE); return true;")
    lines.append("  }")
    lines.append("  return false;")
    lines.append("}")
    lines.append("")

    # helpers: close by ticket with retries
    lines.append("bool AF_CloseTicket(ulong ticket, string tag){")
    lines.append("  for(int k=0;k<AF_Retries;k++){")
    lines.append("    if(!AF_SpreadOk()){ Trace(\"reject\",tag,\"close\",0,0,\"spread\"); return false; }")
    lines.append("    trade.SetDeviationInPoints(AF_SlippagePoints);")
    lines.append("    bool ok = trade.PositionClose(ticket);")
    lines.append("    if(ok){ Trace(\"ok\",tag,\"close\",0,0,\"closed\"); return true; }")
    lines.append("    int err = GetLastError();")
    lines.append("    Trace(\"retry\",tag,\"close\",0,0,\"err=\"+IntegerToString(err));")
    lines.append("    ResetLastError();")
    lines.append("    Sleep(AF_RetryDelayMs);")
    lines.append("  }")
    lines.append("  Trace(\"fail\",tag,\"close\",0,0,\"retries_exhausted\");")
    lines.append("  return false;")
    lines.append("}")
    lines.append("")

    # helpers: open long/short with sl/tp points
    lines.append("bool AF_Open(bool isLong, double lots, int sl_pts, int tp_pts, string tag){")
    lines.append("  if(!AF_SpreadOk()){ Trace(\"reject\",tag,\"open\",0,lots,\"spread\"); return false; }")
    lines.append("  lots = AF_NormalizeLots(lots);")
    lines.append("  int magic = AF_Magic(tag);")
    lines.append("  trade.SetExpertMagicNumber(magic);")
    lines.append("  trade.SetDeviationInPoints(AF_SlippagePoints);")
    lines.append("  double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);")
    lines.append("  double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);")
    lines.append("  double price = isLong ? ask : bid;")
    lines.append("  double pt = AF_Point();")
    lines.append("  double sl=0, tp=0;")
    lines.append("  if(sl_pts>0){ sl = isLong ? price - sl_pts*pt : price + sl_pts*pt; }")
    lines.append("  if(tp_pts>0){ tp = isLong ? price + tp_pts*pt : price - tp_pts*pt; }")
    lines.append("  int stops = AF_StopsLevelPoints();")
    lines.append("  if(stops>0 && sl_pts>0 && sl_pts<stops){ Trace(\"reject\",tag,\"open\",price,lots,\"sl<stops\"); return false; }")
    lines.append("  if(stops>0 && tp_pts>0 && tp_pts<stops){ Trace(\"reject\",tag,\"open\",price,lots,\"tp<stops\"); return false; }")
    lines.append("  string cmt = AF_Comment(tag);")
    lines.append("  for(int k=0;k<AF_Retries;k++){")
    lines.append("    bool ok = isLong ? trade.Buy(lots, _Symbol, price, sl, tp, cmt) : trade.Sell(lots, _Symbol, price, sl, tp, cmt);")
    lines.append("    if(ok){ Trace(\"ok\",tag,isLong?\"buy\":\"sell\",price,lots,\"opened\"); return true; }")
    lines.append("    int err = GetLastError();")
    lines.append("    Trace(\"retry\",tag,isLong?\"buy\":\"sell\",price,lots,\"err=\"+IntegerToString(err));")
    lines.append("    ResetLastError();")
    lines.append("    Sleep(AF_RetryDelayMs);")
    lines.append("  }")
    lines.append("  Trace(\"fail\",tag,isLong?\"buy\":\"sell\",price,lots,\"retries_exhausted\");")
    lines.append("  return false;")
    lines.append("}")
    lines.append("")

    # reducers reset
    if mod.states:
        lines.append("void __ResetReducers(){")
        for st in mod.states:
            for f in st.fields:
                lines.append(f"  {st.name}_{f.name} = {emit_expr(f.init)};")
        lines.append("}")
        lines.append("")

    # init/deinit
    lines.append("int OnInit(){")
    lines.append("  TraceOpen();")
    if mod.states:
        lines.append("  __ResetReducers();")
    lines.append("  return(INIT_SUCCEEDED);")
    lines.append("}")
    lines.append("void OnDeinit(const int reason){ TraceClose(); }")
    lines.append("")

    # OnTick body
    lines.append("void OnTick(){")
    lines.append("  bool newBar = IsNewBar();")
    lines.append("")

    for b in mod.bindings:
        lines.append(f"  // {b.kind} {b.name}")
        lines.append(f"  auto {b.name} = {emit_expr(b.expr)};")
    lines.append("")

    # tick handlers
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
    return "\n".join(lines) + "\n"

# ---- Statements ----
def emit_stmt(st: IRStmt, indent: str) -> List[str]:
    if isinstance(st, IfStmt):
        out = [f"{indent}if({emit_expr(st.cond)}){{"]
        for s in st.block:
            out.extend(emit_stmt(s, indent + "  "))
        out.append(f"{indent}}}")
        return out
    if isinstance(st, SetStmt):
        # state field set
        return [f"{indent}{st.target.obj.name}_{st.target.field} = {emit_expr(st.expr)};"]
    if isinstance(st, ReduceStmt):
        tgt = f"{st.target.obj.name}_{st.target.field}"
        rhs = emit_expr(st.expr)
        if st.op == "max":
            return [f"{indent}{tgt} = MathMax({tgt}, {rhs});"]
        if st.op == "min":
            return [f"{indent}{tgt} = MathMin({tgt}, {rhs});"]
        return [f"{indent}// unsupported reducer op {st.op}"]
    if isinstance(st, TradeIntent):
        return emit_trade_intent(st, indent)
    return [f"{indent}// (unhandled stmt)"]

def emit_trade_intent(t: TradeIntent, indent: str) -> List[str]:
    k = t.kind
    # expected kwargs: qty, sl_points, tp_points, tag
    tag = emit_expr(t.kwargs.get("tag", Lit("AF")))
    qty = emit_expr(t.kwargs.get("qty", Lit(0.01)))
    slp = emit_expr(t.kwargs.get("sl_points", Lit(0)))
    tpp = emit_expr(t.kwargs.get("tp_points", Lit(0)))

    out: List[str] = []
    if k in ("enter_long","enter_short"):
        is_long = "true" if k == "enter_long" else "false"
        # netting/hedging best-effort: close opposite position of same tag, then open
        out.append(f"{indent}{{")
        out.append(f"{indent}  ulong ticket; long ptype;")
        out.append(f"{indent}  if(AF_FindPosition(_Symbol, {tag}, ticket, ptype)){{")
        out.append(f"{indent}    bool wantLong = {is_long};")
        out.append(f"{indent}    bool haveLong = (ptype==POSITION_TYPE_BUY);")
        out.append(f"{indent}    if(wantLong!=haveLong) AF_CloseTicket(ticket, {tag});")
        out.append(f"{indent}  }}")
        out.append(f"{indent}  AF_Open({is_long}, {qty}, (int){slp}, (int){tpp}, {tag});")
        out.append(f"{indent}}}")
        return out

    if k == "exit":
        out.append(f"{indent}{{ ulong ticket; long ptype; if(AF_FindPosition(_Symbol, {tag}, ticket, ptype)) AF_CloseTicket(ticket, {tag}); }}")
        return out

    return [f"{indent}// unsupported trade intent {k}"]

# ---- Expr ----
def emit_expr(e: IRExpr) -> str:
    if isinstance(e, Lit):
        if isinstance(e.value, str):
            return '"' + e.value.replace('"', '\\"') + '"'
        if e.value is True: return "true"
        if e.value is False: return "false"
        if e.value is None: return "0"
        return str(e.value)
    if isinstance(e, Var):
        # price vars
        if e.name in ("bid","ask","close","open","high","low"):
            return {
                "bid":"SymbolInfoDouble(_Symbol,SYMBOL_BID)",
                "ask":"SymbolInfoDouble(_Symbol,SYMBOL_ASK)",
                "close":"iClose(_Symbol,_Period,1)",
                "open":"iOpen(_Symbol,_Period,1)",
                "high":"iHigh(_Symbol,_Period,1)",
                "low":"iLow(_Symbol,_Period,1)",
            }[e.name]
        return e.name
    if isinstance(e, Member):
        # state field read
        if isinstance(e.obj, Var):
            return f"{e.obj.name}_{e.field}"
        return f"{emit_expr(e.obj)}.{e.field}"
    if isinstance(e, BinOp):
        return f"({emit_expr(e.left)} {e.op} {emit_expr(e.right)})"
    if isinstance(e, UnOp):
        op = "!" if e.op == "not" else e.op
        return f"({op}{emit_expr(e.expr)})"
    if isinstance(e, Index):
        # history indexing: x[-1] not supported here; treat as x
        return emit_expr(e.base)
    if isinstance(e, Call):
        return emit_call(e.name, e.args)
    return "0"

def emit_call(name: str, args: List[Tuple[str|None, IRExpr]]) -> str:
    # unwrap positional args
    pos = [a for (k,a) in args if k is None]
    if name in ("ema","sma","wma"):
        # simple MA on close/bid/ask; v1.7 keeps it minimal; true indicator handles can come in later upgrades
        src = emit_expr(pos[0]) if len(pos)>0 else "iClose(_Symbol,_Period,1)"
        n = emit_expr(pos[1]) if len(pos)>1 else "14"
        if name=="ema":
            return f"iMA(_Symbol,_Period,(int){n},0,MODE_EMA,PRICE_CLOSE,1)"
        if name=="sma":
            return f"iMA(_Symbol,_Period,(int){n},0,MODE_SMA,PRICE_CLOSE,1)"
        return f"iMA(_Symbol,_Period,(int){n},0,MODE_LWMA,PRICE_CLOSE,1)"
    if name == "cross_over":
        a = emit_expr(pos[0]); b = emit_expr(pos[1])
        # approximate: current vs previous close-bar values
        return f"(({a}) > ({b}) && ({a})/*prev*/ <= ({b})/*prev*/)"
    if name == "cross_under":
        a = emit_expr(pos[0]); b = emit_expr(pos[1])
        return f"(({a}) < ({b}) && ({a})/*prev*/ >= ({b})/*prev*/)"
    if name == "series_from":
        # args: sym, tf, field
        sym = emit_expr(pos[0]) if len(pos)>0 else "_Symbol"
        tf  = emit_expr(pos[1]) if len(pos)>1 else "_Period"
        fld = emit_expr(pos[2]) if len(pos)>2 else "\"close\""
        return emit_series_from(sym, tf, fld)
    # passthrough
    return f"{name}({', '.join(emit_expr(p) for p in pos)})"

def emit_series_from(sym: str, tf: str, fld: str) -> str:
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
    if fn == "iVolume":
        return f"{fn}({sym}, {period}, 1)"
    return f"{fn}({sym}, {period}, 1)"

def map_type(t: str) -> str:
    return {"int":"int","float":"double","bool":"bool","string":"string"}.get(t, "double")

def map_scalar_type(t: str) -> str:
    return {"int":"int","float":"double","bool":"bool","string":"string"}.get(t, "double")
