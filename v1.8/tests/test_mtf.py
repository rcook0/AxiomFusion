from axiomfusion.parser import parse
from axiomfusion.typecheck import typecheck
from axiomfusion.ir import lower
from axiomfusion.emitters import pine, mql5

def test_series_from_smoke():
    src = '''
input sym:string = "EURUSD"
let h1_close = series_from(sym, "60", "close")
signal up = h1_close > h1_close[-1]

on bar {
  if up { trade.enter_long(qty=0.1, sl_points=200, tp_points=400, tag="MTF") }
}
'''.strip()
    ast = parse(src)
    _, types = typecheck(ast)
    irm = lower(ast, types)
    p = pine.emit(irm)
    m = mql5.emit(irm)
    assert "request.security" in p
    assert "iClose" in m
