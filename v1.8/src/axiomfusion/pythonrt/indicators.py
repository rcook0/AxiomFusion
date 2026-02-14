from __future__ import annotations
import numpy as np
import pandas as pd
from .series import Series, ensure_series

def sma(x: Series, n: int) -> Series:
    s = pd.Series(x.values)
    out = s.rolling(n, min_periods=n).mean().to_numpy(dtype=float)
    return Series(name=f"sma({x.name},{n})", values=out, index=x.index)

def ema(x: Series, n: int) -> Series:
    s = pd.Series(x.values)
    out = s.ewm(span=n, adjust=False, min_periods=n).mean().to_numpy(dtype=float)
    return Series(name=f"ema({x.name},{n})", values=out, index=x.index)

def highest(x: Series, n: int) -> Series:
    s = pd.Series(x.values)
    out = s.rolling(n, min_periods=n).max().to_numpy(dtype=float)
    return Series(name=f"highest({x.name},{n})", values=out, index=x.index)

def lowest(x: Series, n: int) -> Series:
    s = pd.Series(x.values)
    out = s.rolling(n, min_periods=n).min().to_numpy(dtype=float)
    return Series(name=f"lowest({x.name},{n})", values=out, index=x.index)

def stddev(x: Series, n: int) -> Series:
    s = pd.Series(x.values)
    out = s.rolling(n, min_periods=n).std(ddof=0).to_numpy(dtype=float)
    return Series(name=f"stddev({x.name},{n})", values=out, index=x.index)

def roc(x: Series, n: int) -> Series:
    v = x.values.astype(float)
    out = np.empty_like(v)
    out[:] = np.nan
    out[n:] = (v[n:] - v[:-n]) / v[:-n]
    return Series(name=f"roc({x.name},{n})", values=out, index=x.index)

def macd(x: Series, fast: int, slow: int, sig: int):
    ef = ema(x, fast).values
    es = ema(x, slow).values
    line = ef - es
    line_s = Series(name="macd_line", values=line, index=x.index)
    sig_s = ema(line_s, sig).values
    hist = line - sig_s
    return (Series(name="macd_line", values=line, index=x.index),
            Series(name="macd_signal", values=sig_s, index=x.index),
            Series(name="macd_hist", values=hist, index=x.index))

def macd_hist(x: Series, fast: int, slow: int, sig: int) -> Series:
    return macd(x, fast, slow, sig)[2]
