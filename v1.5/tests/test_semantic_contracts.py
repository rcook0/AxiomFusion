from axiomfusion.contracts.validate import validate_source_for_target

def test_tick_rejected_by_pine():
    src = "on tick {\n  trade.enter_long(qty=0.1, tag=\"T\")\n}\n"
    v = validate_source_for_target(src, "pine.strategy")
    assert not v.ok
    assert any("ESEM001" in e for e in v.errors)

def test_tick_allowed_by_mql5():
    src = "on tick {\n  trade.enter_long(qty=0.1, tag=\"T\")\n}\n"
    v = validate_source_for_target(src, "mql5.ea")
    assert v.ok
