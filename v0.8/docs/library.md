# Standard library (v0.7)

Goal: **power without syntax**.
Everything here is a *pure function*; the DSL remains unchanged.

## Series helpers
- `hl2() -> series<float>`  ( (high+low)/2 )
- `ohlc4() -> series<float>` ( (open+high+low+close)/4 )

## Moving averages
- `sma(src: series<num>, len: scalar<int>) -> series<float>`
- `ema(src: series<num>, len: scalar<int>) -> series<float>`
- `wma(src: series<num>, len: scalar<int>) -> series<float>`

## Range / extrema
- `highest(src: series<num>, len: scalar<int>) -> series<float>`
- `lowest(src: series<num>, len: scalar<int>) -> series<float>`

## Volatility
- `stddev(src: series<num>, len: scalar<int>) -> series<float>`
- Bollinger band helpers:
  - `bb_middle(src, len) -> series<float>` (SMA)
  - `bb_upper(src, len, mult) -> series<float>`
  - `bb_lower(src, len, mult) -> series<float>`

## Momentum
- `roc(src: series<num>, len: scalar<int>) -> series<float>` (rate of change, percent)

## MACD (implemented as helpers)
- `macd_line(src, fast, slow) -> series<float>`
- `macd_signal(src, fast, slow, signal) -> series<float>`
- `macd_hist(src, fast, slow, signal) -> series<float>`

## Existing (v0.3+)
- `rsi(src, len) -> series<float>`
- `atr(len) -> series<float>`
- `vwap() -> series<float>`
- `cross_over(a: series, b: series) -> series<bool>`
- `cross_under(a: series, b: series) -> series<bool>`
- `abs(x)`, `min(a,b)`, `max(a,b)`, `nz(a,b)`, `risk_qty(risk, sl)`
- `series_from(symbol, tf, field) -> series<float>` (v0.4)

## Portability notes
- Pine maps most of these to `ta.*` and simple formulas.
- MQL5/Python emitters currently treat many as placeholders; v0.8+ can formalize a true series runtime.
