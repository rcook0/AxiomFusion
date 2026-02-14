from pathlib import Path
from axiomfusion.pipeline import build_source, BuildOptions

def test_mql5_emitter_contains_helpers():
    src = Path("fixtures/basic_macd.e").read_text(encoding="utf-8")
    res = build_source("e", src, opts=BuildOptions(target="mql5.ea", opt="O2"))
    out = res.emitted
    assert "AF_Magic" in out
    assert "AF_NormalizeLots" in out
    assert "AF_FindPosition" in out
    assert "trade.Buy" in out or "trade.Sell" in out
