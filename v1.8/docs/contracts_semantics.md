# Semantic contracts (v1.5)

Capabilities answer: **what APIs you touch**.  
Semantic contracts answer: **what execution semantics you assume**.

## Target semantics fields

- `supports_tick` (bool): can strategy execute on each tick?
- `supports_mtf` (bool): can strategy request other TF/symbol series?
- `mtf_alignment` (`bar_close`|`any`): guarantees about alignment.
- `supports_history_index` (bool): supports `x[-1]`-style indexing.
- `state_persistence` (`bar`|`session`|`restart`|`none`): persistence class.
- `trade_model` (`intents_only`|`orders`): whether target can express true orders.
- `account_model` (`netting`|`hedging`|`unknown`)

## Error codes

- `ESEM001` tick unsupported
- `ESEM002` MTF unsupported
- `ESEM003` MTF alignment unsupported
- `ESEM004` history indexing unsupported
- `ESEM005` state unsupported

## Inference (v1.5)

Inference is intentionally conservative and text-based:
- `on tick` / `On each tick` => needs tick
- `series_from(` / `timeframe` => needs MTF
- `[... ]` indexing => needs history indexing
- `state` / `reduce` => needs state

v1.6+ upgrades inference to AST/IR-driven with exact node spans and provenance.
