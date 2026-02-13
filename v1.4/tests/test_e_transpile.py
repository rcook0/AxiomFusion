from pathlib import Path
from axiomfusion.e_lang import transpile_e
from axiomfusion.contracts.validate import validate_source_for_target

def test_transpile_e_smoke():
    src = Path("fixtures/basic_macd.e").read_text(encoding="utf-8")
    res = transpile_e(src)
    assert "signal LongSignal" in res.axf
    assert res.header.target == "pine.strategy"
    v = validate_source_for_target(res.axf, "pine.strategy")
    assert v.ok, v.errors
