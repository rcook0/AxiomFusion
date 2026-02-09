# Type system (v0.1)

## 1. Kinds
- `Scalar<T>` — ordinary values: bool/int/float/string
- `Series<T>` — bar-aligned time series

## 2. Rules (simplified)
### 2.1 Literals
- `true/false`: `bool`
- integer literal: `int`
- decimal literal: `float`
- string literal: `string`

### 2.2 Series identifiers
- `open/high/low/close/volume` are `series<float>`

### 2.3 Operators
We allow standard arithmetic and comparisons with these rules:

- Arithmetic (`+ - * /`):
  - `scalar<float/int>` op `scalar<float/int>` => scalar (promote int->float if needed)
  - `series<num>` op `scalar<num>` => series<num>
  - `scalar<num>` op `series<num>` => series<num>
  - `series<num>` op `series<num>` => series<num>

- Comparisons (`< <= > >= == !=`):
  - same promotion as arithmetic; output is `series<bool>` if any operand is series, else `bool`

- Logic (`and or not`):
  - works on `bool` or `series<bool>` with series-lifting
  - result is `series<bool>` if any operand is series

### 2.4 Indexing
- `series<T>[-k]` (k>0) => `T` (scalar of element at t-k)
- Any non-negative index is a type error in v0.1

### 2.5 Functions
Each builtin declares a signature; the checker enforces it and performs standard numeric promotion.

Examples:
- `ema(series<float>, int|float)` -> `series<float>`
- `cross_over(series<float>, series<float>)` -> `series<bool>`
- `risk_qty(float, float)` -> float

## 3. No implicit lookahead
The parser allows only negative indices syntactically.

