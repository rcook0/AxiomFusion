from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Set, Optional, List, Any

CAPS = {"trade","tick","state","mtf"}

@dataclass(frozen=True)
class Semantics:
    # coarse-grained semantics flags
    tick_event_loop: bool = False
    mtf_alignment: str = "bar_close"  # bar_close|unknown
    state_persistence: str = "in_memory"  # in_memory|bar_persistent|disk_persistent
    trade_model: str = "intents_only"  # intents_only|native_orders
    notes: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class TargetContract:
    name: str
    allow_caps: Set[str]
    hard_deny_caps: Set[str] = field(default_factory=set)
    semantics: Semantics = field(default_factory=Semantics)
    emitter: str = ""
    mode: str = ""
    # static conformance patterns: list of substrings that must appear in emitted code
    must_contain: List[str] = field(default_factory=list)
    must_not_contain: List[str] = field(default_factory=list)

    def supports(self, required_caps: Set[str]) -> bool:
        if required_caps & self.hard_deny_caps:
            return False
        return required_caps.issubset(self.allow_caps)

@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
