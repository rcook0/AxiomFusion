from __future__ import annotations
import argparse
from pathlib import Path

from .compiler import compile_to_target

def main():
    ap = argparse.ArgumentParser(prog="axiomfusionc", description="AxiomFusion compiler")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("compile", help="Compile .axf to a target")
    c.add_argument("--in", dest="inp", required=True, help="Input .axf file")
    c.add_argument("--out", dest="out", required=True, help="Output file")
    c.add_argument("--target", required=True, help="Target name (e.g. pine.strategy)")
    c.add_argument("--opt", default="O2", choices=["O0","O1","O2","O3"], help="Optimization level")
    c.add_argument("--allow", default=None, help="Override allowed caps: comma-separated (e.g. trade,tick,state,mtf)")
    c.add_argument("--non-strict", action="store_true", help="Warn instead of failing on missing caps (NOT recommended)")
    c.add_argument("--report", dest="report", default=None, help="Write compile report JSON to path")
    c.add_argument("--deps-dot", dest="deps_dot", default=None, help="Write deps graph DOT to path")
    c.add_argument("--sourcemap", dest="sourcemap", default=None, help="Write sourcemap JSON to path")

    args = ap.parse_args()

    allow = None
    if args.allow:
        allow = set([x.strip() for x in args.allow.split(",") if x.strip()])

    src = Path(args.inp).read_text(encoding="utf-8")
    rep = compile_to_target(src, args.target, opt=args.opt, allow_caps=allow, strict=(not args.non_strict))
    Path(args.out).write_text(rep.emitted, encoding="utf-8")


# Optional artifacts
if args.report or args.deps_dot or args.sourcemap:
    from .compiler import emit_compile_artifacts
    _, report, deps, smap = emit_compile_artifacts(src, args.target, opt=args.opt, allow_caps=allow, strict=(not args.non_strict))
    if args.report:
        Path(args.report).write_text(__import__("json").dumps(report, indent=2), encoding="utf-8")
    if args.deps_dot:
        Path(args.deps_dot).write_text(deps, encoding="utf-8")
    if args.sourcemap:
        Path(args.sourcemap).write_text(__import__("json").dumps(smap, indent=2), encoding="utf-8")

    print(f"target: {rep.target}")
    print(f"opt: {rep.opt}")
    print(f"required_caps: {sorted(rep.required_caps)}")
    print(f"allowed_caps: {sorted(rep.allowed_caps)}")

if __name__ == "__main__":
    main()
