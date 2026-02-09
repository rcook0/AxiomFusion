import pandas as pd
from axiomfusion.runtime import run_backtest, TraceConfig

def test_traces_capture():
    df = pd.DataFrame({"open":[1,1], "high":[1,1], "low":[1,1], "close":[2,0.5], "volume":[1,1]})
    def strat(ctx, state):
        return [{"kind":"enter_long","symbol":"TEST","qty":0.1,"sl_points":1,"tp_points":2,"tag":"L"}]
    out = run_backtest(df, strat, trace=TraceConfig(watch=("close","open"), capture_intents=True, capture_fills=True))
    assert len(out["traces"]) == 2
    assert "intents" in out["traces"][0]
    assert "fills" in out["traces"][0]
