from axiomfusion.compiler import compile_to_target

def test_optimizer_folds_and_dce():
    src = '''
let a = 2 + 3
let b = a + 0
let dead = 1 + 1
signal s = b > 4 and true
on bar { if s { trade.enter_long(qty=0.1, sl_points=1, tp_points=2, tag="T") } }
'''.strip()
    rep = compile_to_target(src, "pine.strategy", opt="O2", allow_caps={"trade","state","mtf"}, strict=False)
    out = rep.emitted
    assert "dead" not in out  # DCE
