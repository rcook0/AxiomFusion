from axiomfusion.parser import parse
from axiomfusion.typecheck import typecheck
from axiomfusion.ir import lower
from axiomfusion.emitters import pine

def test_new_builtins_compile_and_emit_pine():
    src = '''
let x = hl2()
let y = ohlc4()
let hi = highest(close, 20)
let lo = lowest(close, 20)
let w = wma(close, 14)
let sd = stddev(close, 20)
let up = bb_upper(close, 20, 2)
let dn = bb_lower(close, 20, 2)
let r = roc(close, 10)
let m = macd_line(close, 12, 26)
let s = macd_signal(close, 12, 26, 9)
let h = macd_hist(close, 12, 26, 9)
signal ok = cross_over(w, ema(close, 20))
on bar { if ok { trade.enter_long(qty=0.1, sl_points=1, tp_points=2, tag="L") } }
'''.strip()
    ast = parse(src)
    _, types = typecheck(ast)
    irm = lower(ast, types)
    out = pine.emit(irm)
    assert "ta.highest" in out
    assert "ta.lowest" in out
    assert "ta.wma" in out
    assert "ta.stdev" in out
    assert "ta.roc" in out
    assert "ta.ema" in out
