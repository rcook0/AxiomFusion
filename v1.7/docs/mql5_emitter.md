# MQ5 emitter upgrade (v1.7)

v1.7 turns the MQL5 output into a *deployable EA* instead of a skeleton.

## Key guarantees
- Tags map to a deterministic `MagicNumber` and a comment marker `AF:<tag>`.
- Trade intents operate per-symbol and per-tag.
- Volume is normalized to broker constraints (min/max/step).
- SL/TP are distance-checked vs `SYMBOL_TRADE_STOPS_LEVEL` (and best-effort freeze handling).
- Order ops are retried with delay.
- Optional trace logging to a CSV-like file.

## Inputs emitted into EA
- `AF_SlippagePoints`
- `AF_Retries`
- `AF_RetryDelayMs`
- `AF_MaxSpreadPoints` (0 disables)
- `AF_Trace` (bool)
- `AF_TraceFile` (string)

## Limitations
- True account-type aware netting/hedging nuances are best-effort: we query existing positions and manage by magic+comment.
- MTF series uses iOpen/iHigh/iLow/iClose with shift=1 for closed bars; non-literal tf/field falls back to `_Period`/`iClose`.
