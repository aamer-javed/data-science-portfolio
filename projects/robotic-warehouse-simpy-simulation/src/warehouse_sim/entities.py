"""Typed entities used by the simulation."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Order:
    """An order/task entering the warehouse simulation."""

    order_id: int
    created_at: float


@dataclass(frozen=True)
class OrderRecord:
    """Completed order-level event record."""

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

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class MonitorRecord:
    """Time-series record used for queue and station monitoring."""

    scenario_id: str
    replication: int
    timestamp_minutes: float
    queue_length: int
    station_queue_length: int
    station_users: int
    completed_orders: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
