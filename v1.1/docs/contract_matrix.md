# Target support matrix (v1.0)

This is the human-readable view of `axiomfusion/contracts/targets.json`.

| Target | trade | tick | state | mtf | Notes |
|---|---:|---:|---:|---:|---|
| pine.indicator | ✗ | ✗ | ✓ | ✓ | Pine indicators: no `strategy.*`, no tick loop |
| pine.strategy | ✓ | ✗ | ✓ | ✓ | Pine strategies: bar-based only |
| mql5.ea | ✓ | ✓ | ✓ | ✓ | EA skeleton: tick+bar loop |
| python.backtest | ✓ | ✓ | ✓ | ✓ | Deterministic policy+Sandbox backtest runner |

Semantics notes:
- `tick` is **hard unsupported** on Pine targets.
- `state` persistence across restarts is not guaranteed anywhere yet (requires target-specific persistence).
- `mtf` alignment is bar-close aligned by contract.
