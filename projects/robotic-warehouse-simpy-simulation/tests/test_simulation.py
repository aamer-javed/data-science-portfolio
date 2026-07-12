from warehouse_sim.config import WarehouseConfig
from warehouse_sim.simulation import WarehouseSimulation, classify_bottleneck, run_scenario, scenario_catalog


def small_config(**overrides):
    base = WarehouseConfig(
        scenario_id="unit_test",
        sim_minutes=120,
        robot_count=8,
        station_count=2,
        charging_station_count=2,
        order_arrival_rate_per_minute=0.25,
        travel_speed_cells_per_minute=12.0,
        mean_pick_time_minutes=1.2,
        mean_dropoff_time_minutes=0.8,
        failure_probability_per_task=0.0,
        charge_after_tasks=100,
        sla_minutes=20.0,
        seed=7,
    )
    return base.with_overrides(**overrides)


def test_single_scenario_produces_order_monitor_and_summary_outputs():
    outputs = run_scenario(small_config())

    assert not outputs.orders.empty
    assert not outputs.monitors.empty
    assert outputs.summary["completed_orders"] > 0
    assert outputs.summary["throughput_per_hour"] > 0
    assert 0 <= outputs.summary["sla_attainment_rate"] <= 1
    assert 0 <= outputs.summary["robot_utilization"] <= 1
    assert 0 <= outputs.summary["station_utilization"] <= 1
    assert 0 <= outputs.summary["charger_utilization"] <= 1
    assert "travel_distance_cells" in outputs.orders.columns
    assert "charger_queue_length" in outputs.monitors.columns


def test_simulation_is_reproducible_for_same_seed_and_replication():
    config = small_config(seed=123, replication=0)
    first = WarehouseSimulation(config).run().summary
    second = WarehouseSimulation(config).run().summary

    assert first["completed_orders"] == second["completed_orders"]
    assert first["throughput_per_hour"] == second["throughput_per_hour"]
    assert first["avg_cycle_time_minutes"] == second["avg_cycle_time_minutes"]


def test_scenario_catalog_contains_named_operating_cases():
    scenario_ids = {config.scenario_id for config in scenario_catalog()}

    assert "baseline" in scenario_ids
    assert "demand_plus_50pct" in scenario_ids
    assert "more_stations" in scenario_ids
    assert "charger_constrained" in scenario_ids
    assert "nearest_robot_policy" in scenario_ids


def test_bottleneck_classifier_is_transparent_and_deterministic():
    assert classify_bottleneck(
        {
            "robot_utilization": 0.91,
            "station_utilization": 0.40,
            "charger_utilization": 0.10,
            "avg_queue_wait_minutes": 12.0,
            "avg_station_wait_minutes": 0.5,
            "avg_charging_wait_minutes": 0.0,
            "sla_attainment_rate": 0.75,
            "orders_left_in_queue": 30,
        }
    ) == "robot constrained"

    assert classify_bottleneck(
        {
            "robot_utilization": 0.40,
            "station_utilization": 0.90,
            "charger_utilization": 0.10,
            "avg_queue_wait_minutes": 1.0,
            "avg_station_wait_minutes": 6.0,
            "avg_charging_wait_minutes": 0.0,
            "sla_attainment_rate": 0.70,
            "orders_left_in_queue": 0,
        }
    ) == "station constrained"

    assert classify_bottleneck(
        {
            "robot_utilization": 0.40,
            "station_utilization": 0.40,
            "charger_utilization": 0.91,
            "avg_queue_wait_minutes": 1.0,
            "avg_station_wait_minutes": 1.0,
            "avg_charging_wait_minutes": 4.0,
            "sla_attainment_rate": 0.90,
            "orders_left_in_queue": 0,
        }
    ) == "charging constrained"
