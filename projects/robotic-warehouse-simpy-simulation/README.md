# Robotic Warehouse Discrete-Event Simulation

**A public-safe, professional simulation project for robotic warehouse systems, fleet sizing, capacity planning, and operational decision support.**

This project implements a reproducible **discrete-event simulation (DES)** of a simplified robotic warehouse using **Python, SimPy, pandas, and matplotlib**. It models stochastic order arrivals, a constrained robot fleet, constrained station capacity, travel time, pick/drop service time, robot failures, charging delay, queueing behavior, SLA attainment, and bottleneck classification.

The project does **not** use private employer data or proprietary warehouse parameters. All assumptions are synthetic and documented.

---

## Executive Summary

Robotic warehouse changes are expensive to test physically. A simulation lets teams evaluate operational changes before rollout: adding robots, changing station capacity, increasing demand, improving reliability, or modifying dispatch rules.

This project is built as a modeling deliverable that a senior data scientist could discuss with robotics, software, operations, and executive stakeholders. It answers practical questions:

- How much throughput is gained by adding robots?
- Where does throughput plateau because another resource becomes constrained?
- How does demand growth affect cycle time and SLA attainment?
- How sensitive is the system to failures, charging, and station capacity?
- Which scenario has the best operational trade-off between throughput, utilization, and service level?

---

## What Makes This Professional

| Area | Implementation |
|---|---|
| Simulation engine | SimPy-based DES with order arrivals, robot workers, station resources, failures, charging, queue monitoring, and event records |
| Configuration | Typed, immutable `WarehouseConfig` with validation and scenario overrides |
| Experimentation | Deterministic scenario runner with replications, scenario sweeps, demand stress tests, CSV outputs, and charts |
| Validation | Unit tests, reproducibility checks, bottleneck rule tests, and documented validation plan |
| Engineering hygiene | Package structure, `pyproject.toml`, `requirements.txt`, tests, ruff linting, and GitHub Actions CI |
| Communication | Executive summary, result charts, notebook, model design, validation plan, and experiment protocol |

---

## Repository Structure

```text
robotic-warehouse-simpy-simulation/
├── README.md
├── pyproject.toml
├── requirements.txt
├── docs/
│   ├── experiment_protocol.md
│   ├── model_design.md
│   └── validation_plan.md
├── notebooks/
│   └── 01_simulation_scenario_analysis.ipynb
├── reports/
│   ├── executive_summary.md
│   ├── scenario_summary.csv
│   ├── fleet_size_sweep.csv
│   ├── demand_stress_test.csv
│   └── figures/
│       ├── throughput_by_fleet_size.svg
│       ├── cycle_time_by_demand.svg
│       ├── sla_attainment_by_scenario.svg
│       └── queue_length_time_series.svg
├── src/
│   └── warehouse_sim/
│       ├── __init__.py
│       ├── config.py
│       ├── entities.py
│       ├── experiments.py
│       └── simulation.py
└── tests/
    ├── test_config.py
    ├── test_experiments.py
    └── test_simulation.py
```

---

## Model Scope

The current model represents a simplified goods-to-person robotic warehouse.

### Entities

- **Orders** arrive stochastically and enter a shared queue.
- **Robots** pull work from the queue and perform travel, service, drop-off, failure recovery, and charging.
- **Stations** represent constrained pick/drop resources.
- **Monitor records** capture time-series queue and station state.
- **Order records** capture cycle time, waits, service components, failure, charging, and SLA status.

### Stochastic Inputs

- Order interarrival time
- Travel time
- Pick/service time
- Drop-off time
- Failure occurrence
- Repair time
- Charging time

### KPI Outputs

| KPI | Why it matters |
|---|---|
| Throughput per hour | Capacity and productivity |
| Average / P50 / P90 cycle time | Latency and tail-risk |
| Queue wait | Robot/task assignment pressure |
| Station wait | Station capacity pressure |
| Robot utilization | Fleet sizing and saturation |
| Station utilization | Shared-resource saturation |
| SLA attainment | Service-level risk |
| Bottleneck classification | Executive interpretation |

---

## Result Preview

### Throughput vs Fleet Size

![Throughput by fleet size](reports/figures/throughput_by_fleet_size.svg)

### Cycle Time Under Demand Stress

![Cycle time by demand](reports/figures/cycle_time_by_demand.svg)

### SLA Attainment by Scenario

![SLA attainment by scenario](reports/figures/sla_attainment_by_scenario.svg)

### Queue Length Over Time

![Queue length time series](reports/figures/queue_length_time_series.svg)

---

## How to Run

```bash
git clone https://github.com/aamer-javed/data-science-portfolio.git
cd data-science-portfolio/projects/robotic-warehouse-simpy-simulation

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

Run tests and linting:

```bash
pytest
ruff check src tests
```

Run the base simulation:

```bash
python -m warehouse_sim.simulation
```

Regenerate reports and charts:

```bash
python -m warehouse_sim.experiments
```

Open the notebook:

```bash
jupyter notebook notebooks/01_simulation_scenario_analysis.ipynb
```

---

## Example Interpretation

A typical result pattern is:

1. **Baseline** establishes the reference operating point.
2. **Fleet-size sweep** shows whether adding robots improves throughput or shifts congestion to stations.
3. **Demand stress test** identifies the arrival rate where cycle time and SLA attainment degrade.
4. **Reliability scenario** estimates the operational cost of robot failures.
5. **Added-station scenario** tests whether station capacity is the dominant constraint.

Example recommendation style:

> The model suggests that adding robots improves throughput only until another shared resource becomes limiting. Once station utilization and queueing rise, additional robots alone have diminishing returns. The next scenario set should evaluate combined fleet sizing, station capacity, reliability improvement, and dispatch-policy changes before physical rollout.

---

## Documentation

- [Model design](docs/model_design.md)
- [Validation plan](docs/validation_plan.md)
- [Experiment protocol](docs/experiment_protocol.md)
- [Executive summary](reports/executive_summary.md)

---

## Production Upgrade Path

For a production-grade digital twin, next steps would include:

- Calibrate arrival and service distributions from historical warehouse event logs.
- Add layout-aware routing using a warehouse graph.
- Model charger resources explicitly.
- Add congestion and blocked-aisle effects.
- Compare dispatching policies: nearest robot, shortest queue, priority/SLA, auction-based assignment.
- Validate simulated KPIs against observed throughput, cycle time, utilization, and queue distributions.
- Add experiment tracking with MLflow or a database-backed scenario registry.
- Surface results through Tableau, Streamlit, or a simulation service API.

---

## Skills Demonstrated

**Simulation:** DES, stochastic systems, queueing, replications, sensitivity analysis  
**Data Science:** experimental design, KPI design, validation, interpretation  
**Operations Research:** capacity planning, bottleneck analysis, fleet sizing, utilization trade-offs  
**Engineering:** Python package structure, tests, CI, reproducible experiment runner  
**Communication:** executive summary, charts, scenario recommendations, model limitations  

---

## Disclaimer

This is a public portfolio project using synthetic assumptions and generated outputs. It does not contain confidential employer data, operational parameters, internal layouts, production algorithms, or proprietary system behavior.
