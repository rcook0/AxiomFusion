from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol, Any
from datetime import datetime

@dataclass
class Intent:
    kind: str              # enter_long|enter_short|exit
    symbol: str
    qty: float
    sl_points: Optional[float] = None
    tp_points: Optional[float] = None
    tag: str = "AF"

@dataclass
class MarketSnapshot:
    symbol: str
    time: datetime
    mid: float
    bid: float
    ask: float
    spread: float

@dataclass
class Position:
    symbol: str
    side: str      # long|short
    qty: float
    entry_price: float
    tag: str

@dataclass
class Account:
    balance: float = 10_000.0
    equity: float = 10_000.0
    free_margin: float = 10_000.0
    leverage: float = 100.0
    positions: List[Position] = field(default_factory=list)

@dataclass
class ExecutionResult:
    accepted: bool
    reason: str = ""
    fill_price: Optional[float] = None
    filled_qty: float = 0.0
    commission: float = 0.0
    slippage: float = 0.0
    spread: float = 0.0

class ExecutionPolicy(Protocol):
    def before(self, intent: Intent, mkt: MarketSnapshot, acct: Account) -> Intent:
        ...
    def decide(self, intent: Intent, mkt: MarketSnapshot, acct: Account) -> ExecutionResult:
        ...

class ExecutionPolicyChain:
    def __init__(self, policies: List[ExecutionPolicy]):
        self.policies = policies

    def execute(self, intent: Intent, mkt: MarketSnapshot, acct: Account) -> ExecutionResult:
        cur = intent
        for p in self.policies:
            cur = p.before(cur, mkt, acct)
        # final decide uses last policy in chain that implements decide; default is accept
        res: Optional[ExecutionResult] = None
        for p in reversed(self.policies):
            r = p.decide(cur, mkt, acct)
            if r is not None:
                res = r
                break
        if res is None:
            res = ExecutionResult(True, fill_price=mkt.ask if cur.kind=="enter_long" else mkt.bid, filled_qty=cur.qty)
        return res
