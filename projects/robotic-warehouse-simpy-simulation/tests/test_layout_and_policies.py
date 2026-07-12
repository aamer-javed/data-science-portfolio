import random

from warehouse_sim.config import WarehouseConfig
from warehouse_sim.entities import Order, RobotState
from warehouse_sim.layout import WarehouseLayout, manhattan_distance, path_distance, travel_minutes
from warehouse_sim.policies import select_order_index


def test_layout_generates_storage_stations_and_chargers():
    layout = WarehouseLayout.from_config(WarehouseConfig(station_count=3, charging_station_count=2))

    assert len(layout.station_locations) == 3
    assert len(layout.charger_locations) == 2
    assert layout.random_storage_location(random.Random(1)) not in layout.station_locations


def test_distance_and_travel_time_are_deterministic():
    assert manhattan_distance((1, 1), (4, 5)) == 7
    assert path_distance([(1, 1), (4, 1), (4, 5)]) == 7
    assert travel_minutes(24, speed_cells_per_minute=12, congestion_multiplier=1.5) == 3.0


def test_assignment_policy_selects_priority_and_nearest_work():
    layout = WarehouseLayout.from_config(WarehouseConfig())
    robot = RobotState(robot_id=1, location=(1, 1))
    orders = [
        Order(order_id=1, created_at=0, storage_location=(35, 20), priority=False, due_by=30),
        Order(order_id=2, created_at=1, storage_location=(2, 2), priority=True, due_by=20),
    ]

    assert select_order_index(orders, robot, layout, "priority_fifo") == 1
    assert select_order_index(orders, robot, layout, "nearest_robot") == 1
