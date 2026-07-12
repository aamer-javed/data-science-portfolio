"""Task assignment policies for robot dispatching.

The policies are intentionally transparent. They are not meant to be optimal;
they provide reviewable baselines that can be compared against richer routing,
optimization, or reinforcement-learning approaches later.
"""

from __future__ import annotations

from warehouse_sim.entities import Order, RobotState
from warehouse_sim.layout import WarehouseLayout


SUPPORTED_ASSIGNMENT_POLICIES = {
    "fifo",
    "priority_fifo",
    "nearest_robot",
    "shortest_queue_priority",
}


def score_order(
    order: Order,
    robot: RobotState,
    layout: WarehouseLayout,
    policy: str,
    system_queue_length: int = 0,
) -> tuple[float, float, int]:
    """Return a sortable score for assigning an order to a robot.

    Lower scores are better. The tuple structure makes policy decisions easy to
    audit in tests and code review.
    """
    if policy not in SUPPORTED_ASSIGNMENT_POLICIES:
        raise ValueError(f"Unsupported assignment policy: {policy}")

    priority_component = 0 if order.priority else 1
    distance = layout.distance(robot.location, order.storage_location)

    if policy == "fifo":
        return (float(order.order_id), 0.0, 0)
    if policy == "priority_fifo":
        return (float(priority_component), float(order.order_id), 0)
    if policy == "nearest_robot":
        return (float(distance), float(priority_component), order.order_id)

    # shortest_queue_priority keeps priority work ahead of standard work while
    # adding a small congestion penalty so the policy is sensitive to system load.
    congestion_penalty = max(system_queue_length, 0) * 0.05
    return (float(priority_component), float(distance) + congestion_penalty, order.order_id)


def select_order_index(
    orders: list[Order],
    robot: RobotState,
    layout: WarehouseLayout,
    policy: str,
    system_queue_length: int = 0,
) -> int:
    """Return the index of the best order for a robot under the selected policy."""
    if not orders:
        raise ValueError("orders must contain at least one order")

    scored = [
        (score_order(order, robot, layout, policy, system_queue_length), idx)
        for idx, order in enumerate(orders)
    ]
    scored.sort(key=lambda item: item[0])
    return scored[0][1]
