"""Starter discrete-event simulation for a robotic warehouse.

This is intentionally small and readable. It can be expanded into a richer
warehouse digital twin with layout-aware routing, congestion, charging stations,
robot failures, station staffing, and calibrated service-time distributions.
"""

from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Any

import pandas as pd
import simpy


@dataclass(frozen=True)
class SimConfig:
    """Configuration for one simulation scenario."""

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
    seed: int = 42


@dataclass
class Order:
    """A warehouse task/order entering the simulation."""

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

    def _exp_time(self, mean_minutes: float) -> float:
        """Sample a positive duration from an exponential distribution."""
        if mean_minutes <= 0:
            return 0.0
        return self.rng.expovariate(1.0 / mean_minutes)

    def order_generator(self) -> simpy.events.Event:
        """Generate orders according to a Poisson arrival process."""
        while self.env.now < self.config.sim_minutes:
            interarrival = self.rng.expovariate(self.config.order_arrival_rate_per_minute)
            yield self.env.timeout(interarrival)

            self.generated_orders += 1
            order = Order(order_id=self.generated_orders, created_at=self.env.now)
            yield self.order_queue.put(order)

    def robot_worker(self, robot_id: int) -> simpy.events.Event:
        """Robot process that takes orders, travels, waits for a station, and completes tasks."""
        tasks_since_charge = 0

        while self.env.now < self.config.sim_minutes:
            order: Order = yield self.order_queue.get()
            start_time = self.env.now
            wait_time = start_time - order.created_at

            travel_time = self._exp_time(self.config.mean_travel_time_minutes)
            yield self.env.timeout(travel_time)

            if self.rng.random() < self.config.failure_probability_per_task:
                repair_time = self._exp_time(self.config.mean_repair_time_minutes)
                yield self.env.timeout(repair_time)
            else:
                repair_time = 0.0

            with self.pick_stations.request() as request:
                station_request_time = self.env.now
                yield request
                station_wait_time = self.env.now - station_request_time

                pick_time = self._exp_time(self.config.mean_pick_time_minutes)
                self.station_busy_minutes += pick_time
                yield self.env.timeout(pick_time)

            dropoff_time = self._exp_time(self.config.mean_dropoff_time_minutes)
            yield self.env.timeout(dropoff_time)

            tasks_since_charge += 1
            charge_time = 0.0
            if tasks_since_charge >= self.config.charge_after_tasks:
                charge_time = self._exp_time(self.config.mean_charge_time_minutes)
                yield self.env.timeout(charge_time)
                tasks_since_charge = 0

            end_time = self.env.now
            cycle_time = end_time - order.created_at
            robot_busy = end_time - start_time
            self.robot_busy_minutes += robot_busy
            self.completed_orders += 1

            self.order_records.append(
                {
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
                }
            )

    def run(self) -> tuple[pd.DataFrame, dict[str, float]]:
        """Run the simulation and return order-level records plus summary KPIs."""
        self.env.process(self.order_generator())
        for robot_id in range(1, self.config.robot_count + 1):
            self.env.process(self.robot_worker(robot_id))

        self.env.run(until=self.config.sim_minutes)

        orders = pd.DataFrame(self.order_records)
        sim_hours = self.config.sim_minutes / 60.0
        available_robot_minutes = self.config.robot_count * self.config.sim_minutes
        available_station_minutes = self.config.station_count * self.config.sim_minutes

        if orders.empty:
            avg_cycle_time = 0.0
            avg_wait_time = 0.0
            avg_station_wait = 0.0
        else:
            avg_cycle_time = float(orders["cycle_time_minutes"].mean())
            avg_wait_time = float(orders["wait_time_minutes"].mean())
            avg_station_wait = float(orders["station_wait_time_minutes"].mean())

        summary = {
            "robot_count": self.config.robot_count,
            "station_count": self.config.station_count,
            "arrival_rate_per_minute": self.config.order_arrival_rate_per_minute,
            "generated_orders": float(self.generated_orders),
            "completed_orders": float(self.completed_orders),
            "throughput_per_hour": self.completed_orders / sim_hours,
            "avg_cycle_time_minutes": avg_cycle_time,
            "avg_queue_wait_minutes": avg_wait_time,
            "avg_station_wait_minutes": avg_station_wait,
            "robot_utilization_proxy": self.robot_busy_minutes / available_robot_minutes,
            "station_utilization_proxy": self.station_busy_minutes / available_station_minutes,
            "orders_left_in_queue": float(len(self.order_queue.items)),
        }
        return orders, summary


def run_scenarios() -> pd.DataFrame:
    """Compare throughput across different fleet sizes."""
    scenario_summaries: list[dict[str, float]] = []

    for robot_count in [10, 15, 20, 25, 30, 40]:
        config = SimConfig(robot_count=robot_count)
        _, summary = WarehouseSimulation(config).run()
        scenario_summaries.append(summary)

    return pd.DataFrame(scenario_summaries)


if __name__ == "__main__":
    results = run_scenarios()
    pd.set_option("display.max_columns", None)
    print(results.round(2).to_string(index=False))
