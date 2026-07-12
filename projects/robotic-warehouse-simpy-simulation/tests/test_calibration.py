import pandas as pd

from warehouse_sim.calibration import apply_calibration, calibrate_from_event_log, compare_to_historical_kpis
from warehouse_sim.config import WarehouseConfig


def test_calibration_estimates_parameters_from_event_log():
    events = pd.DataFrame(
        {
            "created_at": [0, 2, 4, 6, 8],
            "travel_time_minutes": [1.0, 2.0, 3.0, 4.0, 5.0],
            "pick_time_minutes": [2.0, 2.0, 2.0, 2.0, 2.0],
            "dropoff_time_minutes": [1.0, 1.5, 1.0, 1.5, 1.0],
            "repair_time_minutes": [0.0, 0.0, 10.0, 0.0, 0.0],
            "robot_failed": [False, False, True, False, False],
        }
    )

    report = calibrate_from_event_log(events)

    assert report.arrival_rate_per_minute > 0
    assert report.mean_travel_time_minutes == 3.0
    assert report.failure_probability_per_task == 0.2


def test_apply_calibration_returns_new_config():
    events = pd.DataFrame({"created_at": [0, 1, 2], "travel_time_minutes": [2, 2, 2]})
    calibrated = apply_calibration(WarehouseConfig(), events)

    assert calibrated.scenario_id == "calibrated"
    assert calibrated.travel_speed_cells_per_minute == 21.0


def test_compare_to_historical_kpis_returns_error_table():
    simulated = pd.DataFrame({"scenario_id": ["baseline"], "throughput_per_hour": [42.0]})
    historical = pd.DataFrame({"scenario_id": ["baseline"], "throughput_per_hour": [40.0]})

    comparison = compare_to_historical_kpis(simulated, historical)

    assert comparison.iloc[0]["metric"] == "throughput_per_hour"
    assert comparison.iloc[0]["error"] == 2.0
