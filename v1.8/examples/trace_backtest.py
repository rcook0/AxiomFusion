import pandas as pd
from axiomfusion.runtime import run_backtest, BacktestConfig, TraceConfig
from axiomfusion.sandbox import SandboxConfig

def strategy(ctx, state):
    state.setdefault("n", 0)
    state["n"] += 1
    if ctx["close"] > ctx["open"]:
        return [{"kind":"enter_long","symbol":"TEST","qty":0.1,"sl_points":1,"tp_points":2,"tag":"L"}]
    return []

if __name__ == "__main__":
    df = pd.DataFrame({
        "open":[1,1.1,1.2],
        "high":[1.1,1.2,1.3],
        "low":[0.9,1.0,1.1],
        "close":[1.05,1.05,1.25],
        "volume":[100,120,110],
    })
    out = run_backtest(
        df,
        strategy,
        BacktestConfig(symbol="EURUSD", spread=0.0001, slippage=0.00005, commission_per_lot=3.5),
        sandbox_cfg=SandboxConfig(max_intents_per_bar=1),
        trace=TraceConfig(watch=("close","open","n"))
    )
    for row in out["traces"]:
        print(row)
