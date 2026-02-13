from pathlib import Path
from axiomfusion.contracts.validate import validate_source_for_target

def test_pine_strategy_accepts_basic():
    src = Path("fixtures/basic_macd.axf").read_text(encoding="utf-8")
    res = validate_source_for_target(src, "pine.strategy")
    assert res.ok, res.errors

def test_pine_rejects_tick():
    src = Path("fixtures/tick_required.axf").read_text(encoding="utf-8")
    res = validate_source_for_target(src, "pine.strategy")
    assert not res.ok
    assert any("hard-denies" in e or "does not allow" in e for e in res.errors)

def test_mql5_accepts_tick():
    src = Path("fixtures/tick_required.axf").read_text(encoding="utf-8")
    res = validate_source_for_target(src, "mql5.ea")
    assert res.ok, res.errors
