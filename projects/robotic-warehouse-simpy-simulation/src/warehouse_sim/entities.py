"""Typed records produced by the warehouse simulation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class Order:
    """An inbound warehouse task/order waiting for robot assignment."""

    order_id: int
    created_at: float


@dataclass(frozen=True)
class OrderRecord:
    """Completed order-level event record.

    This is intentionally wide enough to support debugging, KPI aggregation,
    statistical calibration, and downstream visualization without re-running the
    event simulation.
    """

    scenario_id: str
    replication: int
    order_id: int
    robot_id: int
    created_at: float
    started_at: float
    completed_at: float
    queue_wait_minutes: float
    station_wait_minutes: float
    travel_time_minutes: float
    pick_time_minutes: float
    dropoff_time_minutes: float
    repair_time_minutes: float
    charge_time_minutes: float
    cycle_time_minutes: float
    met_sla: bool
    robot_failed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MonitorRecord:
    """Periodic monitoring snapshot for queue and station state."""

    scenario_id: str
    replication: int
    timestamp_minutes: float
    queue_length: int
    station_queue_length: int
    station_users: int
    completed_orders: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SimulationOutputs:
    """Structured output returned by a single simulation run."""

    orders: pd.DataFrame
    monitors: pd.DataFrame
    summary: dict[str, Any]
