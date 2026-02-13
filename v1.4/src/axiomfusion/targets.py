from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Dict, Set, Optional, Any

@dataclass(frozen=True)
class Target:
    name: str
    emitter: str  # 'pine'|'mql5'|'python_rt'
    mode: str     # emitter-specific (e.g. indicator|strategy)
    allow_caps: Set[str] = field(default_factory=set)
    options: Dict[str, Any] = field(default_factory=dict)

TARGETS: Dict[str, Target] = {
    "pine.indicator": Target("pine.indicator", "pine", "indicator", allow_caps={"state","mtf"}, options={"force_indicator": True}),
    "pine.strategy":  Target("pine.strategy",  "pine", "strategy",  allow_caps={"trade","state","mtf"}, options={"force_strategy": True}),
    "mql5.ea":        Target("mql5.ea",        "mql5", "ea",        allow_caps={"trade","tick","state","mtf"}, options={}),
    "python.backtest":Target("python.backtest","python_rt","backtest",allow_caps={"trade","tick","state","mtf"}, options={}),
}

def get_target(name: str) -> Target:
    if name not in TARGETS:
        raise KeyError(f"Unknown target '{name}'. Known: {sorted(TARGETS.keys())}")
    return TARGETS[name]
