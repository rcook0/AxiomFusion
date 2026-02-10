from __future__ import annotations
from dataclasses import dataclass
from typing import List

KEYWORDS = {
    "input","let","signal","state","v","on","bar","tick",
    "if","set","reduce","using",
    "sum","min","max","last",
    "and","or","not","true","false",
    "bool","int","float","string","series",
}

SYMBOLS = {"{","}","(",")","[","]",",",":","=",".","+","-","*","/","<",">"}
MULTI = {"<=":None, ">=":None, "==":None, "!=":None}

@dataclass
class Tok:
    kind: str
    text: str
    pos: int
    end: int

class LexError(Exception): ...

def lex(src: str) -> List[Tok]:
    i, n = 0, len(src)
    out: List[Tok] = []
    def emit(kind, text, pos, end): out.append(Tok(kind, text, pos, end))

    while i < n:
        c = src[i]
        if c in " \t\r\n":
            i += 1; continue
        if c == "#":
            while i < n and src[i] != "\n": i += 1
            continue
        if c == "/" and i+1 < n and src[i+1] == "/":
            while i < n and src[i] != "\n": i += 1
            continue
        if c == '"':
            j = i+1; esc = False
            while j < n:
                if not esc and src[j] == '"': break
                if not esc and src[j] == "\\": esc = True
                else: esc = False
                j += 1
            if j >= n or src[j] != '"': raise LexError(f"Unterminated string at {i}")
            emit("STRING", src[i:j+1], i, j+1); i = j+1; continue
        if i+1 < n and src[i:i+2] in MULTI:
            emit("OP", src[i:i+2], i, i+2); i += 2; continue
        if c.isdigit():
            j = i
            while j < n and src[j].isdigit(): j += 1
            if j < n and src[j] == ".":
                j2 = j+1
                while j2 < n and src[j2].isdigit(): j2 += 1
                emit("NUMBER", src[i:j2], i, j2); i = j2; continue
            emit("NUMBER", src[i:j], i, j); i = j; continue
        if c.isalpha() or c == "_":
            j = i
            while j < n and (src[j].isalnum() or src[j] == "_"): j += 1
            text = src[i:j]
            emit("KW" if text in KEYWORDS else "IDENT", text, i, j)
            i = j; continue
        if c in SYMBOLS:
            kind = "OP" if c in "+-*/<>" else "SYM"
            emit(kind, c, i, i+1); i += 1; continue
        raise LexError(f"Unexpected character '{c}' at {i}")

    emit("EOF","",n,n)
    return out
