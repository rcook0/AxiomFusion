# Source maps + provenance (v1.4)

`map.json` is emitted by `axiomfusionc build --artifacts DIR`.

Keys:
- `version`
- `source_sha1`
- `nodes[]`: `{id, kind, span{start,end}, loc{start{line,col}, end{line,col}}}`
- `provenance.edges[]`: `{pass, src, dst, note}`
- `emitted_map.first_symbol_line`: `{symbol: first_line}` (heuristic)

Notes:
- v1.4 spans are **best-effort** (name-based tagging). v1.5 upgrades to true spans.
- Emitted mapping is heuristic (first occurrence).
