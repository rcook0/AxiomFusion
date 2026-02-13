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

    

v = sub.add_parser("validate", help="Validate a source against a target contract")
v.add_argument("--in", dest="inp", required=True, help="Input .axf file")
v.add_argument("--target", required=True, help="Target name (e.g. pine.strategy)")
v.add_argument("--opt", default="O2", choices=["O0","O1","O2","O3"], help="Optimization level")
v.add_argument("--allow", default=None, help="Override allowed caps: comma-separated")
v.add_argument("--non-strict", action="store_true", help="Warn instead of failing on missing caps")


if __name__ == "__main__":
    main()



e1 = sub.add_parser("transpile-e", help="Transpile English-like .e into core .axf")
e1.add_argument("--in", dest="inp", required=True, help="Input .e file")
e1.add_argument("--out", dest="out", required=True, help="Output .axf file")
e1.add_argument("--emit-header", action="store_true", help="Emit parsed header JSON next to output")

e2 = sub.add_parser("compile-e", help="Compile English-like .e directly to a target")
e2.add_argument("--in", dest="inp", required=True, help="Input .e file")
e2.add_argument("--out", dest="out", required=True, help="Output file")
e2.add_argument("--target", required=False, help="Target name; if omitted, uses 'Target is ...' header")
e2.add_argument("--opt", default="O2", choices=["O0","O1","O2","O3"], help="Optimization level")
e2.add_argument("--allow", default=None, help="Override allowed caps: comma-separated")
e2.add_argument("--non-strict", action="store_true", help="Warn instead of failing on missing caps")


b = sub.add_parser("build", help="Full pipeline: ingest (.e/.axf) -> validate -> optimize -> emit + artifacts")
b.add_argument("--in", dest="inp", required=True, help="Input .e or .axf")
b.add_argument("--out", dest="out", required=True, help="Output file")
b.add_argument("--target", required=False, help="Target name; if omitted and input is .e, uses header 'Target is ...'")
b.add_argument("--opt", default="O2", choices=["O0","O1","O2","O3"], help="Optimization level")
b.add_argument("--allow", default=None, help="Override allowed caps: comma-separated")
b.add_argument("--non-strict", action="store_true", help="Warn instead of failing on missing caps")
b.add_argument("--artifacts", default=None, help="Directory to write artifacts (report.json, deps.dot, map.json, core.axf)")

args = ap.parse_args()

allow = None
if getattr(args, "allow", None):
    allow = set([x.strip() for x in args.allow.split(",") if x.strip()])


if args.cmd == "build":
    from .pipeline import BuildOptions, build_from_file
    bo = BuildOptions(
        target=getattr(args, "target", None),
        opt=getattr(args, "opt", "O2"),
        allow_caps=allow,
        strict=(not getattr(args, "non_strict", False)),
        emit_artifacts=True,
    )
    res = build_from_file(args.inp, args.out, artifacts_dir=getattr(args, "artifacts", None), opts=bo)
    print(f"OK: {res.target} ({res.source_kind}) opt={bo.opt}")
    return

if args.cmd == "compile":
    src = Path(args.inp).read_text(encoding="utf-8")
    rep = compile_to_target(src, args.target, opt=args.opt, allow_caps=allow, strict=(not args.non_strict))
    Path(args.out).write_text(rep.emitted, encoding="utf-8")

    # Optional artifacts
    if getattr(args, "report", None) or getattr(args, "deps_dot", None) or getattr(args, "sourcemap", None):
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
    return


    if args.cmd == "transpile-e":
        from .e_lang import transpile_e
        src_e = Path(args.inp).read_text(encoding="utf-8")
        res = transpile_e(src_e)
        Path(args.out).write_text(res.axf, encoding="utf-8")
        if args.emit_header:
            Path(str(args.out) + ".header.json").write_text(__import__("json").dumps(res.header.__dict__, indent=2), encoding="utf-8")
        print("OK")
        return

    if args.cmd == "compile-e":
        from .e_lang import transpile_e
        src_e = Path(args.inp).read_text(encoding="utf-8")
        res = transpile_e(src_e)
        target = args.target or res.header.target
        if not target:
            raise SystemExit("No target specified. Provide --target or 'Target is ...' header.")
        rep = compile_to_target(res.axf, target, opt=args.opt, allow_caps=allow, strict=(not args.non_strict))
        Path(args.out).write_text(rep.emitted, encoding="utf-8")
        print(f"target: {rep.target}")
        print(f"opt: {rep.opt}")
        print(f"required_caps: {sorted(rep.required_caps)}")
        return

if args.cmd == "validate":
    from .contracts.validate import validate_file
    res = validate_file(args.inp, args.target, opt=args.opt, strict=(not args.non_strict), allow_caps=allow)
    if res.ok:
        print("OK")
        return
    print("FAIL")
    for e in res.errors:
        print(" -", e)
    raise SystemExit(2)
