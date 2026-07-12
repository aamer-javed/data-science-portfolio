import pytest

from warehouse_sim.config import WarehouseConfig


def test_config_accepts_valid_baseline():
    config = WarehouseConfig()
    assert config.scenario_id == "baseline"
    assert config.robot_count > 0
    assert config.station_count > 0
    assert config.order_arrival_rate_per_minute > 0


def test_config_rejects_invalid_capacity():
    with pytest.raises(ValueError, match="robot_count"):
        WarehouseConfig(robot_count=0)

    with pytest.raises(ValueError, match="station_count"):
        WarehouseConfig(station_count=0)


def test_config_with_overrides_preserves_immutability():
    base = WarehouseConfig(robot_count=24)
    changed = base.with_overrides(robot_count=32, scenario_id="more_robots")

    assert base.robot_count == 24
    assert changed.robot_count == 32
    assert changed.scenario_id == "more_robots"
