import pandas as pd
from axiomfusion.runtime import run_backtest, BacktestConfig

def strategy(ctx, state):
    # dumb demo: buy when close > open
    if ctx["close"] > ctx["open"]:
        return [{"kind":"enter_long","symbol":"TEST","qty":0.1,"sl_points":200,"tp_points":400,"tag":"L"}]
    return []

if __name__ == "__main__":
    df = pd.DataFrame({
        "open":[1,1.1,1.2],
        "high":[1.1,1.2,1.3],
        "low":[0.9,1.0,1.1],
        "close":[1.05,1.15,1.25],
        "volume":[100,120,110],
    })
    cfg = BacktestConfig(symbol="EURUSD", spread=0.0001, slippage=0.00005, commission_per_lot=3.5, leverage=100)
    res = run_backtest(df, strategy, cfg)
    print("fills:", [(t, r.accepted, r.fill_price, r.commission) for t,_,r in res["fills"]])
