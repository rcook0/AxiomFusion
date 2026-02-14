# Execution profiles (v1.6)

Execution profiles are **data**: JSON files that describe broker constraints and “realism” knobs.
They are referenced either via:

- E header: `Execution profile is "RAW_SPREAD".`
- CLI override: `axiomfusionc build --profile RAW_SPREAD ...`

Profiles affect:
- MQL5 emitter parameters (volume rounding, stops level checks, deviation)
- Python runtime/backtest (placeholder in v1.6; wired in v1.8)
- Build artifacts: `profile.json` + report fields

## Schema (JSON)

```json
{
  "name": "RAW_SPREAD",
  "version": "1",
  "broker": {
    "min_lot": 0.01,
    "lot_step": 0.01,
    "max_lot": 100.0,
    "stops_level_points": 30,
    "freeze_level_points": 0,
    "deviation_points": 20
  },
  "costs": {
    "spread_points": 0.0,
    "commission_per_lot_roundturn": 7.0,
    "slippage_points_mean": 0.0,
    "slippage_points_std": 0.0
  },
  "session": {
    "enabled": false,
    "allow_utc_hours": [6,7,8,9,10,11,12,13,14,15,16,17]
  },
  "notes": "optional"
}
```

## Using profiles

Example:
`axiomfusionc build --in strat.e --out out.mq5 --target mql5.ea --profile RAW_SPREAD --artifacts build/art`

Artifacts will contain:
- `profile.json` (effective profile)
- `report.json` includes `profile_name`
