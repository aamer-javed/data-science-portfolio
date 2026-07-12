# Experiment Protocol

This protocol explains how to run and interpret the robotic warehouse simulation experiments.

## Local Setup

```bash
cd projects/robotic-warehouse-simpy-simulation
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## Run Tests

```bash
pytest
ruff check src tests
```

## Regenerate Reports and Charts

```bash
python -m warehouse_sim.experiments
```

This writes the following artifacts:

```text
reports/
├── order_level_results.csv
├── queue_time_series.csv
├── scenario_summary.csv
├── fleet_size_sweep.csv
├── demand_stress_test.csv
└── figures/
    ├── throughput_by_fleet_size.svg
    ├── cycle_time_by_demand.svg
    ├── sla_attainment_by_scenario.svg
    └── queue_length_time_series.svg
```

## Standard Scenario Set

| Scenario | Purpose |
|---|---|
| baseline | Reference operating point |
| fewer_robots | Tests robot fleet capacity sensitivity |
| more_robots | Tests whether more robots improve throughput |
| demand_plus_25pct | Tests moderate demand growth |
| demand_plus_50pct | Tests stress behavior near capacity |
| more_stations | Tests station capacity improvement |
| higher_failure_rate | Tests reliability sensitivity |

## Recommended Interview Talking Points

When discussing this project, focus on the modeling process rather than claiming it is a full production digital twin:

- I defined entities, resources, events, queues, and KPIs.
- I separated model configuration from simulation execution.
- I used deterministic seeds and replicated scenarios for reproducibility.
- I built a repeatable experiment runner with CI tests.
- I documented assumptions, limitations, and a calibration path.
- The current model is public-safe and synthetic; production value would come from calibration against real telemetry.

## Next Technical Upgrades

1. Add layout-aware routing using a grid graph.
2. Add task assignment policies such as nearest-robot and workload-balanced dispatch.
3. Add confidence intervals across scenario replications.
4. Fit arrival and service-time distributions from historical or Kaggle-style data.
5. Add a Streamlit scenario planner for non-technical stakeholders.
