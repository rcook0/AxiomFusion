# Production-grade portability contracts (v1.0)

AxiomFusion’s core goal is **write once, target many**.  
v1.0 makes that enforceable with **portability contracts**.

## 1. What is a contract?
A contract is a machine-readable statement of what a target supports:
- capabilities (`trade`, `tick`, `state`, `mtf`)
- semantic features (tick frequency, series history, MTF alignment policy, order semantics)
- codegen promises (naming, deterministic output, required scaffolding)
- compliance tests (fixtures + required outputs/patterns)

The compiler validates:
1) strategy **capabilities** ⊆ target allowed
2) strategy **semantic requirements** ⊆ target supported semantics
3) emitted code passes **conformance checks** (static)

## 2. Contract layers
### 2.1 Capability layer (coarse)
- what features are required by the program

### 2.2 Semantics layer (fine)
Examples:
- `on tick` requires a tick-event loop (Pine does not)
- `state` requires persistence semantics:
  - Pine: `var` is persistent across bars but not across reloads
  - MT5: in-memory unless persisted (file/global vars)
- `mtf` requires a defined bar alignment policy (bar-close aligned)

### 2.3 Execution layer
Trade intents are pure; execution is a target-specific policy system.
Contracts describe what the target runtime promises:
- market vs pending orders
- partial fills (not in v1.0)
- SL/TP semantics (placeholder in emitters)

## 3. Built-in target contracts
- `pine.indicator` (no trade, no tick)
- `pine.strategy` (trade allowed; still no tick)
- `mql5.ea` (trade+tick supported)
- `python.backtest` (trade+tick supported; policy sandbox present)

## 4. Conformance suite
Fixtures are stored in `fixtures/`:
- `.axf` source
- expected capabilities
- expected target support outcome
- optional golden outputs (or pattern assertions)

Run:
- `pytest`
- `axiomfusionc validate --target pine.strategy --in fixtures/basic.axf`

## 5. What “production-grade” means here
- Explicit, versioned contracts
- Fast-fail validation
- Deterministic compilation outputs (stable ordering)
- Testable promises rather than folklore
