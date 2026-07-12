"""Configuration objects for the robotic warehouse simulation.

The values in this public portfolio project are synthetic. They are selected to
make operational trade-offs visible without representing a proprietary warehouse
layout, private throughput target, or employer-specific system behavior.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any, Literal

AssignmentPolicy = Literal["fifo", "priority_fifo", "nearest_robot", "shortest_queue_priority"]


@dataclass(frozen=True)
class WarehouseConfig:
    """Simulation configuration for one scenario and replication.

    Units:
    - All times are minutes.
    - Order arrival rate is orders per minute.
    - Travel speed is grid cells per minute.
    - Utilization values are calculated over the configured simulation horizon.
    """

    scenario_id: str = "baseline"
    replication: int = 0
    sim_minutes: int = 8 * 60

    # Capacity and demand.
    robot_count: int = 24
    station_count: int = 4
    charging_station_count: int = 4
    order_arrival_rate_per_minute: float = 0.85

    # Layout, routing, and dispatching.
    warehouse_width: int = 40
    warehouse_height: int = 24
    travel_speed_cells_per_minute: float = 12.0
    congestion_factor: float = 0.08
    assignment_policy: AssignmentPolicy = "shortest_queue_priority"

    # Process times.
    mean_pick_time_minutes: float = 2.2
    mean_dropoff_time_minutes: float = 1.4
    failure_probability_per_task: float = 0.015
    mean_repair_time_minutes: float = 10.0
    charge_after_tasks: int = 14
    mean_charge_time_minutes: float = 12.0

    # Priority/SLA logic.
    sla_minutes: float = 30.0
    priority_order_probability: float = 0.12
    priority_sla_multiplier: float = 0.65

    # Monitoring and reproducibility.
    monitor_interval_minutes: float = 5.0
    seed: int = 42

    def __post_init__(self) -> None:
        if not self.scenario_id:
            raise ValueError("scenario_id must be populated.")
        if self.sim_minutes <= 0:
            raise ValueError("sim_minutes must be positive.")
        if self.robot_count <= 0:
            raise ValueError("robot_count must be positive.")
        if self.station_count <= 0:
            raise ValueError("station_count must be positive.")
        if self.charging_station_count <= 0:
            raise ValueError("charging_station_count must be positive.")
        if self.order_arrival_rate_per_minute <= 0:
            raise ValueError("order_arrival_rate_per_minute must be positive.")
        if self.warehouse_width <= 0 or self.warehouse_height <= 0:
            raise ValueError("warehouse dimensions must be positive.")
        if self.travel_speed_cells_per_minute <= 0:
            raise ValueError("travel_speed_cells_per_minute must be positive.")
        if self.congestion_factor < 0:
            raise ValueError("congestion_factor cannot be negative.")
        if self.assignment_policy not in {"fifo", "priority_fifo", "nearest_robot", "shortest_queue_priority"}:
            raise ValueError(
                "assignment_policy must be fifo, priority_fifo, nearest_robot, or shortest_queue_priority."
            )
        if self.mean_pick_time_minutes < 0:
            raise ValueError("mean_pick_time_minutes cannot be negative.")
        if self.mean_dropoff_time_minutes < 0:
            raise ValueError("mean_dropoff_time_minutes cannot be negative.")
        if not 0 <= self.failure_probability_per_task <= 1:
            raise ValueError("failure_probability_per_task must be between 0 and 1.")
        if self.mean_repair_time_minutes < 0:
            raise ValueError("mean_repair_time_minutes cannot be negative.")
        if self.charge_after_tasks <= 0:
            raise ValueError("charge_after_tasks must be positive.")
        if self.mean_charge_time_minutes < 0:
            raise ValueError("mean_charge_time_minutes cannot be negative.")
        if self.sla_minutes <= 0:
            raise ValueError("sla_minutes must be positive.")
        if not 0 <= self.priority_order_probability <= 1:
            raise ValueError("priority_order_probability must be between 0 and 1.")
        if self.priority_sla_multiplier <= 0:
            raise ValueError("priority_sla_multiplier must be positive.")
        if self.monitor_interval_minutes <= 0:
            raise ValueError("monitor_interval_minutes must be positive.")

    @classmethod
    def from_dict(cls, values: dict[str, Any]) -> "WarehouseConfig":
        """Create a config from a dictionary while ignoring unknown keys."""
        allowed = set(cls.__dataclass_fields__.keys())
        return cls(**{key: value for key, value in values.items() if key in allowed})

    def with_overrides(self, **overrides: Any) -> "WarehouseConfig":
        """Return a new config with selected fields replaced."""
        return replace(self, **overrides)

    def to_dict(self) -> dict[str, Any]:
        """Serialize config to a plain dictionary."""
        return asdict(self)
