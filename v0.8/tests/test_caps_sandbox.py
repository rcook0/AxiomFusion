from datetime import datetime
import pandas as pd

from axiomfusion.compile import compile_source
from axiomfusion.runtime import run_backtest
from axiomfusion.sandbox import SandboxConfig

def test_caps_infer_trade_tick_mtf_state():
    src = '''
state S v 1 { x:float = 0 }
let h1 = series_from("EURUSD","60","close")
on tick { reduce S.x = bid using max }
on bar { trade.enter_long(qty=0.1, sl_points=1, tp_points=2, tag="T") }
'''.strip()
    res = compile_source(src)
    assert "state" in res.capabilities
    assert "tick" in res.capabilities
    assert "mtf" in res.capabilities
    assert "trade" in res.capabilities

def test_sandbox_rate_limit_rejects():
    df = pd.DataFrame({"open":[1,1], "high":[1,1], "low":[1,1], "close":[1,1], "volume":[1,1]})
    def strat(ctx, state):
        # spam intents
        return [{"kind":"enter_long","symbol":"TEST","qty":0.1,"sl_points":1,"tp_points":2,"tag":f"T{i}"} for i in range(10)]
    out = run_backtest(df, strat, sandbox_cfg=SandboxConfig(max_intents_per_bar=2))
    rejects = [r for _,_,r in out["fills"] if not r.accepted]
    assert len(rejects) >= 1
