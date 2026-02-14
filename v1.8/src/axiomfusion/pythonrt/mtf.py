from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict
import pandas as pd
import numpy as np
from .series import Series

TF_RULES = {
    "1": "1min", "1m": "1min",
    "5": "5min", "5m": "5min",
    "15": "15min", "15m": "15min",
    "30": "30min", "30m": "30min",
    "60": "60min", "1h": "60min",
    "240": "240min", "4h": "240min",
    "1d": "1D", "D": "1D",
}

def _tf_to_rule(tf: str) -> str:
    t = tf.strip().lower()
    return TF_RULES.get(t, tf)

def resample_ohlcv(df: pd.DataFrame, tf: str) -> pd.DataFrame:
    rule = _tf_to_rule(tf)
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("DF index must be DatetimeIndex for MTF resampling")
    o = df["open"].resample(rule).first()
    h = df["high"].resample(rule).max()
    l = df["low"].resample(rule).min()
    c = df["close"].resample(rule).last()
    v = df["volume"].resample(rule).sum()
    out = pd.DataFrame({"open":o,"high":h,"low":l,"close":c,"volume":v}).dropna()
    return out

def align_to_base(base_index: pd.DatetimeIndex, higher: pd.Series) -> pd.Series:
    # bar-close alignment: value becomes available at the close of the higher bar.
    # We forward-fill the latest completed bar onto base timestamps.
    return higher.reindex(base_index, method="ffill")

@dataclass
class MTFCache:
    base: pd.DataFrame
    cache: Dict[str, pd.DataFrame]

    def get(self, tf: str) -> pd.DataFrame:
        if tf in self.cache:
            return self.cache[tf]
        rs = resample_ohlcv(self.base, tf)
        self.cache[tf] = rs
        return rs
