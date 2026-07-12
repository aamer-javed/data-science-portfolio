"""Discrete-event simulation engine for a robotic warehouse fleet.

This module is written as a public, portfolio-safe simulation deliverable. It
models operational mechanisms that matter in robotic fulfillment environments:

- stochastic order arrivals
- grid-based warehouse layout and Manhattan travel distance
- policy-based task selection for FIFO, priority, nearest-robot, and queue-aware dispatching
- finite robot, station, and charging capacity
- stochastic pick, drop-off, repair, and charging durations
- queue monitoring and order-level event records
- scenario-level KPIs for throughput, latency, SLA attainment, and utilization

The model is not intended to represent a proprietary warehouse. It is a compact
engineering artifact that demonstrates how to translate real operations into a
reproducible computational model.
"""

from __future__ import annotations

import random
from typing import Any

import pandas as pd
import simpy

try:  # Supports both editable installs and direct script execution.
    from warehouse_sim.config import WarehouseConfig
    from warehouse_sim.entities import MonitorRecord, Order, OrderRecord, RobotState, SimulationOutputs
    from warehouse_sim.layout import WarehouseLayout, path_distance, travel_minutes
    from warehouse_sim.policies import select_order_index
except ModuleNotFoundError:  # pragma: no cover - convenience for direct local execution
    from config import WarehouseConfig
    from entities import MonitorRecord, Order, OrderRecord, RobotState, SimulationOutputs
    from layout import WarehouseLayout, path_distance, travel_minutes
    from policies import select_order_index


