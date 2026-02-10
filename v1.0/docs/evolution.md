# Scope for evolution (v0.5)

## Near-term (v0.6–v0.8)
- **Policy profiles**: named configs (e.g. `ICMarkets_RAW`, `FTMO_Challenge`) with per-symbol overrides.
- **Symbol metadata registry**: pip size, tick size, contract size, margin calc mode, min lot, lot step, stops level.
- **Partial fills + requotes**: a fill policy that can split intents into multiple fills or reject/requote based on liquidity.
- **Position lifecycle**: SL/TP simulation and trailing stops (as policies or as an execution sub-engine).
- **News filter policy**: pluggable calendar source (CSV, web API, broker feed).

## Mid-term (v0.9–v1.2)
- **Deterministic event loop**: ticks + bars + timers unified under a single scheduler with seeded RNG.
- **Broker adapters**: MT5, cTrader, FIX simulators, crypto venues with a shared policy interface.
- **Portfolio support**: multi-symbol positions, cross-margin, correlation-aware risk policies.
- **Replay fidelity**: spread + slippage models based on microstructure proxies (tick volume, range, session regime).

## Long-term
- Formal verification of policy chains (invariants: no negative equity, stops respected, etc.)
- Compilation to a compact bytecode for embedded runtimes (fast backtests)

## Sandbox hardening (v0.6+)
- hierarchical limits (per symbol/per tag)
- exposure in notional terms (qty * contract_size * price)
- kill switch on drawdown / volatility regime
