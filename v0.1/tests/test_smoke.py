from axiomfusion.parser import parse
from axiomfusion.typecheck import typecheck
from axiomfusion.ir import lower
from axiomfusion.emitters import pine, mql5, python_rt

def test_smoke_compile():
    src = '''
input fast:int = 20
input slow:int = 50
let f = ema(close, fast)
let s = ema(close, slow)
signal long = cross_over(f, s)
on bar { if long { trade.enter_long(qty=0.1, sl_points=300, tp_points=600, tag="L") } }
'''.strip()
    ast = parse(src)
    _, types = typecheck(ast)
    irm = lower(ast, types)
    assert "trade" in irm.capabilities
    assert "strategy" in pine.emit(irm)
    assert "OnTick" in mql5.emit(irm)
    assert "pandas" in python_rt.emit(irm)
