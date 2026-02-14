from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re

TF_MAP = {
    "1m":"1", "5m":"5", "15m":"15", "30m":"30",
    "1h":"60", "4h":"240",
    "1D":"D", "1W":"W", "1MN":"MN",
}

@dataclass
class EHeader:
    target: Optional[str] = None
    execution_profile: Optional[str] = None
    sandbox: Dict[str, str] = field(default_factory=dict)

@dataclass
class ETranspileResult:
    header: EHeader
    axf: str

class EParseError(Exception): ...

def transpile_e(src: str) -> ETranspileResult:
    lines = src.replace("\r\n","\n").split("\n")
    hdr = EHeader()
    out: List[str] = []
    i = 0

    def parse_expr(txt: str) -> str:
        txt = txt.strip()
        m = re.match(r"the\s+(\d+)\-period\s+(EMA|SMA|WMA)\s+of\s+(bid|ask|close|open|high|low)\s*$", txt, re.I)
        if m:
            n = int(m.group(1))
            fn = m.group(2).lower()
            field = m.group(3).lower()
            return f"{fn}({field}, {n})"
        m = re.match(r"(bid|ask|close|open|high|low)\s+on\s+timeframe\s+([0-9A-Za-z]+)\s+of\s+(".*?")\s*$", txt, re.I)
        if m:
            field = m.group(1).lower()
            tf = m.group(2)
            sym = m.group(3)
            if tf not in TF_MAP:
                raise EParseError(f"Unknown timeframe '{tf}'")
            return f"series_from({sym}, \"{TF_MAP[tf]}\", \"{field}\")"
        if re.match(r"^".*"$", txt): return txt
        if re.match(r"^[0-9]+(\.[0-9]+)?$", txt): return txt
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", txt): return txt
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*\s*\(", txt):
            return txt
        if txt.lower() in {"bid","ask","close","open","high","low"}:
            return txt.lower()
        raise EParseError(f"Could not parse expr: {txt!r}")

    def parse_cond(txt: str) -> str:
        txt = txt.strip()
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", txt):
            return txt
        m = re.match(r"(.+?)\s+crosses\s+(above|below)\s+(.+)$", txt, re.I)
        if m:
            a = parse_expr(m.group(1))
            b = parse_expr(m.group(3))
            return f"cross_{'over' if m.group(2).lower()=='above' else 'under'}({a}, {b})"
        m = re.match(r"(.+?)\s+is\s+(above|below)\s+(.+)$", txt, re.I)
        if m:
            a = parse_expr(m.group(1))
            b = parse_expr(m.group(3))
            op = ">" if m.group(2).lower()=="above" else "<"
            return f"({a} {op} {b})"
        m = re.match(r"(.+?)\s*(>=|<=|==|!=|>|<)\s*(.+)$", txt)
        if m:
            return f"({parse_expr(m.group(1))} {m.group(2)} {parse_expr(m.group(3))})"
        if " and " in txt:
            parts = [parse_cond(p) for p in txt.split(" and ")]
            return "(" + " and ".join(parts) + ")"
        if " or " in txt:
            parts = [parse_cond(p) for p in txt.split(" or ")]
            return "(" + " or ".join(parts) + ")"
        if txt.lower().startswith("not "):
            return f"(not {parse_cond(txt[4:])})"
        raise EParseError(f"Could not parse condition: {txt!r}")

    def consume_header(line: str) -> bool:
        s = line.strip()
        if not s:
            return True
        m = re.match(r"Target\s+is\s+([A-Za-z0-9_\.]+)\.$", s)
        if m:
            hdr.target = m.group(1)
            return True
        m = re.match(r"Execution\s+profile\s+is\s+(".*?")\.$", s)
        if m:
            hdr.execution_profile = m.group(1)[1:-1]
            return True
        if s == "Sandbox limits:":
            return True
        m = re.match(r"(max\s+entries\s+per\s+bar|max\s+size|max\s+open\s+positions)\s+(.+?)\.$", s)
        if m:
            hdr.sandbox[m.group(1)] = m.group(2)
            return True
        return False

    def transpile_action(stmt: str) -> List[str]:
        s = stmt.strip()
        m = re.match(r"enter\s+(long|short)\s+trade\s+with\s+size\s+([0-9]+(?:\.[0-9]+)?)"
                     r"(?:\s+stop\s+(\d+)\s+points)?"
                     r"(?:\s+take\s+(\d+)\s+points)?"
                     r"(?:\s+tag\s+(".*?"))?\.$", s, re.I)
        if m:
            side = m.group(1).lower()
            qty = m.group(2)
            sl = m.group(3)
            tp = m.group(4)
            tag = m.group(5) or ""AF""
            fn = "trade.enter_long" if side=="long" else "trade.enter_short"
            parts = [f"qty={qty}"]
            if sl is not None: parts.append(f"sl_points={sl}")
            if tp is not None: parts.append(f"tp_points={tp}")
            parts.append(f"tag={tag}")
            return [f"  {fn}({', '.join(parts)})"]
        m = re.match(r"exit\s+trade\s+tagged\s+(".*?")\.$", s, re.I)
        if m:
            tag = m.group(1)
            return [f"  trade.exit(tag={tag})"]
        m = re.match(r"update\s+([A-Za-z_][A-Za-z0-9_]*)\s+to\s+the\s+(maximum|minimum)\s+of\s+([A-Za-z_][A-Za-z0-9_]*)\s+and\s+(bid|ask|close|open|high|low)\.$", s, re.I)
        if m:
            st = m.group(1)
            op = "max" if m.group(2).lower()=="maximum" else "min"
            rhs = m.group(4).lower()
            return [f"  reduce {st}.value = {rhs} using {op}"]
        if s.startswith("#"):
            return []
        raise EParseError(f"Unrecognized action: {stmt!r}")

    while i < len(lines):
        line = lines[i]
        if consume_header(line):
            i += 1
            continue

        s = line.strip()
        if not s:
            i += 1
            continue

        m = re.match(r"Define\s+([A-Za-z_][A-Za-z0-9_]*)\s+as\s+(.+?)\.$", s, re.I)
        if m:
            name = m.group(1)
            expr = parse_expr(m.group(2))
            out.append(f"let {name} = {expr}")
            i += 1
            continue

        m = re.match(r"Define\s+([A-Za-z_][A-Za-z0-9_]*)\s+(?:signal\s+)?when\s+(.+?)\.$", s, re.I)
        if m:
            name = m.group(1)
            cond = parse_cond(m.group(2))
            out.append(f"signal {name} = {cond}")
            i += 1
            continue

        m = re.match(r"Keep\s+state\s+([A-Za-z_][A-Za-z0-9_]*)\s+version\s+(\d+)(?:\s+starting\s+at\s+([0-9]+(?:\.[0-9]+)?))?\.$", s, re.I)
        if m:
            name = m.group(1)
            ver = int(m.group(2))
            init = m.group(3) or "0"
            out.append(f"state {name} v {ver} {{ value:float = {init} }}")
            i += 1
            continue

        m = re.match(r"On\s+each\s+(bar|tick)\s*,\s*$", s, re.I)
        if m:
            evt = m.group(1).lower()
            out.append(f"on {evt} {{")
            i += 1
            while i < len(lines):
                ln = lines[i]
                if not ln.startswith("    "):
                    break
                stmt = ln[4:].rstrip()
                if not stmt:
                    i += 1
                    continue
                m2 = re.match(r"if\s+(.+?)\s*,\s*$", stmt, re.I)
                if m2:
                    cond = parse_cond(m2.group(1))
                    out.append(f"  if {cond} {{")
                    i += 1
                    while i < len(lines):
                        ln2 = lines[i]
                        if not ln2.startswith("        "):
                            break
                        inner = ln2[8:].strip()
                        if inner:
                            out.extend(transpile_action(inner))
                        i += 1
                    out.append("  }")
                    continue
                out.extend(transpile_action(stmt))
                i += 1
            out.append("}")
            continue

        raise EParseError(f"Unrecognized statement: {line!r}")

    return ETranspileResult(header=hdr, axf="\n".join(out) + "\n")
