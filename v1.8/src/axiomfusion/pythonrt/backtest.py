from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Tuple
import math
import pandas as pd
import numpy as np

from ..compile import compile_source
from ..ir import IRModule, IRExpr, Lit, Var, Member, BinOp, UnOp, Call, Index, IRStmt, IfStmt, TradeIntent, SetStmt, ReduceStmt
from ..runtime import BacktestConfig, default_policy_chain, apply_fill
from ..policies.core import Account, MarketSnapshot, Intent

from .series import Series, ensure_series, binary_op, unary_op, shift
from . import indicators as ind
from .mtf import MTFCache, align_to_base
from .trace import TraceWriter, TraceEvent

@dataclass
class EngineConfig:
    symbol: str = "TEST"
    mode: str = "bar"   # bar | tick4
    tick_path: str = "OHL C"  # ignored for now; deterministic 4-tick path
    trace_path: Optional[str] = None
    profile: Optional[Any] = None  # ExecutionProfile
    initial_balance: float = 10_000.0

def _is_true(x: float) -> bool:
    return (not math.isnan(x)) and x != 0.0

def _lit_to_series(l: Lit, n: int, index) -> Series:
    v = float(l.value)
    return Series(name=str(v), values=np.full(n, v, dtype=float), index=index)

class Evaluator:
    def __init__(self, mod: IRModule, df: pd.DataFrame, mtf: Optional[MTFCache] = None):
        self.mod = mod
        self.df = df
        self.index = df.index
        self.n = len(df)
        self.mtf = mtf

        # base inputs
        self.env: Dict[str, Series] = {}
        for col in ["open","high","low","close","volume"]:
            if col in df.columns:
                self.env[col] = ensure_series(col, df[col].to_numpy(dtype=float), index=self.index)

        # compute bindings as series
        for b in mod.bindings:
            self.env[b.name] = self.eval_series(b.expr)

    def eval_series(self, e: IRExpr) -> Series:
        if isinstance(e, Lit):
            return _lit_to_series(e, self.n, self.index)
        if isinstance(e, Var):
            if e.name not in self.env:
                raise KeyError(f"Unknown var: {e.name}")
            return self.env[e.name]
        if isinstance(e, BinOp):
            a = self.eval_series(e.left)
            b = self.eval_series(e.right)
            return binary_op(a, b, e.op)
        if isinstance(e, UnOp):
            a = self.eval_series(e.expr)
            return unary_op(a, e.op)
        if isinstance(e, Index):
            base = self.eval_series(e.base)
            # only support constant integer indices
            if isinstance(e.index, Lit):
                k = int(e.index.value)
                return shift(base, k)
            raise ValueError("Only literal indices supported in v1.8")
        if isinstance(e, Call):
            fn = e.fn
            args = [self.eval_series(a) if not isinstance(a, Lit) else a for a in e.args]
            # normalize helper
            def as_series(x): 
                return x if isinstance(x, Series) else self.eval_series(x)  # should not happen
            def as_int(x):
                return int(x.value) if isinstance(x, Lit) else int(as_series(x).values[~np.isnan(as_series(x).values)][0])
            if fn == "sma":
                return ind.sma(as_series(args[0]), as_int(args[1]))
            if fn == "ema":
                return ind.ema(as_series(args[0]), as_int(args[1]))
            if fn == "highest":
                return ind.highest(as_series(args[0]), as_int(args[1]))
            if fn == "lowest":
                return ind.lowest(as_series(args[0]), as_int(args[1]))
            if fn == "stddev":
                return ind.stddev(as_series(args[0]), as_int(args[1]))
            if fn == "roc":
                return ind.roc(as_series(args[0]), as_int(args[1]))
            if fn == "macd_hist":
                return ind.macd_hist(as_series(args[0]), as_int(args[1]), as_int(args[2]), as_int(args[3]))
            if fn == "series_from":
                # series_from(symbol, timeframe, field)
                if self.mtf is None:
                    raise ValueError("series_from requires MTFCache")
                sym = args[0].value if isinstance(args[0], Lit) else None
                tf = args[1].value if isinstance(args[1], Lit) else None
                field = args[2].value if isinstance(args[2], Lit) else None
                if sym is None or tf is None or field is None:
                    raise ValueError("series_from requires literal symbol, timeframe, field in v1.8")
                hdf = self.mtf.get(str(tf))
                aligned = align_to_base(self.df.index, hdf[str(field)])
                return ensure_series(f"{sym}:{tf}:{field}", aligned.to_numpy(dtype=float), index=self.index)
            raise ValueError(f"Unknown call: {fn}")
        raise TypeError(f"Unsupported expr: {type(e)}")

    def scalar(self, series_name: str, t: int) -> float:
        return self.env[series_name].at(t)

