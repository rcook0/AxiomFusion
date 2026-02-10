from __future__ import annotations
from typing import Optional, Set
from .model import ValidationResult
from .registry import get_contract
from ..compiler import compile_to_target
from ..compile import compile_source

def validate_source_for_target(src: str, target_name: str, *, opt: str="O2", strict: bool=True, allow_caps: Optional[Set[str]]=None) -> ValidationResult:
    contract = get_contract(target_name)
    comp = compile_source(src)
    required = set(comp.capabilities)

    # 1) capability check (hard)
    if required & contract.hard_deny_caps:
        return ValidationResult(False, errors=[f"Target '{target_name}' hard-denies capabilities: {sorted(required & contract.hard_deny_caps)}"])
    allowed = set(allow_caps) if allow_caps is not None else set(contract.allow_caps)
    missing = sorted(required - allowed)
    if missing and strict:
        return ValidationResult(False, errors=[f"Target '{target_name}' does not allow required capabilities: {missing}"])

    # 2) compile + emitter conformance checks
    rep = compile_to_target(src, target_name, opt=opt, allow_caps=allowed, strict=False)
    code = rep.emitted
    errors = []
    for s in contract.must_contain:
        if s not in code:
            errors.append(f"Emitted code missing required marker: {s!r}")
    for s in contract.must_not_contain:
        if s in code:
            errors.append(f"Emitted code contains forbidden marker: {s!r}")
    ok = (len(errors) == 0)
    return ValidationResult(ok, errors=errors, warnings=[])

def validate_file(in_path: str, target: str, **kwargs) -> ValidationResult:
    from pathlib import Path
    src = Path(in_path).read_text(encoding="utf-8")
    return validate_source_for_target(src, target, **kwargs)
