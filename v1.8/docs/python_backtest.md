# Python backtests (v1.8)

Run an AxiomFusion strategy against OHLCV CSV.

CSV must contain columns:
- time (or chosen `--time-col`)
- open, high, low, close, volume

## Example

```bash
axiomfusionc backtest --in fixtures/basic_macd.e --csv data/ohlcv.csv --trace build/trace.jsonl
```

With execution profile realism:

```bash
axiomfusionc backtest --in fixtures/basic_macd.e --csv data/ohlcv.csv --profile RAW_SPREAD --trace build/trace.jsonl
```

Output:
- prints final account snapshot
- optional `--out result.json`
- optional `--trace trace.jsonl` (events: intent/bar)