def run_backtest_from_source(src: str, df: pd.DataFrame, *, cfg: Optional[EngineConfig] = None) -> Dict[str, Any]:
    cfg = cfg or EngineConfig()
    comp = compile_source(src)
    mod = comp.ir_module if hasattr(comp, "ir_module") else None
    # v1.x compile_source returns CompileResult with .ir (IRModule)
    mod = getattr(comp, "ir", None) if mod is None else mod
    if mod is None:
        raise ValueError("Compile did not produce IR module")

    mtf = MTFCache(df, {}) if ("mtf" in getattr(comp, "capabilities", set()) or "series_from" in src.lower()) else None
    ev = Evaluator(mod, df, mtf=mtf)

    # policy chain via execution profile if provided
    if cfg.profile is not None:
        # map profile to BacktestConfig
        btc = BacktestConfig(
            symbol=cfg.symbol,
            spread=float(cfg.profile.costs.spread_points or 0.0),
            slippage=float(cfg.profile.costs.slippage_points_mean or 0.0),
            commission_per_lot=float(cfg.profile.costs.commission_per_lot_roundturn or 0.0),
            leverage=100.0,
            contract_size=100_000.0,
            min_stop=float(cfg.profile.broker.stops_level_points or 0.0),
        )
    else:
        btc = BacktestConfig(symbol=cfg.symbol)

    chain = default_policy_chain(btc)
    acct = Account(balance=cfg.initial_balance, equity=cfg.initial_balance, positions=[])

    tw = TraceWriter(cfg.trace_path) if cfg.trace_path else None

    def emit_trace(t: int, kind: str, data: Dict[str, Any]):
        if tw is None:
            return
        ts = str(df.index[t]) if hasattr(df.index, "__len__") else str(t)
        tw.write(TraceEvent(t=t, time=ts, kind=kind, data=data))

    equity_curve = []
    for t in range(len(df)):
        # deterministic tick4 mode: simulate 4 snapshots in fixed order; intents only on bar close by default
        row = df.iloc[t]
        # market snapshot at close
        mkt = MarketSnapshot(symbol=cfg.symbol, bid=float(row["close"]), ask=float(row["close"]), last=float(row["close"]), time=str(df.index[t]))
        intents: List[Intent] = []

        # execute handlers
        for h in mod.handlers:
            if h.kind != "bar":
                continue
            for st in h.stmts:
                _exec_stmt(st, t, ev, intents)

        # apply policy chain
        for intent in intents:
            res = chain.evaluate(acct, intent, mkt)
            emit_trace(t, "intent", {"intent": intent.__dict__, "accepted": res.accepted, "reason": res.reason, "fill_price": res.fill_price})
            apply_fill(acct, intent, res, mkt)

        # update equity naive mark-to-close
        acct.equity = acct.balance
        for p in acct.positions:
            px = mkt.bid if p.side == "long" else mkt.ask
            # unrealized PnL in quote per unit; ignore contract conversions
            pnl = (px - p.entry) * (1 if p.side == "long" else -1) * p.qty
            acct.equity += pnl
        equity_curve.append(acct.equity)
        emit_trace(t, "bar", {"equity": acct.equity, "positions": [p.__dict__ for p in acct.positions]})

    if tw: tw.close()
    return {"equity": equity_curve, "final": {"balance": acct.balance, "equity": acct.equity, "positions": [p.__dict__ for p in acct.positions]}}

def _exec_stmt(st: IRStmt, t: int, ev: Evaluator, intents: List[Intent]):
    from ..policies.core import Intent as PIntent
    if isinstance(st, IfStmt):
        cond = _eval_cond(st.cond, t, ev)
        if cond:
            for s in st.then_body:
                _exec_stmt(s, t, ev, intents)
        else:
            for s in st.else_body:
                _exec_stmt(s, t, ev, intents)
        return
    if isinstance(st, TradeIntent):
        kind = st.kind
        qty = _eval_scalar_expr(st.qty, t, ev)
        tag = st.tag or ""
        sym = st.symbol or "TEST"
        intents.append(PIntent(kind=kind, symbol=sym, qty=qty, tag=tag,
                               sl=_eval_scalar_expr(st.sl, t, ev) if st.sl else None,
                               tp=_eval_scalar_expr(st.tp, t, ev) if st.tp else None))
        return
    # state/reduce ignored in v1.8 (hooks exist; full persistence later)
    return

def _eval_scalar_expr(e, t: int, ev: Evaluator) -> float:
    if e is None:
        return float("nan")
    if isinstance(e, Lit):
        return float(e.value)
    if isinstance(e, Var):
        return ev.env[e.name].at(t)
    # fallback: compute series then at(t)
    s = ev.eval_series(e)
    return s.at(t)

def _eval_cond(e, t: int, ev: Evaluator) -> bool:
    v = _eval_scalar_expr(e, t, ev)
    return _is_true(v)
