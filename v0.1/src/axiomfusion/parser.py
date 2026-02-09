from __future__ import annotations
from typing import List, Optional, Tuple
from .lexer import Tok, lex
from . import ast as A

class ParseError(Exception): ...

class P:
    def __init__(self, toks: List[Tok]):
        self.toks = toks
        self.i = 0

    def peek(self) -> Tok:
        return self.toks[self.i]

    def eat(self, kind: Optional[str]=None, text: Optional[str]=None) -> Tok:
        t = self.peek()
        if kind and t.kind != kind:
            raise ParseError(f"Expected {kind}, got {t.kind} at {t.pos}")
        if text and t.text != text:
            raise ParseError(f"Expected '{text}', got '{t.text}' at {t.pos}")
        self.i += 1
        return t

    def accept(self, kind: Optional[str]=None, text: Optional[str]=None) -> Optional[Tok]:
        t = self.peek()
        if kind and t.kind != kind:
            return None
        if text and t.text != text:
            return None
        self.i += 1
        return t

def parse(src: str) -> A.Module:
    toks = lex(src)
    p = P(toks)
    decls: List[A.Decl] = []
    while p.peek().kind != "EOF":
        decls.append(parse_decl(p))
    p.eat("EOF")
    return A.Module(decls)

def parse_decl(p: P) -> A.Decl:
    t = p.peek()
    if t.kind == "KW" and t.text == "input":
        p.eat("KW","input")
        name = p.eat("IDENT").text
        p.eat("SYM",":")
        typ = parse_type(p)
        p.eat("SYM","=")
        expr = parse_expr(p)
        return A.InputDecl(name, typ, expr)
    if t.kind == "KW" and t.text == "let":
        p.eat("KW","let")
        name = p.eat("IDENT").text
        p.eat("SYM","=")
        expr = parse_expr(p)
        return A.LetDecl(name, expr)
    if t.kind == "KW" and t.text == "signal":
        p.eat("KW","signal")
        name = p.eat("IDENT").text
        p.eat("SYM","=")
        expr = parse_expr(p)
        return A.SignalDecl(name, expr)
    if t.kind == "KW" and t.text == "on":
        p.eat("KW","on")
        p.eat("KW","bar")
        stmts = parse_block(p)
        return A.OnBar(stmts)
    raise ParseError(f"Unexpected decl start '{t.text}' at {t.pos}")

def parse_type(p: P) -> str:
    t = p.peek()
    if t.kind == "KW" and t.text in {"bool","int","float","string"}:
        return p.eat("KW").text
    if t.kind == "KW" and t.text == "series":
        p.eat("KW","series")
        p.eat("OP","<")
        inner = parse_type(p)
        p.eat("OP",">")
        return f"series<{inner}>"
    raise ParseError(f"Bad type at {t.pos}: {t.text}")

def parse_block(p: P):
    p.eat("SYM","{")
    out: List[A.Stmt] = []
    while not (p.peek().kind == "SYM" and p.peek().text == "}"):
        out.append(parse_stmt(p))
    p.eat("SYM","}")
    return out

def parse_stmt(p: P) -> A.Stmt:
    t = p.peek()
    if t.kind == "KW" and t.text == "if":
        p.eat("KW","if")
        cond = parse_expr(p)
        block = parse_block(p)
        return A.IfStmt(cond, block)
    # call statement
    call = parse_call(p)
    return A.CallStmt(call)

# ---- Expressions ----
def parse_expr(p: P) -> A.Expr:
    return parse_or(p)

def parse_or(p: P):
    e = parse_and(p)
    while p.peek().kind == "KW" and p.peek().text == "or":
        p.eat("KW","or")
        r = parse_and(p)
        e = A.BinOp("or", e, r)
    return e

def parse_and(p: P):
    e = parse_eq(p)
    while p.peek().kind == "KW" and p.peek().text == "and":
        p.eat("KW","and")
        r = parse_eq(p)
        e = A.BinOp("and", e, r)
    return e

def parse_eq(p: P):
    e = parse_cmp(p)
    while p.peek().kind == "OP" and p.peek().text in {"==","!="}:
        op = p.eat("OP").text
        r = parse_cmp(p)
        e = A.BinOp(op, e, r)
    return e

def parse_cmp(p: P):
    e = parse_term(p)
    while p.peek().kind == "OP" and p.peek().text in {"<","<=",">",">="}:
        op = p.eat("OP").text
        r = parse_term(p)
        e = A.BinOp(op, e, r)
    return e

def parse_term(p: P):
    e = parse_factor(p)
    while p.peek().kind == "OP" and p.peek().text in {"+","-"}:
        op = p.eat("OP").text
        r = parse_factor(p)
        e = A.BinOp(op, e, r)
    return e

def parse_factor(p: P):
    e = parse_unary(p)
    while p.peek().kind == "OP" and p.peek().text in {"*","/"}:
        op = p.eat("OP").text
        r = parse_unary(p)
        e = A.BinOp(op, e, r)
    return e

def parse_unary(p: P):
    if p.peek().kind == "KW" and p.peek().text == "not":
        p.eat("KW","not")
        return A.UnOp("not", parse_unary(p))
    if p.peek().kind == "OP" and p.peek().text == "-":
        p.eat("OP","-")
        return A.UnOp("-", parse_unary(p))
    return parse_postfix(p)

def parse_postfix(p: P):
    e = parse_primary(p)
    while True:
        if p.peek().kind == "SYM" and p.peek().text == "[":
            p.eat("SYM","[")
            # only allow negative indexing: [-k]
            p.eat("OP","-")
            k = int(p.eat("NUMBER").text)
            p.eat("SYM","]")
            e = A.Index(e, k)
            continue
        if p.peek().kind == "SYM" and p.peek().text == "(":
            if isinstance(e, A.Var):
                # convert var into call
                name = e.name
                call = parse_call_suffix(p, name)
                e = call
                continue
            else:
                raise ParseError(f"Only identifiers can be called at {p.peek().pos}")
        break
    return e

def parse_primary(p: P):
    t = p.peek()
    if t.kind == "NUMBER":
        txt = p.eat("NUMBER").text
        if "." in txt:
            return A.Lit(float(txt))
        return A.Lit(int(txt))
    if t.kind == "STRING":
        txt = p.eat("STRING").text
        return A.Lit(eval(txt))  # safe enough for simple strings here
    if t.kind == "KW" and t.text in {"true","false"}:
        return A.Lit(p.eat("KW").text == "true")
    if t.kind == "IDENT":
        return A.Var(p.eat("IDENT").text)
    raise ParseError(f"Bad primary at {t.pos}: {t.text}")

def parse_call(p: P) -> A.Call:
    name_tok = p.eat("IDENT")
    name = name_tok.text
    return parse_call_suffix(p, name)

def parse_call_suffix(p: P, name: str) -> A.Call:
    p.eat("SYM","(")
    args: List[Tuple[Optional[str], A.Expr]] = []
    if not (p.peek().kind == "SYM" and p.peek().text == ")"):
        while True:
            # kw arg?
            if p.peek().kind == "IDENT":
                # lookahead for '='
                t0 = p.peek()
                t1 = p.toks[p.i+1]
                if t1.kind == "SYM" and t1.text == "=":
                    kw = p.eat("IDENT").text
                    p.eat("SYM","=")
                    ex = parse_expr(p)
                    args.append((kw, ex))
                else:
                    ex = parse_expr(p)
                    args.append((None, ex))
            else:
                ex = parse_expr(p)
                args.append((None, ex))
            if p.accept("SYM",","):
                continue
            break
    p.eat("SYM",")")
    return A.Call(name, args)
