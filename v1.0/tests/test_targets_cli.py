from axiomfusion.compiler import compile_to_target

def test_target_indicator_forces_no_strategy():
    src = '''
signal s = true
on bar { if s { trade.enter_long(qty=0.1, sl_points=1, tp_points=2, tag="T") } }
'''.strip()
    rep = compile_to_target(src, "pine.indicator", opt="O0", allow_caps={"state","mtf"}, strict=False)
    assert "indicator(" in rep.emitted
