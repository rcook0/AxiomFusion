from __future__ import annotations
from typing import List, Optional, Tuple
from .lexer import Tok, lex
from .meta import MetaTable
from . import ast as A

class ParseError(Exception): ...

class P:
    def __init__(self, toks: List[Tok]):
        self.toks = toks
        self.i = 0
    def peek(self) -> Tok: return self.toks[self.i]
    def eat(self, kind: Optional[str]=None, text: Optional[str]=None) -> Tok:
        t = self.peek()
        if kind and t.kind != kind: raise ParseError(f"Expected {kind}, got {t.kind} at {t.pos}")
        if text and t.text != text: raise ParseError(f"Expected '{text}', got '{t.text}' at {t.pos}")
        self.i += 1; return t
    def accept(self, kind: Optional[str]=None, text: Optional[str]=None) -> Optional[Tok]:
        t = self.peek()
        if kind and t.kind != kind: return None
        if text and t.text != text: return None
        self.i += 1; return t

def parse(src: str) -> A.Module:
    toks = lex(src); p = P(toks)
    decls: List[A.Decl] = []
    while p.peek().kind != "EOF":
        decls.append(parse_decl(p))
    p.eat("EOF")
    return A.Module(decls)

def parse_decl(p: P) -> A.Decl:
    t = p.peek()
    if t.kind == "KW" and t.text == "input":
        p.eat("KW","input"); name = p.eat("IDENT").text
        p.eat("SYM",":"); typ = parse_type(p)
        p.eat("SYM","="); expr = parse_expr(p)
        return A.InputDecl(name, typ, expr)
    if t.kind == "KW" and t.text == "let":
        p.eat("KW","let"); name = p.eat("IDENT").text
        p.eat("SYM","="); return A.LetDecl(name, parse_expr(p))
    if t.kind == "KW" and t.text == "signal":
        p.eat("KW","signal"); name = p.eat("IDENT").text
        p.eat("SYM","="); return A.SignalDecl(name, parse_expr(p))
    if t.kind == "KW" and t.text == "state":
        return parse_state(p)
    if t.kind == "KW" and t.text == "on":
        p.eat("KW","on")
        if p.peek().kind == "KW" and p.peek().text == "bar":
            p.eat("KW","bar"); return A.OnBar(parse_block(p))
        if p.peek().kind == "KW" and p.peek().text == "tick":
            p.eat("KW","tick"); return A.OnTick(parse_block(p))
        raise ParseError(f"Expected bar/tick after on at {p.peek().pos}")
    raise ParseError(f"Unexpected decl start '{t.text}' at {t.pos}")

def parse_state(p: P) -> A.StateDecl:
    p.eat("KW","state"); name = p.eat("IDENT").text
    p.eat("KW","v"); ver = int(float(p.eat("NUMBER").text))
    p.eat("SYM","{")
    fields: List[A.StateField] = []
    while not (p.peek().kind == "SYM" and p.peek().text == "}"):
        fname = p.eat("IDENT").text
        p.eat("SYM",":"); ftyp = parse_scalar_type(p)
        p.eat("SYM","="); fexpr = parse_expr(p)
        fields.append(A.StateField(fname, ftyp, fexpr))
    p.eat("SYM","}")
    return A.StateDecl(name, ver, fields)

def parse_type(p: P) -> str:
    t = p.peek()
    if t.kind == "KW" and t.text in {"bool","int","float","string"}:
        return p.eat("KW").text
    if t.kind == "KW" and t.text == "series":
        p.eat("KW","series"); p.eat("OP","<")
        inner = parse_scalar_type(p)
        p.eat("OP",">")
        return f"series<{inner}>"
    raise ParseError(f"Bad type at {t.pos}: {t.text}")

def parse_scalar_type(p: P) -> str:
    t = p.peek()
    if t.kind == "KW" and t.text in {"bool","int","float","string"}:
        return p.eat("KW").text
    raise ParseError(f"Bad scalar type at {t.pos}: {t.text}")

def parse_block(p: P):
    p.eat("SYM","{"); out: List[A.Stmt] = []
    while not (p.peek().kind == "SYM" and p.peek().text == "}"):
        out.append(parse_stmt(p))
    p.eat("SYM","}"); return out

def parse_stmt(p: P) -> A.Stmt:
    t = p.peek()
    if t.kind == "KW" and t.text == "if":
        p.eat("KW","if"); cond = parse_expr(p); block = parse_block(p)
        return A.IfStmt(cond, block)
    if t.kind == "KW" and t.text == "set":
        p.eat("KW","set"); target = parse_lvalue(p)
        p.eat("SYM","="); ex = parse_expr(p)
        return A.SetStmt(target, ex)
    if t.kind == "KW" and t.text == "reduce":
        p.eat("KW","reduce"); target = parse_lvalue(p)
        p.eat("SYM","="); ex = parse_expr(p)
        p.eat("KW","using"); op = p.eat("KW").text
        if op not in {"sum","min","max","last"}: raise ParseError(f"Bad reduce op {op}")
        return A.ReduceStmt(target, ex, op)
    call = parse_call(p)
    return A.CallStmt(call)

