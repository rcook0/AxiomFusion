from datetime import datetime
from axiomfusion.policies.core import Intent, MarketSnapshot, Account
from axiomfusion.runtime import default_policy_chain, BacktestConfig

def test_policy_chain_fill_price_deterministic():
    cfg = BacktestConfig(spread=0.2, slippage=0.1, commission_per_lot=2.0)
    chain = default_policy_chain(cfg)
    acct = Account()
    mkt = MarketSnapshot("X", datetime(2020,1,1), mid=100.0, bid=100.0, ask=100.0, spread=0.0)
    intent = Intent(kind="enter_long", symbol="X", qty=1.0, sl_points=1.0, tp_points=2.0, tag="T")
    r1 = chain.execute(intent, mkt, acct)
    r2 = chain.execute(intent, mkt, acct)
    assert r1.fill_price == r2.fill_price
    assert r1.commission == r2.commission
