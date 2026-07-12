"""Interactive digital twin scenario planner.

Run from the project root with:

    streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import streamlit as st

from warehouse_sim.config import WarehouseConfig
from warehouse_sim.simulation import run_scenario


st.set_page_config(page_title="Warehouse Digital Twin", layout="wide")
st.title("Robotic Warehouse Digital Twin Scenario Planner")
st.caption("Public-safe DES model for exploring fleet, station, charging, demand, and dispatching trade-offs.")

with st.sidebar:
    st.header("Scenario inputs")
    robot_count = st.slider("Robot fleet size", min_value=8, max_value=60, value=24, step=2)
    station_count = st.slider("Pick/drop stations", min_value=1, max_value=12, value=4)
    charging_station_count = st.slider("Charging stations", min_value=1, max_value=12, value=4)
    arrival_rate = st.slider("Order arrival rate per minute", min_value=0.20, max_value=2.00, value=0.85, step=0.05)
    assignment_policy = st.selectbox(
        "Dispatching policy",
        options=["fifo", "priority_fifo", "nearest_robot", "shortest_queue_priority"],
        index=3,
    )
    congestion_factor = st.slider("Congestion sensitivity", min_value=0.00, max_value=0.30, value=0.08, step=0.01)
    failure_rate = st.slider("Failure probability per task", min_value=0.00, max_value=0.10, value=0.015, step=0.005)
    charge_after_tasks = st.slider("Charge after tasks", min_value=3, max_value=30, value=14)
    seed = st.number_input("Seed", min_value=1, max_value=9999, value=42)

config = WarehouseConfig(
    scenario_id="dashboard_scenario",
    robot_count=robot_count,
    station_count=station_count,
    charging_station_count=charging_station_count,
    order_arrival_rate_per_minute=arrival_rate,
    assignment_policy=assignment_policy,
    congestion_factor=congestion_factor,
    failure_probability_per_task=failure_rate,
    charge_after_tasks=charge_after_tasks,
    seed=int(seed),
)

outputs = run_scenario(config)
summary = outputs.summary
orders = outputs.orders
monitors = outputs.monitors

kpi_cols = st.columns(5)
kpi_cols[0].metric("Throughput / hr", f"{summary['throughput_per_hour']:.1f}")
kpi_cols[1].metric("Avg cycle min", f"{summary['avg_cycle_time_minutes']:.1f}")
kpi_cols[2].metric("SLA attainment", f"{summary['sla_attainment_rate']:.1%}")
kpi_cols[3].metric("Robot util", f"{summary['robot_utilization']:.1%}")
kpi_cols[4].metric("Bottleneck", summary["bottleneck_classification"])

st.subheader("Scenario summary")
st.dataframe(
    {
        "metric": [
            "Completed orders",
            "P90 cycle time",
            "Queue wait",
            "Station wait",
            "Charging wait",
            "Station utilization",
            "Charger utilization",
            "Average travel distance",
        ],
        "value": [
            round(summary["completed_orders"], 2),
            round(summary["p90_cycle_time_minutes"], 2),
            round(summary["avg_queue_wait_minutes"], 2),
            round(summary["avg_station_wait_minutes"], 2),
            round(summary["avg_charging_wait_minutes"], 2),
            round(summary["station_utilization"], 3),
            round(summary["charger_utilization"], 3),
            round(summary["avg_travel_distance_cells"], 2),
        ],
    },
    use_container_width=True,
)

left, right = st.columns(2)
with left:
    st.subheader("Queue length over time")
    if not monitors.empty:
        st.line_chart(monitors.set_index("timestamp_minutes")[["queue_length", "station_queue_length", "charger_queue_length"]])
with right:
    st.subheader("Cycle time distribution")
    if not orders.empty:
        st.bar_chart(orders["cycle_time_minutes"].round().value_counts().sort_index())

st.subheader("Order-level sample")
st.dataframe(orders.head(50), use_container_width=True)

st.info(
    "This dashboard uses synthetic assumptions. In production, the config would be calibrated from historical event logs and compared against observed KPIs."
)
