# AxiomFusion language mini-spec (v0.3)

## 1. Purpose
AxiomFusion is a tiny DSL for trading logic that merges:
- **Pine-style series math** (declarative, bar-aligned, pure)
- **MQL-style execution** (event handlers, order placement) via a **separate shell**

Design goal: **portable strategy logic** + **deterministic core** + **minimal grammar**.

---

## 2. Two-layer model

### 2.1 Research Core (pure)
Declares:
- `input` parameters
- `let` bindings (pure expressions)
- `signal` booleans (pure expressions)

Rules:
- No side effects
- No IO
- No access to account state
- Deterministic: same bars + inputs ⇒ same results

### 2.2 Execution Shell (effects + state)
Consists of event handlers:
- `on bar { ... }` (bar-close)
- `on tick { ... }` (tick-level)

The shell may:
- read `signal`s and `let` bindings
- read/write **persistent state** via `state` declarations
- emit **intents** via `trade.*`
- update per-bar tick reducers via `reduce ... using ...`

Core cannot call shell; shell can use core.

---

## 3. Evaluation model

### 3.1 Bar-close (default)
- All `Series<T>` are defined per bar index `t`.
- `on bar` executes once per bar close (the last completed bar).

### 3.2 Tick mode (v0.2)
- `on tick` executes on each tick.
- Tick handlers are allowed to:
  - emit intents (`trade.*`)
  - update reducer fields (`reduce ...`) in state
  - update state (`set ...`)

**Backtest/live parity rule:** tick logic must not create lookahead on bar series.
Tick handlers may reference bar series only at their *latest known* values.

---

## 4. State model (v0.3)

### 4.1 Declaration
```
state Accum v 1 {
  hi: float = 0
  lo: float = 0
  sumVol: float = 0
}
```

- `state` objects are persistent across bars/ticks.
- `v <int>` is a **schema version**. Emitters store it alongside persisted data.
- Fields must be scalar types in v0.3 (no series fields).

### 4.2 Access
- Read: `Accum.hi`
- Write: `set Accum.hi = expr`

### 4.3 Persistence requirements (contract)
- Values must be serializable (numbers/bools/strings).
- When version changes, runtime must either:
  - migrate (future feature), or
  - reset state and log a warning (minimum acceptable behavior).

---

## 5. Tick reducers (v0.2)

A reducer is a disciplined way to aggregate tick observations into a bar-level value.

### 5.1 Syntax
Only inside `on tick`:
```
reduce Accum.hi = bid using max
reduce Accum.lo = bid using min
reduce Accum.sumVol = tick_volume using sum
reduce Accum.last = bid using last
```

### 5.2 Semantics
- Reducers apply per tick, accumulating into the target field.
- On bar transition, the runtime:
  1) finalizes the accumulated values as the “bar summary”
  2) makes them available to `on bar` as ordinary state fields
  3) resets reducer fields to their initial values (as declared in `state`)

This yields a predictable tick→bar mapping without introducing new series semantics.

---

## 6. Types (v0.3)
Primitives:
- `bool`, `int`, `float`, `string`

Series:
- `series<T>`

State fields:
- scalar only in v0.3

---

## 7. Intents (execution requests)
Effects are **intents** only:
- `trade.enter_long(qty, sl_points, tp_points, tag)`
- `trade.enter_short(qty, sl_points, tp_points, tag)`
- `trade.exit(tag)`
- `trade.set_be(tag, be_points)` (optional)
- `trade.trail(tag, trail_points)` (optional)

