from pathlib import Path
from axiomfusion.pipeline import build_source, BuildOptions

def test_map_artifact_structure(tmp_path):
    src = Path("fixtures/basic_macd.e").read_text(encoding="utf-8")
    out = tmp_path/"out.pine"
    art = tmp_path/"artifacts"
    build_source("e", src, out=str(out), artifacts_dir=str(art), opts=BuildOptions(opt="O2"))
    m = (art/"map.json").read_text(encoding="utf-8")
    assert '"nodes"' in m
    assert '"provenance"' in m
    assert '"emitted_map"' in m
