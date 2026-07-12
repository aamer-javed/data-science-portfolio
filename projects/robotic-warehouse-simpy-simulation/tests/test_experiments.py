from pathlib import Path

import pandas as pd

from warehouse_sim.config import WarehouseConfig
from warehouse_sim.experiments import aggregate_replications, replication_configs, run_experiment_suite


def test_replication_configs_expands_each_scenario():
    configs = [WarehouseConfig(scenario_id="a"), WarehouseConfig(scenario_id="b")]
    expanded = replication_configs(configs, replications=3)

    assert len(expanded) == 6
    assert {config.replication for config in expanded} == {0, 1, 2}


def test_aggregate_replications_keeps_scenario_grain():
    raw = pd.DataFrame(
        [
            {"scenario_id": "baseline", "replication": 0, "throughput_per_hour": 40.0, "bottleneck_classification": "balanced / stable"},
            {"scenario_id": "baseline", "replication": 1, "throughput_per_hour": 44.0, "bottleneck_classification": "balanced / stable"},
            {"scenario_id": "stress", "replication": 0, "throughput_per_hour": 50.0, "bottleneck_classification": "robot constrained"},
        ]
    )

    summary = aggregate_replications(raw)

    baseline = summary.loc[summary["scenario_id"] == "baseline"].iloc[0]
    assert baseline["replications"] == 2
    assert baseline["throughput_per_hour"] == 42.0


def test_experiment_suite_writes_expected_artifacts(tmp_path: Path):
    outputs = run_experiment_suite(tmp_path, replications=1)

    assert (tmp_path / "scenario_summary.csv").exists()
    assert (tmp_path / "fleet_size_sweep.csv").exists()
    assert (tmp_path / "demand_stress_test.csv").exists()
    assert (tmp_path / "figures" / "throughput_by_fleet_size.svg").exists()
    assert not outputs["scenario_summary"].empty
