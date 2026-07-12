"""Run scenario experiments and export charts for the warehouse simulation project."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from warehouse_sim.simulation import SimConfig, run_scenarios


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"


def fleet_size_configs() -> list[SimConfig]:
    """Sweep fleet size while keeping demand and station capacity fixed."""
    return [
        SimConfig(scenario_name=f"fleet_{robots}", robot_count=robots, station_count=4, seed=100 + robots)
        for robots in [10, 15, 20, 25, 30, 40]
    ]


def demand_configs() -> list[SimConfig]:
    """Stress-test the same system under higher order demand."""
    return [
        SimConfig(scenario_name="demand_0_70", order_arrival_rate_per_minute=0.70, seed=201),
        SimConfig(scenario_name="demand_0_80_baseline", order_arrival_rate_per_minute=0.80, seed=202),
        SimConfig(scenario_name="demand_1_00", order_arrival_rate_per_minute=1.00, seed=203),
        SimConfig(scenario_name="demand_1_20", order_arrival_rate_per_minute=1.20, seed=204),
        SimConfig(scenario_name="demand_1_40", order_arrival_rate_per_minute=1.40, seed=205),
    ]


def save_chart_throughput_by_fleet(summary: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(summary["robot_count"], summary["throughput_per_hour"], marker="o")
    ax.set_title("Throughput improves then plateaus as fleet size grows")
    ax.set_xlabel("Robot fleet size")
    ax.set_ylabel("Completed orders per hour")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "throughput_by_fleet_size.svg")
    plt.close(fig)


def save_chart_demand_stress(summary: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(summary["arrival_rate_per_minute"], summary["avg_cycle_time_minutes"], marker="o", label="Average cycle time")
    ax.plot(summary["arrival_rate_per_minute"], summary["p90_cycle_time_minutes"], marker="o", label="P90 cycle time")
    ax.set_title("Cycle time rises quickly once demand approaches system capacity")
    ax.set_xlabel("Order arrival rate per minute")
    ax.set_ylabel("Cycle time minutes")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "cycle_time_by_demand.svg")
    plt.close(fig)


def save_chart_sla(summary: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(summary["scenario_name"], summary["sla_attainment_rate"] * 100)
    ax.set_title("SLA attainment by operating scenario")
    ax.set_xlabel("Scenario")
    ax.set_ylabel("Orders meeting SLA (%)")
    ax.tick_params(axis="x", rotation=30)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "sla_attainment_by_scenario.svg")
    plt.close(fig)


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    orders, queues, base_summary = run_scenarios()
    _, _, fleet_summary = run_scenarios(fleet_size_configs())
    _, _, demand_summary = run_scenarios(demand_configs())

    orders.to_csv(REPORTS_DIR / "order_level_results.csv", index=False)
    queues.to_csv(REPORTS_DIR / "queue_time_series.csv", index=False)
    base_summary.to_csv(REPORTS_DIR / "scenario_summary.csv", index=False)
    fleet_summary.to_csv(REPORTS_DIR / "fleet_size_sweep.csv", index=False)
    demand_summary.to_csv(REPORTS_DIR / "demand_stress_test.csv", index=False)

    save_chart_throughput_by_fleet(fleet_summary)
    save_chart_demand_stress(demand_summary)
    save_chart_sla(base_summary)

    print("Reports written to", REPORTS_DIR)


if __name__ == "__main__":
    main()
