import pandas as pd
from pathlib import Path
from axiomfusion.e_lang import transpile_e
from axiomfusion.pythonrt.backtest import run_backtest_from_source, EngineConfig
from axiomfusion.profiles.registry import load_profile

def test_python_backtest_runs():
    src_e = Path("fixtures/basic_macd.e").read_text(encoding="utf-8")
    axf = transpile_e(src_e).axf
    df = pd.read_csv("data/sample_ohlcv.csv")
    df["time"] = pd.to_datetime(df["time"])
    df = df.set_index("time").sort_index()
    prof = load_profile("RAW_SPREAD")
    res = run_backtest_from_source(axf, df, cfg=EngineConfig(trace_path=None, profile=prof))
    assert "final" in res
    assert "equity" in res["final"]
