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


## v0.4 data access builtins
- `series_from(symbol, tf, field)`

### v0.7 builtins
- `hl2()`, `ohlc4()`
- `wma(series, len)`
- `highest(series, len)`, `lowest(series, len)`
- `stddev(series, len)`
- `bb_middle(series, len)`, `bb_upper(series, len, mult)`, `bb_lower(series, len, mult)`
- `roc(series, len)`
- `macd_line(series, fast, slow)`, `macd_signal(series, fast, slow, signal)`, `macd_hist(series, fast, slow, signal)`
