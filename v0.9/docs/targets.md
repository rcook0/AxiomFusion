# Compilation targets (v0.8)

Targets specify:
- emitter backend
- capability allowlist (default)
- feature switches (e.g. Pine indicator vs strategy)
- formatting and codegen options

## Built-in targets
- `pine.indicator`
- `pine.strategy`
- `mql5.ea`
- `python.backtest`

## CLI
`axiomfusionc compile --target pine.strategy --opt O2 --in strategy.axf --out out.pine`

Capability gating:
- `--allow trade,tick,state,mtf`
- `--strict` (default): fail if required caps are not allowed

The compiler reports:
- required capabilities
- chosen opt level
- target configuration
