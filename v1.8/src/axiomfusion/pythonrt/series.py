from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Sequence
import numpy as np
import pandas as pd

@dataclass
class Series:
    name: str
    values: np.ndarray  # float64
    index: Optional[pd.Index] = None

    def at(self, t: int) -> float:
        if t < 0 or t >= len(self.values):
            return float("nan")
        v = self.values[t]
        try:
            return float(v)
        except Exception:
            return float("nan")

    def rel(self, t: int, k: int) -> float:
        # k is relative (negative means past)
        return self.at(t + k)

def _to_arr(x) -> np.ndarray:
    if isinstance(x, Series):
        return x.values
    if isinstance(x, (pd.Series, pd.Index)):
        return np.asarray(x, dtype=float)
    return np.asarray(x, dtype=float)

def ensure_series(name: str, x, index=None) -> Series:
    if isinstance(x, Series):
        return x
    arr = _to_arr(x).astype(float)
    return Series(name=name, values=arr, index=index)

def binary_op(a: Series, b: Series, op: str) -> Series:
    av, bv = a.values, b.values
    if op == "+": out = av + bv
    elif op == "-": out = av - bv
    elif op == "*": out = av * bv
    elif op == "/": out = av / bv
    elif op == ">": out = (av > bv).astype(float)
    elif op == "<": out = (av < bv).astype(float)
    elif op == ">=": out = (av >= bv).astype(float)
    elif op == "<=": out = (av <= bv).astype(float)
    elif op == "==": out = (av == bv).astype(float)
    elif op == "!=": out = (av != bv).astype(float)
    elif op == "and": out = ((av != 0) & (bv != 0)).astype(float)
    elif op == "or": out = ((av != 0) | (bv != 0)).astype(float)
    else:
        raise ValueError(f"Unsupported op: {op}")
    return Series(name=f"({a.name}{op}{b.name})", values=out, index=a.index)

def unary_op(a: Series, op: str) -> Series:
    av = a.values
    if op == "-": out = -av
    elif op == "not": out = (av == 0).astype(float)
    else:
        raise ValueError(f"Unsupported unop: {op}")
    return Series(name=f"{op}{a.name}", values=out, index=a.index)

def shift(a: Series, k: int) -> Series:
    av = a.values
    out = np.empty_like(av, dtype=float)
    out[:] = np.nan
    if k < 0:
        kk = -k
        out[kk:] = av[:-kk]
    elif k > 0:
        out[:-k] = av[k:]
    else:
        out[:] = av
    return Series(name=f"{a.name}[{k}]", values=out, index=a.index)
