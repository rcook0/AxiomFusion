# Debuggability & traceability (v0.9)

v0.9 aims to make AxiomFusion **auditable**:
- What did the strategy compute?
- Which inputs and bars led to an intent?
- What optimizations changed the emitted shape?

## 1. Stable node IDs
Each AST node and IR node gets an ID:
- deterministic across compiles for identical source (hash-based)
- used in source maps and traces

## 2. Source spans
The lexer tracks token positions; parser attaches spans `(start,end)` to nodes.
(For this prototype: spans are best-effort; line/col mapping is provided.)

## 3. Source map (compile artifact)
Compiler can emit:
- `out.code` (target source)
- `out.map.json` mapping IR node IDs -> source spans and (optionally) emitted line ranges
- `out.report.json` compile report (caps, opt level, target, warnings)

## 4. Dependency graph
Bindings form a DAG. Compiler can output `out.deps.dot` for visualization.

## 5. Runtime traces (Python)
Backtest runner can trace:
- selected binding/signal values by name
- emitted intents + sandbox/policy decisions

Output options:
- JSONL trace stream
- in-memory list for tests

## 6. Philosophy
- Tracing is **opt-in**
- Keep the core pure; tracing belongs to runtime/compile artifacts, not language semantics
