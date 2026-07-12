"""Grid-based warehouse layout utilities.

The layout intentionally stays simple and public-safe. It provides enough
structure to demonstrate layout-aware simulation without encoding a real facility
map or proprietary routing logic.
"""

from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Iterable

from warehouse_sim.config import WarehouseConfig
from warehouse_sim.entities import Location


@dataclass(frozen=True)
class WarehouseLayout:
    """Rectangular warehouse layout with stations, chargers, and storage cells."""

    width: int
    height: int
    station_locations: tuple[Location, ...]
    charger_locations: tuple[Location, ...]
    inbound_location: Location
    outbound_location: Location

    @classmethod
    def from_config(cls, config: WarehouseConfig) -> "WarehouseLayout":
        """Create a default synthetic layout from simulation config."""
        mid_y = config.warehouse_height // 2
        station_y_positions = _evenly_spaced(config.station_count, upper=max(2, config.warehouse_height - 3))
        charger_x_positions = _evenly_spaced(
            config.charging_station_count,
            upper=max(2, config.warehouse_width - 3),
        )
        return cls(
            width=config.warehouse_width,
            height=config.warehouse_height,
            station_locations=tuple((config.warehouse_width - 2, y) for y in station_y_positions),
            charger_locations=tuple((x, 1) for x in charger_x_positions),
            inbound_location=(1, mid_y),
            outbound_location=(config.warehouse_width - 1, mid_y),
        )

    def storage_locations(self) -> list[Location]:
        """Return candidate storage cells away from stations and chargers."""
        blocked = set(self.station_locations) | set(self.charger_locations) | {
            self.inbound_location,
            self.outbound_location,
        }
        return [
            (x, y)
            for x in range(2, max(3, self.width - 3))
            for y in range(2, max(3, self.height - 2))
            if (x, y) not in blocked
        ]

    def random_storage_location(self, rng: random.Random) -> Location:
        """Sample a synthetic storage location."""
        locations = self.storage_locations()
        if not locations:
            raise ValueError("No storage locations available for the configured layout.")
        return rng.choice(locations)

    def nearest_station(self, location: Location) -> Location:
        """Return the closest station to a location using Manhattan distance."""
        return min(self.station_locations, key=lambda station: manhattan_distance(location, station))

    def nearest_charger(self, location: Location) -> Location:
        """Return the closest charger to a location using Manhattan distance."""
        return min(self.charger_locations, key=lambda charger: manhattan_distance(location, charger))


def manhattan_distance(start: Location, end: Location) -> int:
    """Grid travel distance between two points."""
    return abs(start[0] - end[0]) + abs(start[1] - end[1])


def path_distance(points: Iterable[Location]) -> int:
    """Total Manhattan distance across a sequence of waypoints."""
    waypoints = list(points)
    if len(waypoints) < 2:
        return 0
    return sum(manhattan_distance(a, b) for a, b in zip(waypoints[:-1], waypoints[1:]))


def travel_minutes(
    distance_cells: int,
    speed_cells_per_minute: float,
    congestion_multiplier: float = 1.0,
) -> float:
    """Convert grid distance to travel time."""
    if speed_cells_per_minute <= 0:
        raise ValueError("speed_cells_per_minute must be positive.")
    return (distance_cells / speed_cells_per_minute) * max(1.0, congestion_multiplier)


def _evenly_spaced(count: int, upper: int) -> list[int]:
    """Return approximately evenly spaced integer coordinates."""
    if count <= 0:
        raise ValueError("count must be positive.")
    if count == 1:
        return [max(1, upper // 2)]
    step = upper / (count + 1)
    return [max(1, min(upper, round(step * (idx + 1)))) for idx in range(count)]
