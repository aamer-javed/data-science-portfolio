"""Configuration objects for the robotic warehouse simulation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any


@dataclass(frozen=True)
class WarehouseConfig:
    """Simulation configuration for one scenario.

    Times are expressed in minutes. Arrival rate is orders per minute.
    """

    sim_minutes: int = 480
    robot_count: int = 24
    station_count: int = 4
    order_arrival_rate_per_minute: float = 0.85
    mean_travel_time_minutes: float = 4.0
    mean_pick_time_minutes: float = 2.2
    mean_dropoff_time_minutes: float = 1.4
    failure_probability_per_task: float = 0.015
    mean_repair_time_minutes: float = 10.0
    charge_after_tasks: int = 14
    mean_charge_time_minutes: float = 12.0
    sla_minutes: float = 30.0
    monitor_interval_minutes: float = 5.0
    seed: int = 42

    def __post_init__(self) -> None:
        if self.sim_minutes <= 0:
            raise ValueError("sim_minutes must be positive.")
        if self.robot_count <= 0:
            raise ValueError("robot_count must be positive.")
        if self.station_count <= 0:
            raise ValueError("station_count must be positive.")
        if self.order_arrival_rate_per_minute <= 0:
            raise ValueError("order_arrival_rate_per_minute must be positive.")
        if not 0 <= self.failure_probability_per_task <= 1:
            raise ValueError("failure_probability_per_task must be between 0 and 1.")
        if self.charge_after_tasks <= 0:
            raise ValueError("charge_after_tasks must be positive.")
        if self.monitor_interval_minutes <= 0:
            raise ValueError("monitor_interval_minutes must be positive.")

    @classmethod
    def from_dict(cls, values: dict[str, Any]) -> "WarehouseConfig":
        """Create a config from a dictionary, ignoring unknown keys."""
        allowed = set(cls.__dataclass_fields__.keys())
        return cls(**{key: value for key, value in values.items() if key in allowed})

    def with_overrides(self, **overrides: Any) -> "WarehouseConfig":
        """Return a new config with selected fields replaced."""
        return replace(self, **overrides)

    def to_dict(self) -> dict[str, Any]:
        """Serialize config to a plain dictionary."""
        return asdict(self)
