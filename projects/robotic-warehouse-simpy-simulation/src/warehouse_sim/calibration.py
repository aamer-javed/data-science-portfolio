"""Calibration helpers for fitting simulation inputs from event logs.

The functions in this module accept public-safe, Kaggle-style dataframes. They are
small on purpose: the goal is to show the interface between historical operating
KPIs and simulation parameters without requiring private warehouse data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from warehouse_sim.config import WarehouseConfig


@dataclass(frozen=True)
class CalibrationReport:
    """Parameter estimates derived from historical or synthetic event data."""

    arrival_rate_per_minute: float
    mean_travel_time_minutes: float
    mean_pick_time_minutes: float
    mean_dropoff_time_minutes: float
    failure_probability_per_task: float
    mean_repair_time_minutes: float

    def to_config_overrides(self) -> dict[str, float]:
        return {
            "order_arrival_rate_per_minute": self.arrival_rate_per_minute,
            "mean_travel_time_minutes": self.mean_travel_time_minutes,
            "mean_pick_time_minutes": self.mean_pick_time_minutes,
            "mean_dropoff_time_minutes": self.mean_dropoff_time_minutes,
            "failure_probability_per_task": self.failure_probability_per_task,
            "mean_repair_time_minutes": self.mean_repair_time_minutes,
        }


def _positive_mean(frame: pd.DataFrame, column: str, fallback: float) -> float:
    if column not in frame.columns:
        return fallback
    values = pd.to_numeric(frame[column], errors="coerce")
    values = values[values > 0]
    if values.empty:
        return fallback
    return float(values.mean())


def estimate_arrival_rate(events: pd.DataFrame, timestamp_col: str = "created_at") -> float:
    """Estimate average order arrival rate from timestamped order events."""
    if timestamp_col not in events.columns or len(events) < 2:
        return WarehouseConfig().order_arrival_rate_per_minute

    timestamps = pd.to_numeric(events[timestamp_col], errors="coerce").dropna().sort_values()
    if len(timestamps) < 2:
        return WarehouseConfig().order_arrival_rate_per_minute

    duration = float(timestamps.max() - timestamps.min())
    if duration <= 0:
        return WarehouseConfig().order_arrival_rate_per_minute
    return float((len(timestamps) - 1) / duration)


def calibrate_from_event_log(events: pd.DataFrame, base_config: WarehouseConfig | None = None) -> CalibrationReport:
    """Fit simple simulation parameter estimates from order-level event data.

    Expected optional columns: created_at, travel_time_minutes,
    pick_time_minutes, dropoff_time_minutes, repair_time_minutes, robot_failed.
    Missing columns fall back to the base configuration.
    """
    base = base_config or WarehouseConfig()
    failure_rate = base.failure_probability_per_task
    if "robot_failed" in events.columns and not events.empty:
        failure_rate = float(pd.Series(events["robot_failed"]).astype(bool).mean())

    return CalibrationReport(
        arrival_rate_per_minute=estimate_arrival_rate(events),
        mean_travel_time_minutes=_positive_mean(events, "travel_time_minutes", base.mean_travel_time_minutes),
        mean_pick_time_minutes=_positive_mean(events, "pick_time_minutes", base.mean_pick_time_minutes),
        mean_dropoff_time_minutes=_positive_mean(events, "dropoff_time_minutes", base.mean_dropoff_time_minutes),
        failure_probability_per_task=failure_rate,
        mean_repair_time_minutes=_positive_mean(events, "repair_time_minutes", base.mean_repair_time_minutes),
    )


def apply_calibration(base_config: WarehouseConfig, events: pd.DataFrame, scenario_id: str = "calibrated") -> WarehouseConfig:
    """Return a new simulation config using fitted parameter estimates."""
    report = calibrate_from_event_log(events, base_config)
    return base_config.with_overrides(scenario_id=scenario_id, **report.to_config_overrides())


def compare_to_historical_kpis(simulated_summary: pd.DataFrame, historical_kpis: pd.DataFrame) -> pd.DataFrame:
    """Compare simulated KPI outputs to historical KPI targets.

    Both dataframes should contain scenario_id plus one or more shared numeric KPI
    columns. The output includes signed and absolute error for each shared metric.
    """
    if "scenario_id" not in simulated_summary.columns or "scenario_id" not in historical_kpis.columns:
        raise ValueError("Both dataframes must contain scenario_id")

    shared = [
        col
        for col in simulated_summary.columns
        if col in historical_kpis.columns and col != "scenario_id" and pd.api.types.is_numeric_dtype(simulated_summary[col])
    ]
    merged = simulated_summary[["scenario_id", *shared]].merge(
        historical_kpis[["scenario_id", *shared]], on="scenario_id", suffixes=("_simulated", "_historical")
    )

    rows: list[dict[str, Any]] = []
    for _, row in merged.iterrows():
        for metric in shared:
            simulated = float(row[f"{metric}_simulated"])
            historical = float(row[f"{metric}_historical"])
            rows.append(
                {
                    "scenario_id": row["scenario_id"],
                    "metric": metric,
                    "simulated": simulated,
                    "historical": historical,
                    "error": simulated - historical,
                    "absolute_error": abs(simulated - historical),
                }
            )
    return pd.DataFrame(rows)
