# AxiomFusion v0.3 — Pine-like research core + MQL-like execution shell (simplified)

This workspace is a **design + reference implementation skeleton** for a tiny trading DSL that:
- feels like Pine (series-first, declarative, bar-aligned)
- can compile to MQL5-style event handlers (execution shell)
- stays **intentionally small** in grammar and lexicon

It contains three deliverables:
1) **Mini-spec** (semantics, types, capabilities, execution model)
2) **Grammar + lexicon** (EBNF + reserved words + builtins)
3) **IR + emitter plans** (a compact IR and target mapping notes)
Plus: a small Python prototype compiler pipeline (lexer → parser → typecheck → IR → emitters).

> Status: v0.1 is **scope-locked** to bar-close evaluation (no tick microstructure yet).
> The architecture explicitly supports extending to tick-mode later.

---

## Directory layout

- `docs/`
  - `spec.md` — overall language + runtime semantics
  - `grammar.ebnf` — simplified grammar
  - `lexicon.md` — reserved words + builtins (small)
  - `type_system.md` — types, coercions, and rules
  - `ir.md` — IR nodes + lowering strategy
  - `emitters.md` — mapping notes for MQL5 / Pine / Python
- `src/axiomfusion/`
  - `lexer.py` — tokenizer
  - `parser.py` — recursive descent parser (tiny)
  - `ast.py` — AST dataclasses
  - `typecheck.py` — basic type inference/checking
  - `ir.py` — IR dataclasses + lowering
  - `emitters/`
    - `pine.py` — Pine skeleton emitter
    - `mql5.py` — MQL5 skeleton emitter
    - `python_rt.py` — Python/pandas skeleton emitter
  - `cli.py` — `python -m axiomfusion ...`
- `examples/`
  - `ema_cross.axf` — example strategy
  - `vwap_revert.axf` — example signal
- `tests/`
  - `test_smoke.py`

---

## Quick start

### 1) Build IR from an example
```bash
python -m axiomfusion compile examples/ema_cross.axf --target pine --out out/ema_cross.pine
python -m axiomfusion compile examples/ema_cross.axf --target mql5 --out out/EMA_Cross_EA.mq5
python -m axiomfusion compile examples/ema_cross.axf --target python --out out/ema_cross.py
```

### 2) Run the smoke test
```bash
python -m pytest -q
```

---

## Design constraints (why it’s so small)

**Grammar minimization goals**
- Single module file
- Only `input`, `let`, `signal`, `on bar` blocks
- Expressions are purely functional (no assignment inside expressions)
- Side effects are only allowed inside `on bar` via `trade.*` intents

**Trading-systems-first semantics**
- Everything is bar-aligned unless explicitly `series(...)`
- No implicit lookahead; history access only via `x[-k]` (with k>0)
- Execution: signal → intent → broker adapter

---

## Next steps (v0.2+)
- Tick-mode (`on tick`) with reducer model
- Position/state machines (`state { ... }`) with versioned storage
- Capability gating + sandbox policy
- Multi-symbol & multi-timeframe
- Slippage/partial-fill models as pluggable execution policies


## What’s new in v0.2 + v0.3

- `on tick { ... }` handler (v0.2)
- `state Name v <int> { field:type = expr ... }` persistent state with schema versioning (v0.3)
- `set State.field = expr` statement
- `reduce State.field = expr using (sum|min|max|last)` statement for tick reducers (v0.2)
- Member access `State.field` in expressions


## v0.4
- Multi-timeframe + multi-symbol via `series_from(symbol, tf, field)`.

## v0.5
- Execution policies as pluggable modules (fills, spread/slippage, commissions, margin, sessions/news filters).
- Python runtime now includes a policy-driven executor and a minimal backtest harness.

## v0.6
- Capability gating (declare/inspect required capabilities and enforce an allowlist).
- Sandbox runner for intent-rate limits, max exposure, symbol/timeframe allowlists, and safety vetoes.

## v0.7
- Library expansion: more TA/math builtins (highest/lowest, wma, stddev, bbands, roc, macd*), no new syntax.

## v0.8
- IR optimization passes (const fold, simplify, DCE) with opt levels.
- Serious compilation targets: target registry + CLI compiler (`axiomfusionc`).

## v0.9
- Debuggability: source maps, stable node IDs, and trace hooks.
- Compiler can emit a JSON compile report + binding dependency graph.
- Python runtime can produce per-bar traces of selected bindings/signals/intents.

## v1.0
- Production-grade portability contracts: target capability matrices, feature support, and conformance validation.
- Contract-driven compilation: compile fails fast if a program uses unsupported semantics for a target.
- Conformance test suite + golden fixtures.

## v1.1
- E-surface grammar (English-like, context-free) + desugaring spec.
- Minimal E parser/transpiler: `.e` -> core `.axf`.
- CLI: `axiomfusionc transpile-e` and `axiomfusionc compile-e`.

## v1.2
- Full compile pipeline: ingest (.e/.axf), transpile, validate contracts, optimize, emit target code + artifacts.
- New `axiomfusionc build` command.
- Distribution renamed to `axiomfusion-lang` to reduce collision risk; import path remains `axiomfusion`.

## v1.4
- Source maps + provenance: line/col spans, stable node IDs, rewrite edges, and best-effort emitted line mapping.

## v1.6
- Execution profile system: pluggable realism models + broker constraints via JSON profiles.
- CLI `--profile` override; E header `Execution profile is "...".` respected by `build`.
- Artifacts include `profile.json` + report includes effective profile.
