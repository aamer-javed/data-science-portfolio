# Robotic Warehouse DES Simulation

## Objective

Build a discrete-event simulation of a robotic warehouse using **Python and SimPy**. The model simulates order arrivals, robot task execution, station queues, travel time, pick/drop-off time, downtime, charging, and throughput bottlenecks.

This project is designed to demonstrate skills directly relevant to senior/principal data science roles in robotic warehouse systems.

## Why this matters

Physical warehouse testing is expensive and slow. A simulation allows teams to test operational changes before deployment, estimate capacity, identify bottlenecks, and compare scenarios such as increased demand, larger robot fleets, additional stations, or higher downtime.

## Core Questions

- How many orders per hour can the warehouse process?
- Where do queues form first: robot availability, stations, travel, charging, or downtime?
- How does throughput change as fleet size increases?
- What is the utilization of robots and pick stations?
- What demand level causes SLA degradation?

## Technical Scope

- Discrete-event simulation with SimPy
- Stochastic order arrivals
- Stochastic travel, pick, drop-off, repair, and charge times
- Robot fleet process model
- Station resource constraints
- Scenario experiments
- KPI output as pandas DataFrames

## Initial KPIs

- Throughput per hour
- Average order cycle time
- Average order wait time
- Robot utilization proxy
- Station utilization proxy
- Completed orders
- Queue delay
- Downtime impact

## Repository Structure

```text
robotic-warehouse-simpy-simulation/
├── README.md
├── requirements.txt
└── src/
    └── warehouse_sim/
        ├── __init__.py
        └── simulation.py
```

## Run Locally

```bash
pip install -r requirements.txt
python src/warehouse_sim/simulation.py
```

## Next Build Steps

1. Add richer warehouse layout assumptions.
2. Add separate robot states: idle, traveling, picking, dropping, charging, failed.
3. Add task-priority logic and SLA rules.
4. Add scenario comparison charts.
5. Add Streamlit or Tableau dashboard.
6. Calibrate arrival and service-time distributions using operational or Kaggle-style datasets.

## Skills Demonstrated

Python, SimPy, pandas, NumPy, stochastic modeling, queueing behavior, throughput analysis, bottleneck detection, simulation experimentation, operational decision support.
