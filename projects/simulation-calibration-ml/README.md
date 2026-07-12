# Simulation Calibration with Machine Learning

## Objective

Improve simulation realism by estimating simulation parameters from historical warehouse or logistics data.

## Parameters to Calibrate

- Order arrival distribution
- Travel-time distribution
- Pick/service-time distribution
- Failure probability
- Repair-time distribution
- Charging-time distribution
- Congestion penalty

## Methods to Build

- Distribution fitting
- Regression models for travel time or service time
- Forecasting demand patterns
- Parameter search with Optuna or grid search
- Simulated-vs-observed KPI validation

## Evaluation Metrics

- Mean absolute error between simulated and observed throughput
- Cycle-time distribution similarity
- Queue-length error
- Utilization error
- Scenario ranking stability

## Business Questions

- Does the simulation match real operational behavior closely enough to support decisions?
- Which parameters most influence throughput and latency?
- How much historical data is needed for reliable calibration?
- Which assumptions are most risky?

## Skills Demonstrated

Statistics, stochastic processes, ML calibration, model validation, simulation credibility, pandas, NumPy, SciPy, scikit-learn, Optuna.
