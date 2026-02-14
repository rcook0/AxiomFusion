# AxiomFusion-E desugaring spec (v1.1)

E is a **surface language** that lowers into the existing `.axf` core syntax.
No new semantics are introduced.

## Definitions
E: `Define fast as the 20-period EMA of close.`
AXF: `let fast = ema(close, 20)`

## Signals
E: `Define LongSignal when fast crosses above slow.`
AXF: `signal LongSignal = cross_over(fast, slow)`

## State (prototype)
E: `Keep state High version 1 starting at 0.`
AXF: `state High v 1 { value:float = 0 }`

## Events
E:
`On each bar,` → `on bar { ... }`
`On each tick,` → `on tick { ... }`

## If blocks
E:
```
    if LongSignal,
        enter long trade ...
```
AXF:
```
  if LongSignal {
    trade.enter_long(...)
  }
```

## Trades
E: `enter long trade with size 0.1 stop 100 points take 200 points tag "L".`
AXF: `trade.enter_long(qty=0.1, sl_points=100, tp_points=200, tag="L")`

E: `exit trade tagged "L".`
AXF: `trade.exit(tag="L")`

## MTF
E: `Define H1Close as close on timeframe 1h of "EURUSD".`
AXF: `let H1Close = series_from("EURUSD", "60", "close")`

## Reducers (prototype)
E: `update High to the maximum of High and bid.`
AXF: `reduce High.value = bid using max`

## Headers
Headers are consumed by the CLI and can guide compilation:
- `Target is ...`
- `Execution profile is ...`
- `Sandbox limits: ...`
