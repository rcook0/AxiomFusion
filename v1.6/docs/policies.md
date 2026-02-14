# Execution policies (v0.5)

In AxiomFusion, the **core language stays pure**: it only emits *trade intents* like:
- `trade.enter_long(qty, sl_points, tp_points, tag)`
- `trade.exit(tag)`

**Realism lives in the execution layer** via **pluggable policies**.

## 1. Why policies?
Different venues and brokers behave differently:
- spread widens, slippage changes with volatility
- commissions vary by symbol/account
- margin + stop-out rules constrain order sizing
- sessions/news impose “no-trade” windows
- partial fills / requotes exist in some contexts

Rather than hardcoding this into the DSL (gross), v0.5 provides a **policy chain** that can be:
- swapped per broker / backtest profile
- unit tested independently
- reused across MQL5 / Python / future cTrader emitters

## 2. Policy chain model
A policy gets called in a pipeline:

1) **Pre-trade veto / transform**
   - session filter, news filter, max positions, throttles

2) **Pricing**
   - spread model -> bid/ask from mid
   - slippage model -> executed price from bid/ask + slip

3) **Costs**
   - commission, swap/financing (future), fees

4) **Risk / constraints**
   - margin check
   - min/max lot, lot step, stops level (broker constraints)

5) **Fill model**
   - immediate fill (market), partial fill (future), reject/requote

Policies are composed into an `ExecutionPolicyChain`.

## 3. Contracts

### 3.1 Data structures
- `Intent`: what the strategy requests (direction, qty, tag, sl/tp)
- `MarketSnapshot`: market info at decision time (mid, bid/ask, spread, time, symbol)
- `ExecutionResult`: fill or rejection with details
- `Account`: equity/balance/free margin, positions

### 3.2 Determinism rule
Given the same:
- bar/tick stream
- intent stream
- policy configuration
the policy chain should be deterministic (unless explicitly using RNG with a seeded stream).

## 4. Built-in policies (starter set)
- `SessionFilterPolicy` (allow trading only during windows)
- `SpreadModelPolicy` (fixed / percentage / ATR-based)
- `SlippagePolicy` (fixed points / volatility-based)
- `CommissionPolicy` (per-lot + per-side)
- `MarginPolicy` (simple leverage-based margin requirement)
- `StopsLevelPolicy` (enforce min SL/TP distance)
- `FillPolicyMarket` (accept or reject; fill at computed price)

## 5. Emitters
- **Python runtime** ships a usable policy chain + backtest harness.
- **MQL5 emitter** remains a skeleton; the policy concept maps to EA inputs + helper classes.
