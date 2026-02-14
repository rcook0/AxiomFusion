from __future__ import annotations
from dataclasses import dataclass
from typing import Set, Optional, Dict, Any
import re

@dataclass(frozen=True)
class RequiredSemantics:
    needs_tick: bool = False
    needs_mtf: bool = False
    needs_history_index: bool = False
    needs_state: bool = False
    # For now we assume bar_close intent; later upgrades derive more precisely.
    mtf_alignment: str = "bar_close"  # bar_close | any

def infer_required_semantics(src: str) -> RequiredSemantics:
    s = src.lower()

    needs_tick = bool(re.search(r"\bon\s+tick\b", s)) or bool(re.search(r"\bon\s+each\s+tick\b", s))
    # MTF patterns
    needs_mtf = ("series_from(" in s) or ("timeframe" in s) or bool(re.search(r"\brequest\.security\b", s))
    # History indexing patterns (future): x[-1] in E or core
    needs_history = bool(re.search(r"\[[\-]?\d+\]", src))  # crude: any bracket index
    # State usage
    needs_state = bool(re.search(r"\bstate\b", s)) or bool(re.search(r"\bkeep\s+state\b", s)) or (".value" in s and "reduce" in s)

    return RequiredSemantics(
        needs_tick=needs_tick,
        needs_mtf=needs_mtf,
        needs_history_index=needs_history,
        needs_state=needs_state,
        mtf_alignment="bar_close" if needs_mtf else "bar_close",
    )

# Error codes
E_TICK_UNSUPPORTED = "ESEM001"
E_MTF_UNSUPPORTED  = "ESEM002"
E_ALIGN_UNSUPPORTED= "ESEM003"
E_HIST_UNSUPPORTED = "ESEM004"
E_STATE_UNSUPPORTED= "ESEM005"

def validate_semantics(req: RequiredSemantics, target_sem: Dict[str, Any]) -> list[tuple[str,str]]:
    errs: list[tuple[str,str]] = []
    if req.needs_tick and not bool(target_sem.get("supports_tick", False)):
        errs.append((E_TICK_UNSUPPORTED, "Target does not support tick-level execution, but source requires it."))
    if req.needs_mtf and not bool(target_sem.get("supports_mtf", False)):
        errs.append((E_MTF_UNSUPPORTED, "Target does not support multi-timeframe/multi-symbol series, but source requires it."))
    if req.needs_mtf:
        align = str(target_sem.get("mtf_alignment", "bar_close"))
        if req.mtf_alignment == "bar_close" and align not in ("bar_close","any"):
            errs.append((E_ALIGN_UNSUPPORTED, f"Target MTF alignment '{align}' incompatible with required '{req.mtf_alignment}'."))
    if req.needs_history_index and not bool(target_sem.get("supports_history_index", False)):
        errs.append((E_HIST_UNSUPPORTED, "Target does not support history indexing, but source uses indexed series."))
    # State: currently all targets allow some state; keep hook for future strict targets
    if req.needs_state and str(target_sem.get("state_persistence","bar")) == "none":
        errs.append((E_STATE_UNSUPPORTED, "Target does not support persistent state, but source declares/updates state."))
    return errs
