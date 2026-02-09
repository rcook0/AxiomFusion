# Emitters (v0.1 mapping notes)

## Pine emitter (target = pine)
- Inputs -> `input.*` declarations
- `let` bindings -> inline series expressions (or `var` where needed)
- `signal` -> boolean series
- `on bar`:
  - If `trade.*` intents exist, emit `strategy(...)` skeleton and translate intents to `strategy.entry/strategy.close`
  - Otherwise emit `indicator(...)` skeleton
Notes:
- Pine cannot do true broker-side fills; this emitter is for TradingView Strategy or alerts.

## MQL5 emitter (target = mql5)
- Generates a single `.mq5` EA skeleton:
  - `OnInit` sets up handles if needed
  - `OnTick` checks for new bar (v0.1) and then evaluates signals on bar close
- Signals are evaluated via indicator buffers or direct computation.
- `trade.*` intents map to:
  - `CTrade trade; trade.Buy(...); trade.Sell(...);` etc.
  - SL/TP in points mapped to price offsets using `_Point`
Notes:
- v0.1 emits stubs with TODO markers for:
  - `risk_qty` mapping (needs account equity and symbol tick value)
  - robust position tagging (magic number + comment)

## Python emitter (target = python)
- Produces a pandas-based skeleton:
  - DataFrame columns: open/high/low/close/volume
  - Indicator computations as functions (EMA/RSI)
  - Signal series computed into boolean masks
  - Intents emitted into a list of actions for a simple simulator

---

## Execution policy hooks (future)
Emitters should accept a policy block:
- slippage model
- partial fill model
- spread handling
- session / news filters

These are intentionally outside the core language.

