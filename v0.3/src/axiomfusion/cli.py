from __future__ import annotations
import argparse, os
from .parser import parse
from .typecheck import typecheck
from .ir import lower
from .emitters import pine, mql5, python_rt

def main():
    ap = argparse.ArgumentParser(prog="axiomfusion")
    sub = ap.add_subparsers(dest="cmd", required=True)

    cp = sub.add_parser("compile", help="Compile .axf to a target")
    cp.add_argument("path")
    cp.add_argument("--target", choices=["pine","mql5","python"], required=True)
    cp.add_argument("--out", required=True)

    args = ap.parse_args()
    if args.cmd == "compile":
        with open(args.path, "r", encoding="utf-8") as f:
            src = f.read()
        ast = parse(src)
        _, expr_types = typecheck(ast)
        irmod = lower(ast, expr_types)
        if args.target == "pine":
            out = pine.emit(irmod)
        elif args.target == "mql5":
            out = mql5.emit(irmod)
        else:
            out = python_rt.emit(irmod)
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"Wrote {args.out}")

if __name__ == "__main__":
    main()
