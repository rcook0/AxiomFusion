from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Set, Dict, Any, Tuple
import json

from .e_lang import transpile_e, EHeader
from .contracts.validate import validate_source_for_target
from .compiler import compile_to_target, emit_compile_artifacts

@dataclass
class BuildOptions:
    profile: str | None = None
    profiles_dir: str | None = None

    target: Optional[str] = None
    opt: str = "O2"
    allow_caps: Optional[Set[str]] = None
    strict: bool = True
    emit_artifacts: bool = True

@dataclass
class BuildResult:
    source_kind: str
    header: Optional[Dict[str, Any]]
    axf: str
    target: str
    emitted: str
    report: Optional[Dict[str, Any]] = None
    deps_dot: Optional[str] = None
    sourcemap: Optional[Dict[str, Any]] = None

class PipelineError(Exception): ...

def read_source(path: str) -> Tuple[str, str]:
    p = Path(path)
    txt = p.read_text(encoding="utf-8")
    ext = p.suffix.lower()
    if ext == ".e":
        return "e", txt
    if ext in {".axf", ".af", ".txt"}:
        return "axf", txt
    return "axf", txt

def build_from_file(inp: str, out: str, *, artifacts_dir: Optional[str] = None, opts: Optional[BuildOptions] = None) -> BuildResult:
    kind, src = read_source(inp)
    return build_source(kind, src, out=out, artifacts_dir=artifacts_dir, opts=opts)

def build_source(kind: str, src: str, *, out: Optional[str] = None, artifacts_dir: Optional[str] = None, opts: Optional[BuildOptions] = None) -> BuildResult:
    opts = opts or BuildOptions()

    header_obj: Optional[EHeader] = None
    axf = src
    if kind == "e":
        res = transpile_e(src)
        header_obj = res.header
        axf = res.axf

    target = opts.target or (header_obj.target if header_obj else None)

    profile_name = opts.profile or (header_obj.execution_profile if header_obj else None)
    profile_obj = None
    if profile_name:
        from .profiles.registry import load_profile
        profile_obj = load_profile(profile_name, profiles_dir=opts.profiles_dir)

    if not target:
        raise PipelineError("No target specified. Provide --target or 'Target is ...' header in .e source.")

    v = validate_source_for_target(axf, target, opt=opts.opt, strict=opts.strict, allow_caps=opts.allow_caps)
    if not v.ok:
        raise PipelineError("Contract validation failed:\n" + "\n".join(" - "+e for e in v.errors))

    if opts.emit_artifacts:
        emitted, report, deps, smap = emit_compile_artifacts(axf, target, opt=opts.opt, allow_caps=opts.allow_caps, strict=opts.strict, profile=profile_obj)
    else:
        rep = compile_to_target(axf, target, opt=opts.opt, allow_caps=opts.allow_caps, strict=opts.strict)
        emitted, report, deps, smap = rep.emitted, None, None, None

    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(emitted, encoding="utf-8")

    if artifacts_dir and opts.emit_artifacts:
        ad = Path(artifacts_dir)
        ad.mkdir(parents=True, exist_ok=True)
        ad.joinpath("report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        ad.joinpath("deps.dot").write_text(deps, encoding="utf-8")
        ad.joinpath("map.json").write_text(json.dumps(smap, indent=2), encoding="utf-8")
        if header_obj:
            ad.joinpath("header.json").write_text(json.dumps(header_obj.__dict__, indent=2), encoding="utf-8")
        ad.joinpath("core.axf").write_text(axf, encoding="utf-8")
        if profile_obj:
            from .profiles.schema import to_jsonable
            ad.joinpath("profile.json").write_text(json.dumps(to_jsonable(profile_obj), indent=2), encoding="utf-8")

    if report is not None and profile_obj is not None:
        report["profile_name"] = profile_obj.name

    return BuildResult(
        
        source_kind=kind,
        header=(header_obj.__dict__ if header_obj else None),
        axf=axf,
        target=target,
        emitted=emitted,
        report=report,
        deps_dot=deps,
        sourcemap=smap,
    )
