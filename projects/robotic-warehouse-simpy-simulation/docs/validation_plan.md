# Validation Plan

Simulation is useful only when the model is explicit about what has been validated and what still needs calibration. This document defines a practical validation path for the project.

## 1. Code-Level Validation

Implemented through unit tests and CI:

- Configuration validation rejects impossible inputs.
- A small scenario produces non-empty order, monitor, and summary outputs.
- Results are reproducible for the same seed and replication.
- Bottleneck classification rules are deterministic.
- The experiment runner writes the expected CSV and chart artifacts.

## 2. Face Validity Checks

The model should behave in ways that are directionally reasonable:

| Change | Expected behavior |
|---|---|
| Add robots | Throughput improves until another constraint dominates |
| Increase demand | Cycle time and queue wait increase |
| Add stations | Station wait decreases when stations are constrained |
| Increase failure probability | Cycle time and SLA risk increase |
| Increase charging delay | Robot utilization and cycle time pressure increase |

## 3. Extreme-Case Tests

Future test cases should cover:

- Very low demand: queues should remain near zero.
- Very high demand: queue length should grow and SLA attainment should fall.
- Very high station capacity: station wait should approach zero.
- Very high robot count: station capacity should become the limiting constraint.
- Zero failure probability: failure rate should be zero.

## 4. Calibration Plan

A production-grade version would estimate parameters from historical telemetry:

| Parameter | Calibration approach |
|---|---|
| Order arrival rate | Fit arrival distribution by hour, site, shift, or business condition |
| Travel time | Fit distribution by distance band or route class |
| Station service time | Fit distribution by station type and task type |
| Failure probability | Estimate from task-level error/fault logs |
| Charging delay | Estimate from battery and charger utilization logs |
| SLA threshold | Align with operational or product-level target |

## 5. Backtesting Plan

A calibrated model should be backtested against held-out historical periods:

1. Fit parameters on historical period A.
2. Simulate historical period B using observed demand inputs.
3. Compare simulated and observed throughput, cycle time, utilization, and queue depth.
4. Report error metrics and confidence intervals.
5. Identify where the model is biased and update assumptions.

## 6. Governance and Reproducibility

For interview and portfolio use, this project now includes:

- Deterministic random seeds
- Scenario configuration objects
- Repeatable experiment runner
- Unit tests
- GitHub Actions CI
- Public-safe assumptions and disclaimers
