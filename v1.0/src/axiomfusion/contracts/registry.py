from __future__ import annotations
import json
from pathlib import Path
from typing import Dict
from .model import TargetContract, Semantics

def load_contracts() -> Dict[str, TargetContract]:
    path = Path(__file__).with_name("targets.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    out: Dict[str, TargetContract] = {}
    for t in data["targets"]:
        sem = t.get("semantics", {})
        tc = TargetContract(
            name=t["name"],
            allow_caps=set(t["allow_caps"]),
            hard_deny_caps=set(t.get("hard_deny_caps", [])),
            semantics=Semantics(**{**Semantics().__dict__, **sem}),
            emitter=t.get("emitter",""),
            mode=t.get("mode",""),
            must_contain=list(t.get("must_contain", [])),
            must_not_contain=list(t.get("must_not_contain", [])),
        )
        out[tc.name] = tc
    return out

_CONTRACTS = None

def get_contract(name: str) -> TargetContract:
    global _CONTRACTS
    if _CONTRACTS is None:
        _CONTRACTS = load_contracts()
    if name not in _CONTRACTS:
        raise KeyError(f"Unknown contract '{name}'. Known: {sorted(_CONTRACTS.keys())}")
    return _CONTRACTS[name]
