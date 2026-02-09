# AxiomFusion language mini-spec (v0.1)

## 1. Purpose
AxiomFusion is a tiny DSL for trading logic that merges:
- **Pine-style series math** (declarative, bar-aligned, pure)
- **MQL-style execution** (event handlers, order placement) via a **separate shell**

The design goal is: **portable strategy logic** + **deterministic core** + **minimal grammar**.

---

## 2. Two-layer model

### 2.1 Research Core (pure)
The Research Core defines:
- `input` parameters
- `let` bindings (pure expressions)
- `signal` booleans (pure expressions)
- `plot`/`output` (not implemented in v0.1 prototype, but reserved)

Rules:
- No side effects
- No IO
- No access to account state
- Only bar-aligned data (`Series<T>`) and scalars (`T`)
- Deterministic evaluation: same bars + inputs => same results

### 2.2 Execution Shell (effects)
The Execution Shell consists of `on bar { ... }` blocks.
Inside these blocks, you may:
- reference `signal`s and `let` bindings
- emit **intents** via `trade.*` calls (no direct broker calls)

Rule:
- Shell can call Core bindings
- Core cannot call Shell

---

## 3. Evaluation model (v0.1)
- Default mode is **bar-close**.
- All `Series<T>` values are defined per bar index `t`.
- Builtins like `ema(close, 20)` are interpreted as producing a `Series<float>`.

No tick simulation in v0.1.

---

## 4. Data model and types

### 4.1 Primitive types
- `bool`, `int`, `float`, `string`

### 4.2 Domain types (aliases in v0.1 prototype)
In the spec, we treat these as distinct types, but the prototype aliases them to floats/strings:
- `price`, `money`, `lots`, `points`, `pips`

### 4.3 Series
- `series<float>`, `series<bool>`, etc.

### 4.4 Time-series indexing
- `x[-k]` means k bars ago (k>0).
- Lookahead is forbidden: `x[+k]` is invalid.
- `x[0]` is current bar (allowed).

---

## 5. Capabilities (design, not enforced in v0.1)
Scripts may declare:
- `cap trade`
- `cap network`
- `cap fileio`

v0.1 assumes `trade` capability is allowed if the script contains any `trade.*` call.

---

## 6. Intents (execution requests)
The only allowed effects are **intents**. The runtime/broker adapter decides exact execution details.

v0.1 supports:
- `trade.enter_long(qty, sl_points, tp_points, tag)`
- `trade.enter_short(qty, sl_points, tp_points, tag)`
- `trade.exit(tag)` (exit positions matching tag)
- `trade.set_be(tag, be_points)` (optional)
- `trade.trail(tag, trail_points)` (optional)

---

## 7. Minimal language constructs

### 7.1 Inputs
```
input fast:int = 20
input risk:float = 0.01
```

### 7.2 Pure bindings
```
let fastEma = ema(close, fast)
let slowEma = ema(close, slow)
```

### 7.3 Signals
```
signal long = cross_over(fastEma, slowEma)
signal short = cross_under(fastEma, slowEma)
```

### 7.4 Event handler
```
on bar {
  if long { trade.enter_long(qty=risk_qty(risk, 300), sl_points=300, tp_points=600, tag="L") }
  if short { trade.enter_short(qty=risk_qty(risk, 300), sl_points=300, tp_points=600, tag="S") }
}
```

---

## 8. Determinism guarantees
- Core is pure and does not depend on non-series runtime state.
- Shell effects are emitted as intents; execution policy is external.
- A backtester can replay the exact same intents given the same data.

