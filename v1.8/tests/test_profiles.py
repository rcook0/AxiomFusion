from pathlib import Path
import json
from axiomfusion.profiles.registry import load_profile
from axiomfusion.pipeline import build_source, BuildOptions

def test_load_profile_builtin():
    p = load_profile("RAW_SPREAD")
    assert p.name == "RAW_SPREAD"
    assert p.broker.min_lot > 0

def test_profile_artifact_written(tmp_path):
    src = Path("fixtures/basic_macd.e").read_text(encoding="utf-8")
    out = tmp_path/"out.mq5"
    art = tmp_path/"art"
    build_source("e", src, out=str(out), artifacts_dir=str(art), opts=BuildOptions(target="mql5.ea", profile="RAW_SPREAD"))
    pj = json.loads((art/"profile.json").read_text(encoding="utf-8"))
    assert pj["name"] == "RAW_SPREAD"
