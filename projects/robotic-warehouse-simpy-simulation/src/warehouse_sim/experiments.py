"""Experiment runner for the robotic warehouse DES project.

Running this module regenerates the committed CSV outputs and SVG figures:

    python -m warehouse_sim.experiments

The experiment suite is deliberately deterministic. Each scenario has its own
seed so results are reproducible and reviewable in a pull request.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import pandas as pd

from warehouse_sim.config import WarehouseConfig
from warehouse_sim.simulation import run_scenarios, scenario_catalog

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

SUMMARY_COLUMNS = [
    "scenario_id",
    "replication",
    "robot_count",
    "station_count",
    "arrival_rate_per_minute",
    "generated_orders",
    "completed_orders",
    "orders_left_in_queue",
    "throughput_per_hour",
    "avg_cycle_time_minutes",
    "p50_cycle_time_minutes",
    "p90_cycle_time_minutes",
    "avg_queue_wait_minutes",
    "avg_station_wait_minutes",
    "robot_utilization",
    "station_utilization",
    "sla_attainment_rate",
    "failure_rate",
    "charge_time_total_minutes",
    "bottleneck_classification",
]


def fleet_size_configs() -> list[WarehouseConfig]:
    """Sweep fleet size while holding demand and station capacity constant."""
    base = WarehouseConfig(scenario_id="fleet_sweep_base", order_arrival_rate_per_minute=0.85)
    return [
        base.with_overrides(scenario_id=f"fleet_{robots}", robot_count=robots, seed=100 + robots)
        for robots in [12, 16, 20, 24, 28, 32, 40]
    ]


def demand_stress_configs() -> list[WarehouseConfig]:
    """Stress-test a fixed system under increasing order demand."""
    base = WarehouseConfig(robot_count=24, station_count=4)
    rates = [0.65, 0.85, 1.05, 1.25, 1.45]
    return [
        base.with_overrides(
            scenario_id=f"demand_{str(rate).replace('.', '_')}",
            order_arrival_rate_per_minute=rate,
            seed=200 + idx,
        )
        for idx, rate in enumerate(rates, start=1)
    ]


def replication_configs(
    configs: Iterable[WarehouseConfig], replications: int = 5
) -> list[WarehouseConfig]:
    """Expand scenarios across replications for more stable summary statistics."""
    expanded: list[WarehouseConfig] = []
    for config in configs:
        for replication in range(replications):
            expanded.append(config.with_overrides(replication=replication, seed=config.seed + replication * 1_000))
    return expanded


def aggregate_replications(summary: pd.DataFrame) -> pd.DataFrame:
    """Aggregate replicated scenario results for executive reporting."""
    numeric_cols = summary.select_dtypes(include="number").columns.tolist()
    numeric_cols = [col for col in numeric_cols if col != "replication"]
    grouped = summary.groupby("scenario_id", as_index=False)[numeric_cols].mean()

    bottlenecks = (
        summary.groupby("scenario_id")["bottleneck_classification"]
        .agg(lambda values: values.mode().iloc[0] if not values.mode().empty else values.iloc[0])
        .reset_index()
    )
    return grouped.merge(bottlenecks, on="scenario_id", how="left")


def save_line_chart(
    frame: pd.DataFrame,
    x_col: str,
    y_cols: list[str],
    title: str,
    x_label: str,
    y_label: str,
    output_path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for y_col in y_cols:
        ax.plot(frame[x_col], frame[y_col], marker="o", label=y_col.replace("_", " "))
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.grid(True, alpha=0.25)
    if len(y_cols) > 1:
        ax.legend()
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def save_bar_chart(
    frame: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    x_label: str,
    y_label: str,
    output_path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.bar(frame[x_col], frame[y_col])
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.tick_params(axis="x", rotation=25)
    ax.grid(True, axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def save_queue_chart(monitors: pd.DataFrame, output_path: Path) -> None:
    selected = monitors[monitors["scenario_id"].isin(["baseline", "demand_plus_50pct"])]
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for scenario_id, group in selected.groupby("scenario_id"):
        queue_by_time = group.groupby("timestamp_minutes", as_index=False)["queue_length"].mean()
        ax.plot(queue_by_time["timestamp_minutes"], queue_by_time["queue_length"], label=scenario_id)
    ax.set_title("Queue growth exposes demand stress before throughput fails")
    ax.set_xlabel("Simulation minute")
    ax.set_ylabel("Average order queue length")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def run_experiment_suite(output_dir: Path = REPORTS_DIR) -> dict[str, pd.DataFrame]:
    """Run the standard experiment suite and write outputs to disk."""
    figures_dir = output_dir / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    orders, monitors, scenario_summary_raw = run_scenarios(replication_configs(scenario_catalog(), 5))
    scenario_summary = aggregate_replications(scenario_summary_raw)

    _, _, fleet_raw = run_scenarios(replication_configs(fleet_size_configs(), 5))
    fleet_summary = aggregate_replications(fleet_raw).sort_values("robot_count")

    _, _, demand_raw = run_scenarios(replication_configs(demand_stress_configs(), 5))
    demand_summary = aggregate_replications(demand_raw).sort_values("arrival_rate_per_minute")

    orders.to_csv(output_dir / "order_level_results.csv", index=False)
    monitors.to_csv(output_dir / "queue_time_series.csv", index=False)
    scenario_summary[SUMMARY_COLUMNS].to_csv(output_dir / "scenario_summary.csv", index=False)
    fleet_summary[SUMMARY_COLUMNS].to_csv(output_dir / "fleet_size_sweep.csv", index=False)
    demand_summary[SUMMARY_COLUMNS].to_csv(output_dir / "demand_stress_test.csv", index=False)

    save_line_chart(
        fleet_summary,
        x_col="robot_count",
        y_cols=["throughput_per_hour"],
        title="Throughput improves then plateaus as fleet size grows",
        x_label="Robot fleet size",
        y_label="Completed orders per hour",
        output_path=figures_dir / "throughput_by_fleet_size.svg",
    )
    save_line_chart(
        demand_summary,
        x_col="arrival_rate_per_minute",
        y_cols=["avg_cycle_time_minutes", "p90_cycle_time_minutes"],
        title="Cycle time rises nonlinearly as demand approaches capacity",
        x_label="Order arrival rate per minute",
        y_label="Cycle time minutes",
        output_path=figures_dir / "cycle_time_by_demand.svg",
    )
    save_bar_chart(
        scenario_summary.sort_values("sla_attainment_rate", ascending=False),
        x_col="scenario_id",
        y_col="sla_attainment_rate",
        title="SLA attainment by operating scenario",
        x_label="Scenario",
        y_label="Share of completed orders meeting SLA",
        output_path=figures_dir / "sla_attainment_by_scenario.svg",
    )
    save_queue_chart(monitors, figures_dir / "queue_length_time_series.svg")

    return {
        "orders": orders,
        "monitors": monitors,
        "scenario_summary": scenario_summary,
        "fleet_summary": fleet_summary,
        "demand_summary": demand_summary,
    }


def main() -> None:
    outputs = run_experiment_suite()
    print("Wrote simulation reports to", REPORTS_DIR)
    print(outputs["scenario_summary"][SUMMARY_COLUMNS].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