class WarehouseSimulation:
    """Discrete-event simulation of a simplified robotic warehouse.

    The class owns the SimPy environment and generates three kinds of outputs:
    order-level event records, monitoring snapshots, and scenario-level KPIs.
    """

    def __init__(self, config: WarehouseConfig):
        self.config = config
        self.env = simpy.Environment()
        self.rng = random.Random(config.seed + config.replication)
        self.layout = WarehouseLayout.from_config(config)

        self.order_queue: simpy.Store[Order] = simpy.Store(self.env)
        self.pick_stations = simpy.Resource(self.env, capacity=config.station_count)
        self.chargers = simpy.Resource(self.env, capacity=config.charging_station_count)

        self.robots: dict[int, RobotState] = {
            robot_id: RobotState(robot_id=robot_id, location=self.layout.inbound_location)
            for robot_id in range(1, config.robot_count + 1)
        }

        self.generated_orders = 0
        self.completed_orders = 0
        self.robot_busy_minutes = 0.0
        self.station_busy_minutes = 0.0
        self.charger_busy_minutes = 0.0

        self.order_records: list[OrderRecord] = []
        self.monitor_records: list[MonitorRecord] = []

    def _exp_time(self, mean_minutes: float) -> float:
        """Sample a duration from an exponential distribution."""
        if mean_minutes <= 0:
            return 0.0
        return self.rng.expovariate(1.0 / mean_minutes)

    def _congestion_multiplier(self) -> float:
        """Translate current queue pressure into a simple travel-time multiplier."""
        queued_work = len(self.order_queue.items) + len(self.pick_stations.queue) + len(self.chargers.queue)
        capacity = max(1, self.config.robot_count + self.config.station_count + self.config.charging_station_count)
        return 1.0 + self.config.congestion_factor * (queued_work / capacity)

    def _travel_time(self, distance_cells: int) -> float:
        return travel_minutes(
            distance_cells,
            speed_cells_per_minute=self.config.travel_speed_cells_per_minute,
            congestion_multiplier=self._congestion_multiplier(),
        )

    def order_generator(self):
        """Generate orders using a Poisson arrival process."""
        while self.env.now < self.config.sim_minutes:
            interarrival = self.rng.expovariate(self.config.order_arrival_rate_per_minute)
            yield self.env.timeout(interarrival)

            if self.env.now >= self.config.sim_minutes:
                break

            self.generated_orders += 1
            priority = self.rng.random() < self.config.priority_order_probability
            due_by = float(self.env.now) + self.config.sla_minutes * (
                self.config.priority_sla_multiplier if priority else 1.0
            )
            order = Order(
                order_id=self.generated_orders,
                created_at=float(self.env.now),
                storage_location=self.layout.random_storage_location(self.rng),
                priority=priority,
                due_by=due_by,
            )
            yield self.order_queue.put(order)

    def monitor(self):
        """Capture queue, station, and charger state at a fixed cadence."""
        while self.env.now < self.config.sim_minutes:
            self.monitor_records.append(
                MonitorRecord(
                    scenario_id=self.config.scenario_id,
                    replication=self.config.replication,
                    timestamp_minutes=float(self.env.now),
                    queue_length=len(self.order_queue.items),
                    station_queue_length=len(self.pick_stations.queue),
                    station_users=self.pick_stations.count,
                    charger_queue_length=len(self.chargers.queue),
                    charger_users=self.chargers.count,
                    completed_orders=self.completed_orders,
                )
            )
            yield self.env.timeout(self.config.monitor_interval_minutes)

    def _next_order_for_robot(self, robot: RobotState) -> Order:
        """Select the next order from the queue under the configured dispatch policy."""
        if not self.order_queue.items:
            raise ValueError("order queue is empty")
        selected_idx = select_order_index(
            list(self.order_queue.items),
            robot=robot,
            layout=self.layout,
            policy=self.config.assignment_policy,
            system_queue_length=len(self.order_queue.items),
        )
        return self.order_queue.items.pop(selected_idx)

    def robot_worker(self, robot_id: int):
        """Robot worker that pulls orders and processes them through the system."""
        robot = self.robots[robot_id]

        while self.env.now < self.config.sim_minutes:
            if self.order_queue.items:
                order = self._next_order_for_robot(robot)
            else:
                order = yield self.order_queue.get()

            started_at = float(self.env.now)
            queue_wait = started_at - order.created_at

            station_location = self.layout.nearest_station(order.storage_location)
            to_storage_distance = path_distance([robot.location, order.storage_location])
            to_station_distance = path_distance([order.storage_location, station_location])
            work_travel_distance = to_storage_distance + to_station_distance
            travel_time = self._travel_time(work_travel_distance)
            yield self.env.timeout(travel_time)
            robot.location = station_location

            robot_failed = self.rng.random() < self.config.failure_probability_per_task
            repair_time = self._exp_time(self.config.mean_repair_time_minutes) if robot_failed else 0.0
            if repair_time:
                yield self.env.timeout(repair_time)

            with self.pick_stations.request() as request:
                station_requested_at = float(self.env.now)
                yield request
                station_wait = float(self.env.now) - station_requested_at

                pick_time = self._exp_time(self.config.mean_pick_time_minutes)
                self.station_busy_minutes += pick_time
                yield self.env.timeout(pick_time)

            dropoff_distance = path_distance([robot.location, self.layout.outbound_location])
            dropoff_travel_time = self._travel_time(dropoff_distance)
            dropoff_service_time = self._exp_time(self.config.mean_dropoff_time_minutes)
            dropoff_time = dropoff_travel_time + dropoff_service_time
            yield self.env.timeout(dropoff_time)
            robot.location = self.layout.outbound_location

            robot.tasks_since_charge += 1
            charge_time = 0.0
            charging_wait = 0.0
            charging_distance = 0
            charging_travel_time = 0.0
            if robot.tasks_since_charge >= self.config.charge_after_tasks:
                charger_location = self.layout.nearest_charger(robot.location)
                charging_distance = path_distance([robot.location, charger_location])
                charging_travel_time = self._travel_time(charging_distance)
                yield self.env.timeout(charging_travel_time)
                robot.location = charger_location

                with self.chargers.request() as charger_request:
                    charger_requested_at = float(self.env.now)
                    yield charger_request
                    charging_wait = float(self.env.now) - charger_requested_at
                    charge_time = self._exp_time(self.config.mean_charge_time_minutes)
                    self.charger_busy_minutes += charge_time
                    yield self.env.timeout(charge_time)
                    robot.tasks_since_charge = 0

            completed_at = float(self.env.now)
            cycle_time = completed_at - order.created_at
            total_distance = work_travel_distance + dropoff_distance + charging_distance
            total_travel_time = travel_time + dropoff_travel_time + charging_travel_time
            self.robot_busy_minutes += completed_at - started_at
            self.completed_orders += 1

            self.order_records.append(
                OrderRecord(
                    scenario_id=self.config.scenario_id,
                    replication=self.config.replication,
                    order_id=order.order_id,
                    robot_id=robot_id,
                    created_at=float(order.created_at),
                    started_at=started_at,
                    completed_at=completed_at,
                    queue_wait_minutes=queue_wait,
                    station_wait_minutes=station_wait,
                    charging_wait_minutes=charging_wait,
                    travel_time_minutes=total_travel_time,
                    pick_time_minutes=pick_time,
                    dropoff_time_minutes=dropoff_time,
                    repair_time_minutes=repair_time,
                    charge_time_minutes=charge_time,
                    cycle_time_minutes=cycle_time,
                    travel_distance_cells=total_distance,
                    storage_x=order.storage_location[0],
                    storage_y=order.storage_location[1],
                    station_x=station_location[0],
                    station_y=station_location[1],
                    priority=order.priority,
                    due_by=order.due_by,
                    met_sla=completed_at <= order.due_by,
                    robot_failed=robot_failed,
                    assignment_policy=self.config.assignment_policy,
                )
            )

    def run(self) -> SimulationOutputs:
        """Run one scenario/replication and return structured outputs."""
        self.env.process(self.order_generator())
        self.env.process(self.monitor())
        for robot_id in range(1, self.config.robot_count + 1):
            self.env.process(self.robot_worker(robot_id))

        self.env.run(until=self.config.sim_minutes)

        orders = pd.DataFrame([record.to_dict() for record in self.order_records])
        monitors = pd.DataFrame([record.to_dict() for record in self.monitor_records])
        summary = self._build_summary(orders)
        return SimulationOutputs(orders=orders, monitors=monitors, summary=summary)

    def _build_summary(self, orders: pd.DataFrame) -> dict[str, Any]:
        sim_hours = self.config.sim_minutes / 60.0
        available_robot_minutes = self.config.robot_count * self.config.sim_minutes
        available_station_minutes = self.config.station_count * self.config.sim_minutes
        available_charger_minutes = self.config.charging_station_count * self.config.sim_minutes

        if orders.empty:
            avg_cycle_time = 0.0
            p50_cycle_time = 0.0
            p90_cycle_time = 0.0
            avg_queue_wait = 0.0
            avg_station_wait = 0.0
            avg_charging_wait = 0.0
            sla_rate = 0.0
            priority_sla_rate = 0.0
            failure_rate = 0.0
            charge_time_total = 0.0
            avg_travel_distance = 0.0
        else:
            avg_cycle_time = float(orders["cycle_time_minutes"].mean())
            p50_cycle_time = float(orders["cycle_time_minutes"].quantile(0.50))
            p90_cycle_time = float(orders["cycle_time_minutes"].quantile(0.90))
            avg_queue_wait = float(orders["queue_wait_minutes"].mean())
            avg_station_wait = float(orders["station_wait_minutes"].mean())
            avg_charging_wait = float(orders["charging_wait_minutes"].mean())
            sla_rate = float(orders["met_sla"].mean())
            priority_orders = orders[orders["priority"]]
            priority_sla_rate = float(priority_orders["met_sla"].mean()) if not priority_orders.empty else 0.0
            failure_rate = float(orders["robot_failed"].mean())
            charge_time_total = float(orders["charge_time_minutes"].sum())
            avg_travel_distance = float(orders["travel_distance_cells"].mean())

        robot_utilization = self.robot_busy_minutes / available_robot_minutes
        station_utilization = self.station_busy_minutes / available_station_minutes
        charger_utilization = self.charger_busy_minutes / available_charger_minutes
        orders_left_in_queue = len(self.order_queue.items)

        summary: dict[str, Any] = {
            "scenario_id": self.config.scenario_id,
            "replication": self.config.replication,
            "robot_count": self.config.robot_count,
            "station_count": self.config.station_count,
            "charging_station_count": self.config.charging_station_count,
            "arrival_rate_per_minute": self.config.order_arrival_rate_per_minute,
            "assignment_policy": self.config.assignment_policy,
            "warehouse_width": self.config.warehouse_width,
            "warehouse_height": self.config.warehouse_height,
            "generated_orders": self.generated_orders,
            "completed_orders": self.completed_orders,
            "orders_left_in_queue": orders_left_in_queue,
            "throughput_per_hour": self.completed_orders / sim_hours,
            "avg_cycle_time_minutes": avg_cycle_time,
            "p50_cycle_time_minutes": p50_cycle_time,
            "p90_cycle_time_minutes": p90_cycle_time,
            "avg_queue_wait_minutes": avg_queue_wait,
            "avg_station_wait_minutes": avg_station_wait,
            "avg_charging_wait_minutes": avg_charging_wait,
            "avg_travel_distance_cells": avg_travel_distance,
            "robot_utilization": robot_utilization,
            "station_utilization": station_utilization,
            "charger_utilization": charger_utilization,
            "sla_attainment_rate": sla_rate,
            "priority_sla_attainment_rate": priority_sla_rate,
            "failure_rate": failure_rate,
            "charge_time_total_minutes": charge_time_total,
        }
        summary["bottleneck_classification"] = classify_bottleneck(summary)
        return summary


