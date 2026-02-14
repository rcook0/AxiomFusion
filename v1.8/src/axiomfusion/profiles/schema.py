from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional, List

class ProfileError(Exception): ...

@dataclass
class BrokerConstraints:
    min_lot: float = 0.01
    lot_step: float = 0.01
    max_lot: float = 100.0
    stops_level_points: int = 0
    freeze_level_points: int = 0
    deviation_points: int = 20

@dataclass
class CostModel:
    spread_points: Optional[float] = None  # if None, "use live/broker"
    commission_per_lot_roundturn: float = 0.0
    slippage_points_mean: float = 0.0
    slippage_points_std: float = 0.0

@dataclass
class SessionFilter:
    enabled: bool = False
    allow_utc_hours: Optional[List[int]] = None  # list of allowed hour-of-day in UTC

@dataclass
class ExecutionProfile:
    name: str
    version: str = "1"
    broker: BrokerConstraints = BrokerConstraints()
    costs: CostModel = CostModel()
    session: SessionFilter = SessionFilter()
    notes: Optional[str] = None

def _req(d: Dict[str, Any], k: str):
    if k not in d:
        raise ProfileError(f"Missing required key: {k}")
    return d[k]

def load_profile_dict(d: Dict[str, Any]) -> ExecutionProfile:
    name = str(_req(d, "name"))
    version = str(d.get("version", "1"))
    broker_d = dict(d.get("broker", {}))
    costs_d = dict(d.get("costs", {}))
    sess_d = dict(d.get("session", {}))

    broker = BrokerConstraints(
        min_lot=float(broker_d.get("min_lot", 0.01)),
        lot_step=float(broker_d.get("lot_step", 0.01)),
        max_lot=float(broker_d.get("max_lot", 100.0)),
        stops_level_points=int(broker_d.get("stops_level_points", 0)),
        freeze_level_points=int(broker_d.get("freeze_level_points", 0)),
        deviation_points=int(broker_d.get("deviation_points", 20)),
    )
    costs = CostModel(
        spread_points=(None if "spread_points" not in costs_d else float(costs_d["spread_points"])),
        commission_per_lot_roundturn=float(costs_d.get("commission_per_lot_roundturn", 0.0)),
        slippage_points_mean=float(costs_d.get("slippage_points_mean", 0.0)),
        slippage_points_std=float(costs_d.get("slippage_points_std", 0.0)),
    )
    session = SessionFilter(
        enabled=bool(sess_d.get("enabled", False)),
        allow_utc_hours=(None if "allow_utc_hours" not in sess_d else [int(x) for x in sess_d["allow_utc_hours"]]),
    )
    # basic validation
    if broker.min_lot <= 0 or broker.lot_step <= 0 or broker.max_lot <= 0:
        raise ProfileError("Invalid broker lot constraints")
    if broker.min_lot > broker.max_lot:
        raise ProfileError("min_lot > max_lot")
    if costs.commission_per_lot_roundturn < 0:
        raise ProfileError("commission_per_lot_roundturn < 0")
    if session.allow_utc_hours is not None:
        for h in session.allow_utc_hours:
            if h < 0 or h > 23:
                raise ProfileError("allow_utc_hours must be 0..23")

    return ExecutionProfile(
        name=name,
        version=version,
        broker=broker,
        costs=costs,
        session=session,
        notes=d.get("notes"),
    )

def to_jsonable(p: ExecutionProfile) -> Dict[str, Any]:
    return {
        "name": p.name,
        "version": p.version,
        "broker": {
            "min_lot": p.broker.min_lot,
            "lot_step": p.broker.lot_step,
            "max_lot": p.broker.max_lot,
            "stops_level_points": p.broker.stops_level_points,
            "freeze_level_points": p.broker.freeze_level_points,
            "deviation_points": p.broker.deviation_points,
        },
        "costs": {
            **({} if p.costs.spread_points is None else {"spread_points": p.costs.spread_points}),
            "commission_per_lot_roundturn": p.costs.commission_per_lot_roundturn,
            "slippage_points_mean": p.costs.slippage_points_mean,
            "slippage_points_std": p.costs.slippage_points_std,
        },
        "session": {
            "enabled": p.session.enabled,
            **({} if p.session.allow_utc_hours is None else {"allow_utc_hours": p.session.allow_utc_hours}),
        },
        **({} if p.notes is None else {"notes": p.notes}),
    }
