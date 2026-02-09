# Lexicon: reserved words and builtins (v0.1)

## Reserved words (tiny set)
- Declarations: `input`, `let`, `signal`, `on`, `bar`
- Control: `if`
- Logic: `and`, `or`, `not`, `true`, `false`
- Types: `bool`, `int`, `float`, `string`, `series`

## Reserved namespaces
- `trade.*` — execution intents (effects)

## Builtin series identifiers
These are treated as predefined `series<float>`:
- `open`, `high`, `low`, `close`, `volume`

## Builtin functions (pure core)
All functions are pure and return `series<T>` unless otherwise noted.

### Technical indicators
- `sma(x, n)`
- `ema(x, n)`
- `rsi(x, n)`
- `atr(n)`              # uses (high,low,close) implicitly
- `vwap()`              # uses (typical price, volume) implicitly in v0.1 spec

### Signal helpers
- `cross_over(a,b)`     -> series<bool>
- `cross_under(a,b)`    -> series<bool>

### Math
- `abs(x)`, `min(a,b)`, `max(a,b)`
- `nz(x, fallback)`     # replace NaN/undefined with fallback

### Risk helper (pure)
- `risk_qty(risk_frac, sl_points)` -> float
  Interpreted as: position sizing in lots given risk fraction of equity and SL distance.
  (Target-specific mapping is in docs/emitters.md; v0.1 emitter stubs.)

## Builtin trade intents (effects)
- `trade.enter_long(qty, sl_points, tp_points, tag)`
- `trade.enter_short(qty, sl_points, tp_points, tag)`
- `trade.exit(tag)`
- `trade.set_be(tag, be_points)`   # optional
- `trade.trail(tag, trail_points)` # optional

