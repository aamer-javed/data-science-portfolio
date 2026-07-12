# Robotic Warehouse Discrete-Event Simulation

**A public-safe, portfolio-quality simulation project for senior/principal data science roles in robotic warehouse systems, fleet optimization, operations research, and digital twins.**

This project implements a reproducible **discrete-event simulation (DES)** of a robotic warehouse operation using **Python and SimPy**. It models stochastic order arrivals, constrained robot fleet capacity, pick/drop station capacity, travel time, service time, robot failures, charging delays, queueing behavior, and SLA performance.

The goal is not to claim access to a real warehouse system or private operational data. The goal is to demonstrate how a data scientist would structure, validate, and communicate a simulation model that can support warehouse design, capacity planning, algorithm evaluation, and operational decision-making.

---

## Executive Summary

Robotic warehouse decisions are expensive to test physically. Adding robots, stations, chargers, dispatch logic, or new routing policies can change throughput, queueing, utilization, and failure behavior in non-linear ways. A simulation model gives product, robotics, and operations teams a safe way to test changes before production rollout.

This project answers questions such as:

- How much throughput is gained by adding more robots?
- When does adding robots stop helping because stations become the bottleneck?
- How does demand growth affect cycle time and SLA attainment?
- How sensitive is the system to robot failures and charging behavior?
- Which scenario provides the best operational tradeoff between throughput and utilization?

---

## What Makes This Project Interview-Ready

This project is structured like a professional modeling deliverable, not a one-off notebook.

| Area | What is included |
|---|---|
| Simulation engine | SimPy-based order arrivals, robot workers, stations, failures, charging, and event logging |
| Scenario design | Reproducible scenario matrix with demand, fleet, station, and reliability changes |
| Metrics | Throughput, cycle time, queue wait, SLA attainment, robot utilization, station utilization |
| Experimentation | Multi-replication runs with deterministic seeds for repeatability |
| Validation | Sanity checks for utilization, completed orders, service levels, and bottleneck indicators |
| Communication | Executive summary, charts, notebook, assumptions, and model design documentation |
| Engineering hygiene | Package structure, tests, requirements, Makefile, and GitHub Actions CI |

---

## Architecture

```text
robotic-warehouse-simpy-simulation/
├── README.md
├── Makefile
├── pyproject.toml
├── requirements.txt
├── configs/
│   └── scenarios.json
├── docs/
│   ├── assumptions.md
│   ├── interview_talk_track.md
│   └── model_design.md
├── notebooks/
│   └── 01_simulation_scenario_analysis.ipynb
├── reports/
│   ├── executive_summary.md
│   ├── example_outputs/
│   │   ├── demand_stress_test.csv
│   │   ├── fleet_size_sweep.csv
│   │   └── scenario_summary.csv
│   └── figures/
│       ├── throughput_by_fleet_size.svg
│       ├── cycle_time_by_demand.svg
│       └── sla_attainment_by_scenario.svg
├── src/
│   └── warehouse_sim/
│       ├── __init__.py
│       ├── config.py
│       ├── entities.py
│       ├── experiments.py
│       ├── plots.py
│       ├── simulation.py
│       └── validation.py
└── tests/
    └── test_simulation.py
```

---

## Model Scope

The current model represents a simplified goods-to-person robotic warehouse.

### Entities

- **Orders** arrive stochastically using a Poisson arrival process.
- **Robots** pull work from an order queue, travel to inventory, perform pick/drop work, may fail, and periodically charge.
- **Stations** represent constrained pick/drop capacity.
- **Queues** form when demand exceeds robot capacity or station capacity.

### Stochastic Inputs

- Order interarrival time
- Travel time
- Pick/drop station service time
- Failure occurrence
- Repair time
- Charging time

### Outputs

- Completed orders
- Throughput per hour
- Average and percentile cycle time
- Average queue wait
- SLA attainment
- Robot utilization
- Station utilization
- Queue length over time
- Bottleneck classification

---

## Result Preview

Example outputs are included under `reports/example_outputs/`. They are generated from a fixed seed and synthetic assumptions so the project is public-safe and reproducible.

### Throughput vs Fleet Size

![Throughput by fleet size](reports/figures/throughput_by_fleet_size.svg)

### Cycle Time Under Demand Stress

![Cycle time by demand](reports/figures/cycle_time_by_demand.svg)

### SLA Attainment by Scenario

![SLA attainment by scenario](reports/figures/sla_attainment_by_scenario.svg)

---

## How to Run

```bash
git clone https://github.com/aamer-javed/data-science-portfolio.git
cd data-science-portfolio/projects/robotic-warehouse-simpy-simulation

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

Run the base simulation:

```bash
python -m warehouse_sim.simulation
```

Run the full scenario experiment suite and regenerate outputs:

```bash
python -m warehouse_sim.experiments
```

Run tests:

```bash
pytest -q
```

Or use Make:

```bash
make install
make test
make run
```

---

## Example Interpretation

A typical analysis pattern from this model is:

1. **Baseline** establishes the current operating capacity.
2. **Fleet-size sweep** shows whether adding robots increases throughput or simply shifts congestion to stations.
3. **Demand stress test** identifies the arrival rate where average cycle time and SLA performance degrade.
4. **Reliability scenario** quantifies the operational cost of robot failures and repair delays.
5. **Added-station scenario** tests whether station capacity or robot capacity is the binding constraint.

The output is designed to support a recommendation like:

> The model suggests that increasing fleet size improves throughput up to the point where station utilization becomes the dominant constraint. Beyond that point, additional robots increase queueing around shared resources without proportional throughput gain. A combined strategy of fleet sizing, station capacity, and reliability improvement should be evaluated before rollout.

---

## What I Would Add in a Real Production Setting

For a production-grade digital twin, the next steps would be:

- Calibrate arrival and service distributions from historical warehouse event logs.
- Add layout-aware routing using a warehouse graph.
- Model charger resources explicitly.
- Add congestion effects and blocked aisle behavior.
- Compare dispatching policies such as nearest-robot, shortest-queue, priority/SLA, and auction-based assignment.
- Validate against observed throughput, cycle time, utilization, and station queue distributions.
- Add experiment tracking with MLflow or a database-backed scenario registry.
- Surface results through Tableau, Streamlit, or a simulation service API.

---

## Skills Demonstrated

**Simulation:** discrete-event simulation, queueing behavior, stochastic systems, replications  
**Data Science:** experimental design, metrics, validation, sensitivity analysis  
**Operations Research:** capacity planning, bottleneck analysis, fleet sizing, utilization tradeoffs  
**Engineering:** Python package structure, reproducible runs, tests, CI, documented assumptions  
**Communication:** executive summary, charts, scenario recommendations, technical design notes  

---

## Disclaimer

This is a public portfolio project using synthetic assumptions and generated outputs. It does not contain confidential employer data, operational parameters, internal layouts, production algorithms, or proprietary system behavior.
