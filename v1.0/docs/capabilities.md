# Capabilities (v0.6)

AxiomFusion is intentionally split into:
- **Pure core** (research logic, expressions, series math)
- **Shell** (handlers, state updates, trade intents)

To keep deployments safe and portable, v0.6 introduces **capabilities**:
a small set of flags that describe what a strategy *requires*.

## Capability set
- `trade`  — emits `trade.*` intents (execution)
- `tick`   — uses `on tick { ... }`
- `state`  — declares persistent `state ... v ... { ... }`
- `mtf`    — uses multi-timeframe / multi-symbol data via `series_from(...)`

## Why this matters
- Pine can’t do real tick execution -> disallow `tick` for Pine targets.
- Some brokers/distributions disallow MTF access.
- Some “safe mode” deployments disallow trading entirely (`trade`).

## How it works
- The compiler/IR exposes `IRModule.capabilities`.
- Runtimes enforce an allowlist: required ⊆ allowed.

## Minimal contract
If a strategy requires a capability that is not allowed:
- compilation should fail (or emit a warning, depending on strictness)
- runtime execution must reject the strategy before any effects occur
