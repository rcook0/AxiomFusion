# Lexicon: reserved words and builtins (v0.3)

## Reserved words
- Declarations: `input`, `let`, `signal`, `state`, `v`, `on`, `bar`, `tick`
- Control: `if`
- Shell: `set`, `reduce`, `using`
- Reducer ops: `sum`, `min`, `max`, `last`
- Logic: `and`, `or`, `not`, `true`, `false`
- Types: `bool`, `int`, `float`, `string`, `series`

## Namespaces
- `trade.*` — execution intents (effects)

## Builtins
Bar series: `open`, `high`, `low`, `close`, `volume` (`series<float>`)

Tick vars (only in `on tick`):
- `bid`, `ask`, `last`, `tick_volume` (`float`)

Pure core functions: `sma`, `ema`, `rsi`, `atr`, `vwap`, `cross_over`, `cross_under`, `abs`, `min`, `max`, `nz`, `risk_qty`.

