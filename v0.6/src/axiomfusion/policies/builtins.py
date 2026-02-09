from __future__ import annotations
from dataclasses import dataclass
from datetime import time
from typing import Optional, Tuple, List
from .core import Intent, MarketSnapshot, Account, ExecutionResult, ExecutionPolicy

@dataclass
class SessionFilterPolicy:
    # list of allowed windows (local time) as (start, end) inclusive-exclusive
    windows: List[Tuple[time, time]]

    def before(self, intent: Intent, mkt: MarketSnapshot, acct: Account) -> Intent:
        return intent

    def decide(self, intent: Intent, mkt: MarketSnapshot, acct: Account) -> ExecutionResult:
        t = mkt.time.time()
        ok = any(w0 <= t < w1 for (w0,w1) in self.windows)
        if not ok:
            return ExecutionResult(False, reason="session_filter")
        return None  # allow next policy to decide

@dataclass
class SpreadModelPolicy:
    # spread in price units (not points); simplest fixed spread
    spread: float

    def before(self, intent: Intent, mkt: MarketSnapshot, acct: Account) -> Intent:
        # update bid/ask logically from mid
        half = self.spread/2.0
        mkt.bid = mkt.mid - half
        mkt.ask = mkt.mid + half
        mkt.spread = self.spread
        return intent

    def decide(self, intent: Intent, mkt: MarketSnapshot, acct: Account) -> ExecutionResult:
        return None

@dataclass
class SlippagePolicy:
    # slippage in price units; applied in direction of the trade
    slip: float

    def before(self, intent: Intent, mkt: MarketSnapshot, acct: Account) -> Intent:
        return intent

    def decide(self, intent: Intent, mkt: MarketSnapshot, acct: Account) -> ExecutionResult:
        return None

    def apply(self, intent: Intent, px: float) -> Tuple[float, float]:
        if intent.kind == "enter_long":
            return px + self.slip, self.slip
        if intent.kind == "enter_short":
            return px - self.slip, self.slip
        return px, 0.0

@dataclass
class CommissionPolicy:
    # commission per lot per side
    per_lot: float

    def before(self, intent: Intent, mkt: MarketSnapshot, acct: Account) -> Intent:
        return intent

    def decide(self, intent: Intent, mkt: MarketSnapshot, acct: Account) -> ExecutionResult:
        return None

    def commission(self, intent: Intent) -> float:
        return abs(intent.qty) * self.per_lot

@dataclass
class MarginPolicy:
    contract_size: float = 100_000.0  # FX standard; adjust per symbol
    def before(self, intent: Intent, mkt: MarketSnapshot, acct: Account) -> Intent:
        return intent
    def decide(self, intent: Intent, mkt: MarketSnapshot, acct: Account) -> ExecutionResult:
        if intent.kind.startswith("enter"):
            notional = abs(intent.qty) * self.contract_size * mkt.mid
            margin_req = notional / acct.leverage
            if acct.free_margin < margin_req:
                return ExecutionResult(False, reason="insufficient_margin")
        return None

@dataclass
class StopsLevelPolicy:
    min_distance: float  # in price units
    def before(self, intent: Intent, mkt: MarketSnapshot, acct: Account) -> Intent:
        return intent
    def decide(self, intent: Intent, mkt: MarketSnapshot, acct: Account) -> ExecutionResult:
        if intent.kind.startswith("enter") and intent.sl_points is not None:
            # interpret sl_points as price units for now
            if intent.sl_points < self.min_distance:
                return ExecutionResult(False, reason="stops_level")
        return None

@dataclass
class FillPolicyMarket:
    slippage: Optional[SlippagePolicy] = None
    commission: Optional[CommissionPolicy] = None

    def before(self, intent: Intent, mkt: MarketSnapshot, acct: Account) -> Intent:
        return intent

    def decide(self, intent: Intent, mkt: MarketSnapshot, acct: Account) -> ExecutionResult:
        if intent.kind == "exit":
            # accept exit, no fill price modeling here
            return ExecutionResult(True, reason="exit_accepted")
        if intent.kind == "enter_long":
            base_px = mkt.ask
        elif intent.kind == "enter_short":
            base_px = mkt.bid
        else:
            return ExecutionResult(False, reason="unknown_intent")
        fill_px, slip = (base_px, 0.0)
        if self.slippage:
            fill_px, slip = self.slippage.apply(intent, base_px)
        comm = self.commission.commission(intent) if self.commission else 0.0
        return ExecutionResult(True, fill_price=fill_px, filled_qty=intent.qty, commission=comm, slippage=slip, spread=mkt.spread)
