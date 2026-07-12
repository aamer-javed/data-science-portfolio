"""Discrete-event simulation for a robotic warehouse fleet.

This module models a simplified robotic warehouse operation using SimPy. It is
built as a portfolio-quality example for robotic warehouse simulation roles:
orders arrive stochastically, robots pull work from a queue, stations constrain
processing capacity, and each order records travel, queue, station, failure,
charging, and cycle-time behavior.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import random
from typing import Any

import pandas as pd
import simpy


@dataclass(frozen=True)
class SimConfig:
    """Configuration for one simulation scenario."""

    scenario_name: str = "baseline"
    sim_minutes: int = 8 * 60
    robot_count: int = 20
    station_count: int = 4
    order_arrival_rate_per_minute: float = 0.80
    mean_travel_time_minutes: float = 4.0
    mean_pick_time_minutes: float = 2.5
    mean_dropoff_time_minutes: float = 1.5
    failure_probability_per_task: float = 0.02
    mean_repair_time_minutes: float = 8.0
    charge_after_tasks: int = 12
    mean_charge_time_minutes: float = 15.0
    sla_minutes: float = 20.0
    seed: int = 42


@dataclass
class Order:
    """A warehouse task entering the simulation."""

    order_id: int
    created_at: float


class WarehouseSimulation:
    """Discrete-event model of a simplified robotic warehouse."""

    def __init__(self, config: SimConfig):
        self.config = config
        self.env = simpy.Environment()
        self.rng = random.Random(config.seed)
        self.order_queue: simpy.Store[Order] = simpy.Store(self.env)
        self.pick_stations = simpy.Resource(self.env, capacity=config.station_count)

        self.generated_orders = 0
        self.completed_orders = 0
        self.robot_busy_minutes = 0.0
        self.station_busy_minutes = 0.0
        self.order_records: list[dict[str, Any]] = []
        self.queue_snapshots: list[dict[str, Any]] = []

    def _exp_time(self, mean_minutes: float) -> float:
        if mean_minutes <= 0:
            return 0.0
        return self.rng.expovariate(1.0 / mean_minutes)

    def order_generator(self):
        """Generate orders with a Poisson arrival process."""
        while self.env.now < self.config.sim_minutes:
            interarrival = self.rng.expovariate(self.config.order_arrival_rate_per_minute)
            yield self.env.timeout(interarrival)
            self.generated_orders += 1
            yield self.order_queue.put(Order(self.generated_orders, self.env.now))

    def queue_monitor(self, interval_minutes: float = 5.0):
        """Capture queue length periodically for time-series analysis."""
        while self.env.now < self.config.sim_minutes:
            self.queue_snapshots.append(
                {
                    "scenario_name": self.config.scenario_name,
                    "time_minute": self.env.now,
                    "queue_length": len(self.order_queue.items),
                }
            )
            yield self.env.timeout(interval_minutes)

    def robot_worker(self, robot_id: int):
        """Robot process that completes orders from the shared queue."""
        tasks_since_charge = 0
        while self.env.now < self.config.sim_minutes:
            order: Order = yield self.order_queue.get()
            start_time = self.env.now
            wait_time = start_time - order.created_at

            travel_time = self._exp_time(self.config.mean_travel_time_minutes)
            yield self.env.timeout(travel_time)

            repair_time = 0.0
            failed = self.rng.random() < self.config.failure_probability_per_task
            if failed:
                repair_time = self._exp_time(self.config.mean_repair_time_minutes)
                yield self.env.timeout(repair_time)

            with self.pick_stations.request() as request:
                station_request_time = self.env.now
                yield request
                station_wait_time = self.env.now - station_request_time
                pick_time = self._exp_time(self.config.mean_pick_time_minutes)
                self.station_busy_minutes += pick_time
                yield self.env.timeout(pick_time)

            dropoff_time = self._exp_time(self.config.mean_dropoff_time_minutes)
            yield self.env.timeout(dropoff_time)

            charge_time = 0.0
            tasks_since_charge += 1
            if tasks_since_charge >= self.config.charge_after_tasks:
                charge_time = self._exp_time(self.config.mean_charge_time_minutes)
                yield self.env.timeout(charge_time)
                tasks_since_charge = 0

            end_time = self.env.now
            cycle_time = end_time - order.created_at
            self.robot_busy_minutes += end_time - start_time
            self.completed_orders += 1

            self.order_records.append(
                {
                    "scenario_name": self.config.scenario_name,
                    "order_id": order.order_id,
                    "robot_id": robot_id,
                    "created_at": order.created_at,
                    "completed_at": end_time,
                    "wait_time_minutes": wait_time,
                    "station_wait_time_minutes": station_wait_time,
                    "travel_time_minutes": travel_time,
                    "pick_time_minutes": pick_time,
                    "dropoff_time_minutes": dropoff_time,
                    "repair_time_minutes": repair_time,
                    "charge_time_minutes": charge_time,
                    "cycle_time_minutes": cycle_time,
                    "met_sla": cycle_time <= self.config.sla_minutes,
                    "robot_failed": failed,
                }
            )

    def run(self) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, float]]:
        """Run one simulation and return order records, queue series, and summary KPIs."""
        self.env.process(self.order_generator())
        self.env.process(self.queue_monitor())
        for robot_id in range(1, self.config.robot_count + 1):
            self.env.process(self.robot_worker(robot_id))

        self.env.run(until=self.config.sim_minutes)

        orders = pd.DataFrame(self.order_records)
        queue = pd.DataFrame(self.queue_snapshots)
        sim_hours = self.config.sim_minutes / 60.0
        available_robot_minutes = self.config.robot_count * self.config.sim_minutes
        available_station_minutes = self.config.station_count * self.config.sim_minutes

        if orders.empty:
            avg_cycle_time = avg_wait_time = avg_station_wait = p90_cycle_time = sla_rate = 0.0
        else:
            avg_cycle_time = float(orders["cycle_time_minutes"].mean())
            avg_wait_time = float(orders["wait_time_minutes"].mean())
            avg_station_wait = float(orders["station_wait_time_minutes"].mean())
            p90_cycle_time = float(orders["cycle_time_minutes"].quantile(0.90))
            sla_rate = float(orders["met_sla"].mean())

        summary = {
            "scenario_name": self.config.scenario_name,
            "robot_count": float(self.config.robot_count),
            "station_count": float(self.config.station_count),
            "arrival_rate_per_minute": self.config.order_arrival_rate_per_minute,
            "generated_orders": float(self.generated_orders),
            "completed_orders": float(self.completed_orders),
            "orders_left_in_queue": float(len(self.order_queue.items)),
            "throughput_per_hour": self.completed_orders / sim_hours,
            "avg_cycle_time_minutes": avg_cycle_time,
            "p90_cycle_time_minutes": p90_cycle_time,
            "avg_queue_wait_minutes": avg_wait_time,
            "avg_station_wait_minutes": avg_station_wait,
            "robot_utilization_proxy": self.robot_busy_minutes / available_robot_minutes,
            "station_utilization_proxy": self.station_busy_minutes / available_station_minutes,
            "sla_attainment_rate": sla_rate,
        }
        summary.update({f"config_{k}": v for k, v in asdict(self.config).items()})
        return orders, queue, summary


def default_scenarios() -> list[SimConfig]:
    """Scenario set used by the notebook and chart generator."""
    return [
        SimConfig(scenario_name="baseline", robot_count=20, station_count=4, order_arrival_rate_per_minute=0.80),
        SimConfig(scenario_name="fleet_15", robot_count=15, station_count=4, order_arrival_rate_per_minute=0.80, seed=43),
        SimConfig(scenario_name="fleet_25", robot_count=25, station_count=4, order_arrival_rate_per_minute=0.80, seed=44),
        SimConfig(scenario_name="demand_plus_25pct", robot_count=20, station_count=4, order_arrival_rate_per_minute=1.00, seed=45),
        SimConfig(scenario_name="demand_plus_50pct", robot_count=20, station_count=4, order_arrival_rate_per_minute=1.20, seed=46),
        SimConfig(scenario_name="stations_6", robot_count=20, station_count=6, order_arrival_rate_per_minute=0.80, seed=47),
    ]


def run_scenarios(configs: list[SimConfig] | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Run multiple scenarios and return order, queue, and summary dataframes."""
    configs = configs or default_scenarios()
    all_orders: list[pd.DataFrame] = []
    all_queues: list[pd.DataFrame] = []
    summaries: list[dict[str, float]] = []

    for config in configs:
        orders, queue, summary = WarehouseSimulation(config).run()
        all_orders.append(orders)
        all_queues.append(queue)
        summaries.append(summary)

    return pd.concat(all_orders, ignore_index=True), pd.concat(all_queues, ignore_index=True), pd.DataFrame(summaries)


if __name__ == "__main__":
    _, _, scenario_summary = run_scenarios()
    columns = [
        "scenario_name",
        "robot_count",
        "station_count",
        "arrival_rate_per_minute",
        "completed_orders",
        "throughput_per_hour",
        "avg_cycle_time_minutes",
        "p90_cycle_time_minutes",
        "avg_queue_wait_minutes",
        "robot_utilization_proxy",
        "station_utilization_proxy",
        "sla_attainment_rate",
    ]
    print(scenario_summary[columns].round(2).to_string(index=False))