def classify_bottleneck(summary: dict[str, Any]) -> str:
    """Classify the dominant bottleneck using transparent heuristic rules.

    This is deliberately simple. In a production setting, these rules would be
    validated against operational observations and may be replaced by a calibrated
    statistical classifier.
    """
    robot_utilization = float(summary.get("robot_utilization", 0.0))
    station_utilization = float(summary.get("station_utilization", 0.0))
    charger_utilization = float(summary.get("charger_utilization", 0.0))
    queue_wait = float(summary.get("avg_queue_wait_minutes", 0.0))
    station_wait = float(summary.get("avg_station_wait_minutes", 0.0))
    charging_wait = float(summary.get("avg_charging_wait_minutes", 0.0))
    sla_rate = float(summary.get("sla_attainment_rate", 0.0))
    orders_left = float(summary.get("orders_left_in_queue", 0.0))

    if charger_utilization >= 0.80 or charging_wait >= 3:
        return "charging constrained"
    if station_utilization >= 0.85 or station_wait >= 5:
        return "station constrained"
    if robot_utilization >= 0.80 or queue_wait >= 10 or orders_left >= 10:
        return "robot constrained"
    if sla_rate < 0.80 and queue_wait > station_wait:
        return "demand exceeds modeled capacity"
    return "balanced / stable"


