# IR optimizer (v0.8)

The optimizer operates on **IRModule** and is intentionally conservative to preserve determinism.

## Opt levels
- `O0`: no transforms
- `O1`: constant folding + algebraic simplification
- `O2`: O1 + dead-binding elimination (DCE) + trivial inlining
- `O3`: O2 + common subexpression caching (limited, safe subset)

## Passes
### Constant folding
Folds expressions like `(2 + 3)` and propagates literals into pure contexts.

### Simplification
- `x and true -> x`
- `x and false -> false`
- `x or true -> true`
- `x or false -> x`
- `not(not x) -> x`
- numeric identities: `x + 0 -> x`, `x * 1 -> x`, `x * 0 -> 0`, etc.

### DCE
Removes `let`/`signal` bindings not referenced by any handler statements or other live bindings.

### Trivial inlining
Optionally inlines small `let` bindings used once to reduce emitted code size.

## Safety rules
- No reordering across handlers.
- No introduction of new series history.
- No changes to state writes or trade intents.
