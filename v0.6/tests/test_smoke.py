from axiomfusion.parser import parse
from axiomfusion.typecheck import typecheck
from axiomfusion.ir import lower
from axiomfusion.emitters import pine, mql5, python_rt

def test_smoke_compile_v03():
    src = '''
state Acc v 1 { hi:float = 0 lo:float = 1e9 }
input fast:int = 20
input slow:int = 50
let f = ema(close, fast)
let s = ema(close, slow)
signal long = cross_over(f, s)

on tick {
  reduce Acc.hi = bid using max
  reduce Acc.lo = bid using min
}

on bar {
  if long { trade.enter_long(qty=0.1, sl_points=300, tp_points=600, tag="L") }
}
'''.strip()
    ast = parse(src)
    _, types = typecheck(ast)
    irm = lower(ast, types)
    out_p = pine.emit(irm)
    out_m = mql5.emit(irm)
    out_py = python_rt.emit(irm)
    assert "on tick not supported" in out_p
    assert "OnTick" in out_m
    assert "state" in out_py