def run_scenario(config: WarehouseConfig) -> SimulationOutputs:
    """Convenience wrapper for a single scenario run."""
    return WarehouseSimulation(config).run()


def scenario_catalog() -> list[WarehouseConfig]:
    """Curated scenarios used by the experiment runner and notebook."""
    baseline = WarehouseConfig()
    return [
        baseline,
        baseline.with_overrides(scenario_id="fewer_robots", robot_count=16, seed=43),
        baseline.with_overrides(scenario_id="more_robots", robot_count=32, seed=44),
        baseline.with_overrides(scenario_id="demand_plus_25pct", order_arrival_rate_per_minute=1.06, seed=45),
        baseline.with_overrides(scenario_id="demand_plus_50pct", order_arrival_rate_per_minute=1.28, seed=46),
        baseline.with_overrides(scenario_id="more_stations", station_count=6, seed=47),
        baseline.with_overrides(
            scenario_id="charger_constrained",
            charging_station_count=1,
            charge_after_tasks=6,
            mean_charge_time_minutes=18,
            seed=48,
        ),
        baseline.with_overrides(
            scenario_id="nearest_robot_policy",
            assignment_policy="nearest_robot",
            seed=49,
        ),
        baseline.with_overrides(
            scenario_id="higher_failure_rate",
            failure_probability_per_task=0.04,
            mean_repair_time_minutes=14,
            seed=50,
        ),
    ]


def run_scenarios(configs: list[WarehouseConfig] | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Run a list of scenarios and return order, monitor, and summary tables."""
    configs = configs or scenario_catalog()
    orders: list[pd.DataFrame] = []
    monitors: list[pd.DataFrame] = []
    summaries: list[dict[str, Any]] = []

    for config in configs:
        outputs = run_scenario(config)
        orders.append(outputs.orders)
        monitors.append(outputs.monitors)
        summaries.append(outputs.summary)

    orders_df = pd.concat(orders, ignore_index=True) if orders else pd.DataFrame()
    monitors_df = pd.concat(monitors, ignore_index=True) if monitors else pd.DataFrame()
    summary_df = pd.DataFrame(summaries)
    return orders_df, monitors_df, summary_df


if __name__ == "__main__":
    _, _, summary = run_scenarios()
    display_columns = [
        "scenario_id",
        "robot_count",
        "station_count",
        "charging_station_count",
        "assignment_policy",
        "throughput_per_hour",
        "avg_cycle_time_minutes",
        "p90_cycle_time_minutes",
        "sla_attainment_rate",
        "robot_utilization",
        "station_utilization",
        "charger_utilization",
        "bottleneck_classification",
    ]
    print(summary[display_columns].round(2).to_string(index=False))
