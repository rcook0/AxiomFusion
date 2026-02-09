from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Optional

import pandas as pd

from .policies.core import Intent, MarketSnapshot, Account, Position, ExecutionPolicyChain
from .policies.builtins import SpreadModelPolicy, SlippagePolicy, CommissionPolicy, MarginPolicy, StopsLevelPolicy, FillPolicyMarket
from .sandbox import Sandbox, SandboxConfig, CapabilityGate

@dataclass
class BacktestConfig:
    symbol: str = "TEST"
    spread: float = 0.0
    slippage: float = 0.0
    commission_per_lot: float = 0.0
    leverage: float = 100.0
    contract_size: float = 100_000.0
    min_stop: float = 0.0

def default_policy_chain(cfg: BacktestConfig) -> ExecutionPolicyChain:
    slip = SlippagePolicy(cfg.slippage) if cfg.slippage else None
    comm = CommissionPolicy(cfg.commission_per_lot) if cfg.commission_per_lot else None
    policies = [
        SpreadModelPolicy(cfg.spread),
        MarginPolicy(contract_size=cfg.contract_size),
        StopsLevelPolicy(cfg.min_stop),
        FillPolicyMarket(slippage=slip, commission=comm),
    ]
    return ExecutionPolicyChain(policies)

def apply_fill(acct: Account, intent: Intent, res, mkt: MarketSnapshot):
    if not res.accepted:
        return
    if intent.kind == "enter_long":
        acct.positions.append(Position(intent.symbol, "long", intent.qty, res.fill_price or mkt.ask, intent.tag))
    elif intent.kind == "enter_short":
        acct.positions.append(Position(intent.symbol, "short", intent.qty, res.fill_price or mkt.bid, intent.tag))
    elif intent.kind == "exit":
        acct.positions = [p for p in acct.positions if p.tag != intent.tag]
    acct.balance -= res.commission
    acct.equity = acct.balance
    acct.free_margin = acct.equity  # simplified

def run_backtest(df: pd.DataFrame, strategy_run_fn, cfg: Optional[BacktestConfig]=None, *, sandbox_cfg: Optional[SandboxConfig]=None):
    cfg = cfg or BacktestConfig()
    acct = Account(balance=10_000.0, equity=10_000.0, free_margin=10_000.0, leverage=cfg.leverage)
    chain = default_policy_chain(cfg)
    state = {}
    intents_out = []
    sandbox = Sandbox(sandbox_cfg or SandboxConfig())
    fills_out = []

    # strategy_run_fn should accept (row_ctx, state) and return list[intent_dict]
    for t in range(len(df)):
        row = df.iloc[t]
        tm = row.name if isinstance(row.name, datetime) else datetime.utcnow()
        mid = float(row.get("close", row.get("mid", 0.0)))
        mkt = MarketSnapshot(cfg.symbol, tm, mid, mid, mid, 0.0)
        sandbox.on_new_bar(tm)
        ctx = {
            "open": float(row.get("open", mid)),
            "high": float(row.get("high", mid)),
            "low": float(row.get("low", mid)),
            "close": float(row.get("close", mid)),
            "volume": float(row.get("volume", 0.0)),
            "bid": mkt.bid,
            "ask": mkt.ask,
            "last": mkt.mid,
            "tick_volume": float(row.get("volume", 0.0)),
        }
        intents = strategy_run_fn(ctx, state) or []
        for idict in intents:
            intent = Intent(**idict)
            intent.symbol = cfg.symbol
            intents_out.append((t, intent))
            reason = sandbox.vet_intent(intent, acct)
            if reason:
                res = type('R', (), {})()  # lightweight
                res.accepted=False; res.reason=reason; res.fill_price=None; res.filled_qty=0.0; res.commission=0.0; res.slippage=0.0; res.spread=mkt.spread
            else:
                sandbox.record_intent()
                res = chain.execute(intent, mkt, acct)
            fills_out.append((t, intent, res))
            apply_fill(acct, intent, res, mkt)
    return {"account": acct, "intents": intents_out, "fills": fills_out, "state": state}


def check_capabilities(required: set[str], allowed: set[str] | None = None, strict: bool = True) -> None:
    gate = CapabilityGate(allowed=allowed or {"trade","tick","state","mtf"}, strict=strict)
    gate.check(required)
