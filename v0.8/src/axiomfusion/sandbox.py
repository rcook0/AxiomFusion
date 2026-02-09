from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Optional, Set, Dict, List, Tuple
from datetime import datetime, timedelta

from .policies.core import Intent, Account, ExecutionResult, MarketSnapshot

@dataclass
class CapabilityGate:
    allowed: Set[str] = field(default_factory=lambda: {"trade","tick","state","mtf"})
    strict: bool = True

    def check(self, required: Set[str]) -> None:
        missing = sorted(required - self.allowed)
        if missing and self.strict:
            raise PermissionError(f"Capabilities not allowed: {missing}")
        # non-strict mode: allow but could log warning elsewhere

@dataclass
class SandboxConfig:
    # intent limits
    max_intents_per_bar: int = 5
    max_open_positions: int = 5
    max_qty: float = 5.0
    allow_symbols: Optional[Set[str]] = None
    deny_intents: Set[str] = field(default_factory=set)  # e.g. {"enter_long","enter_short"}
    kill_switch: Optional[Callable[[], bool]] = None  # returns True to halt

@dataclass
class SandboxState:
    bar_intents: int = 0
    last_bar_time: Optional[datetime] = None

class Sandbox:
    def __init__(self, cfg: SandboxConfig):
        self.cfg = cfg
        self.state = SandboxState()

    def on_new_bar(self, t: datetime):
        self.state.last_bar_time = t
        self.state.bar_intents = 0

    def vet_intent(self, intent: Intent, acct: Account) -> Optional[str]:
        if self.cfg.kill_switch and self.cfg.kill_switch():
            return "kill_switch"
        if self.cfg.allow_symbols is not None and intent.symbol not in self.cfg.allow_symbols:
            return "symbol_not_allowed"
        if intent.kind in self.cfg.deny_intents:
            return "intent_denied"
        if self.state.bar_intents >= self.cfg.max_intents_per_bar:
            return "rate_limited"
        if intent.kind.startswith("enter") and len(acct.positions) >= self.cfg.max_open_positions:
            return "max_positions"
        if intent.kind.startswith("enter") and abs(intent.qty) > self.cfg.max_qty:
            return "qty_cap"
        return None

    def record_intent(self):
        self.state.bar_intents += 1
