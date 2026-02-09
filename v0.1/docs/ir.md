# IR (Intermediate Representation) v0.1

The IR is intentionally small and target-agnostic.

## 1. Modules
A module contains:
- `inputs: [InputDecl]`
- `bindings: [Binding]`      # let/signal
- `handlers: [Handler]`      # on bar
- `capabilities: set[str]`   # derived from presence of effects

## 2. Expressions
All expressions are pure.

Nodes:
- `Lit(value)`
- `Var(name)`
- `BinOp(op, left, right)`
- `UnOp(op, expr)`
- `Call(name, args)`              # pure core call
- `Index(series_expr, k)`         # history access: k>0
- `IfExpr(cond, then, else)`      # reserved for v0.2, not used in v0.1

Type on each expression after typecheck:
- `Scalar<T>` or `Series<T>`

## 3. Statements (effects allowed only here)
- `IfStmt(cond_expr, [stmt...])`
- `TradeIntent(kind, kwargs)`     # enter_long/enter_short/exit/...

## 4. Lowering pipeline
AST -> Typed AST -> IR

Key transformations:
- Resolve `signal` as `Binding(kind="signal")` producing `series<bool>`
- Enforce effect purity: trade intents can only appear in handlers
- Derive `capabilities` if any `TradeIntent` exists

## 5. Target mapping
- Pine: Core exprs map directly; intents map to `strategy.*` or alerts
- MQL5: Core exprs become buffer computations; intents become `CTrade` calls
- Python: Core exprs become vectorized pandas; intents become simulator API calls

See `docs/emitters.md` for mapping details.

