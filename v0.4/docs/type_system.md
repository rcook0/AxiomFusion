# Type system (v0.3)

- Scalars: bool/int/float/string
- Series: series<T>
- State fields: scalar only (v0.3)

Member access:
- `State.field` has the declared scalar type.

Statements:
- `set State.field = expr` requires assignable type.
- `reduce State.field = expr using op` allowed only in `on tick`, with numeric scalar field + numeric expr.

Tick vars:
- `bid/ask/last/tick_volume` only available inside `on tick`.