def parse_lvalue(p: P) -> A.Member:
    obj = A.Var(p.eat("IDENT").text)
    p.eat("SYM","."); field = p.eat("IDENT").text
    return A.Member(obj, field)

# ---- Expressions ----
def parse_expr(p: P) -> A.Expr: return parse_or(p)

def parse_or(p: P):
    e = parse_and(p)
    while p.peek().kind == "KW" and p.peek().text == "or":
        p.eat("KW","or"); e = A.BinOp("or", e, parse_and(p))
    return e

def parse_and(p: P):
    e = parse_eq(p)
    while p.peek().kind == "KW" and p.peek().text == "and":
        p.eat("KW","and"); e = A.BinOp("and", e, parse_eq(p))
    return e

def parse_eq(p: P):
    e = parse_cmp(p)
    while p.peek().kind == "OP" and p.peek().text in {"==","!="}:
        op = p.eat("OP").text; e = A.BinOp(op, e, parse_cmp(p))
    return e

def parse_cmp(p: P):
    e = parse_term(p)
    while p.peek().kind == "OP" and p.peek().text in {"<","<=",">",">="}:
        op = p.eat("OP").text; e = A.BinOp(op, e, parse_term(p))
    return e

def parse_term(p: P):
    e = parse_factor(p)
    while p.peek().kind == "OP" and p.peek().text in {"+","-"}:
        op = p.eat("OP").text; e = A.BinOp(op, e, parse_factor(p))
    return e

def parse_factor(p: P):
    e = parse_unary(p)
    while p.peek().kind == "OP" and p.peek().text in {"*","/"}:
        op = p.eat("OP").text; e = A.BinOp(op, e, parse_unary(p))
    return e

def parse_unary(p: P):
    if p.peek().kind == "KW" and p.peek().text == "not":
        p.eat("KW","not"); return A.UnOp("not", parse_unary(p))
    if p.peek().kind == "OP" and p.peek().text == "-":
        p.eat("OP","-"); return A.UnOp("-", parse_unary(p))
    return parse_postfix(p)

def parse_postfix(p: P):
    e = parse_primary(p)
    while True:
        if p.peek().kind == "SYM" and p.peek().text == ".":
            p.eat("SYM","."); e = A.Member(e, p.eat("IDENT").text); continue
        if p.peek().kind == "SYM" and p.peek().text == "[":
            p.eat("SYM","["); p.eat("OP","-")
            k = int(float(p.eat("NUMBER").text)); p.eat("SYM","]")
            e = A.Index(e, k); continue
        if p.peek().kind == "SYM" and p.peek().text == "(":
            if isinstance(e, A.Var):
                e = parse_call_suffix(p, e.name); continue
            raise ParseError("Only identifiers can be called")
        break
    return e

def parse_primary(p: P):
    t = p.peek()
    if t.kind == "NUMBER":
        txt = p.eat("NUMBER").text
        return A.Lit(float(txt) if "." in txt else int(txt))
    if t.kind == "STRING":
        return A.Lit(eval(p.eat("STRING").text))
    if t.kind == "KW" and t.text in {"true","false"}:
        return A.Lit(p.eat("KW").text == "true")
    if t.kind == "IDENT":
        return A.Var(p.eat("IDENT").text)
    raise ParseError(f"Bad primary at {t.pos}: {t.text}")

def parse_call(p: P) -> A.Call:
    return parse_call_suffix(p, p.eat("IDENT").text)

def parse_call_suffix(p: P, name: str) -> A.Call:
    p.eat("SYM","("); args: List[Tuple[Optional[str], A.Expr]] = []
    if not (p.peek().kind == "SYM" and p.peek().text == ")"):
        while True:
            if p.peek().kind == "IDENT" and p.toks[p.i+1].kind == "SYM" and p.toks[p.i+1].text == "=":
                kw = p.eat("IDENT").text; p.eat("SYM","="); args.append((kw, parse_expr(p)))
            else:
                args.append((None, parse_expr(p)))
            if p.accept("SYM",","): continue
            break
    p.eat("SYM",")")
    return A.Call(name, args)


def parse_with_meta(src: str):
    toks = lex(src); p = P(toks)
    meta = MetaTable()
    decls: List[A.Decl] = []
    while p.peek().kind != "EOF":
        decls.append(parse_decl_meta(p, meta))
    p.eat("EOF")
    return A.Module(decls), meta

def span_from(t0: Tok, t1: Tok):
    return (t0.pos, t1.end)

def parse_decl_meta(p: P, meta: MetaTable) -> A.Decl:
    t0 = p.peek()
    d = parse_decl(p)
    # best-effort span: from first token to previous token
    t1 = p.toks[p.i-1] if p.i>0 else t0
    meta.add(d, span_from(t0, t1), salt=type(d).__name__)
    return d
