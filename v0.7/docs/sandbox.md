# Sandbox (v0.6)

The sandbox is an **intent boundary firewall**.

It does not try to prove a strategy is “good”.
It enforces that a strategy is **bounded**.

## What the sandbox can enforce
- Max intents per bar / per minute
- Max open positions
- Max order size (`qty`)
- Symbol allowlist (and optional tf allowlist for MTF usage)
- Disable certain intent types (e.g. allow `exit` but no `enter_*`)
- Optional “kill switch” callback

## Where it lives
- Python runtime: implemented now (`axiomfusion.sandbox`)
- MQL5 / cTrader: concept maps to EA inputs + checks before order placement

## Determinism
Sandbox decisions must be deterministic under the same inputs (unless using seeded RNG).
