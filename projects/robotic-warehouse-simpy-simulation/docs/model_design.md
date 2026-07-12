# Model Design

## Purpose

This project is a public-safe discrete-event simulation of a robotic warehouse operation. It is built to show how operational behavior can be translated into a computational model that supports scenario testing, capacity planning, and bottleneck analysis.

The model is intentionally compact, but it follows the same structure used in professional simulation work:

1. Define the system boundary.
2. Identify entities, resources, events, and state variables.
3. Specify stochastic assumptions.
4. Run controlled experiments.
5. Report operational KPIs with clear limitations.

## System Boundary

The modeled system begins when an order/task enters the warehouse queue and ends when the assigned robot completes travel, station processing, drop-off, and any charging or failure-related delay.

The current model includes:

- Order arrivals
- Shared order queue
- Robot fleet capacity
- Pick/drop station capacity
- Travel time
- Pick/service time
- Drop-off time
- Robot failure and repair delay
- Charging delay after a configurable number of tasks
- Queue and station monitoring snapshots

The current model does not yet include:

- Physical warehouse layout
- Collision avoidance
- SKU-level inventory constraints
- Human labor schedule constraints
- Real-time dispatch policy learning
- Calibration from production telemetry

Those are intentionally listed as future enhancements so the project does not overclaim realism.

## Entities

| Entity | Description |
|---|---|
| Order | A unit of work entering the warehouse system |
| Robot | A worker process that pulls orders from the queue |
| Pick/drop station | A constrained resource where service time is incurred |
| Monitor record | Time-series snapshot of queue and station state |
| Order record | Completed order-level event record used for KPI analysis |

## Events

| Event | Modeled behavior |
|---|---|
| Order arrival | Poisson-style stochastic arrival process |
| Robot assignment | Robot pulls the next available order from the shared queue |
| Travel | Stochastic travel duration |
| Failure/repair | Optional delay based on per-task failure probability |
| Station request | Robot waits for constrained station capacity |
| Pick/service | Stochastic service time at station |
| Drop-off | Stochastic completion delay |
| Charging | Optional delay after a configured number of tasks |

## Outputs

The model produces three output tables:

| Output | Purpose |
|---|---|
| `order_level_results.csv` | Order-level cycle time, waits, service times, failures, charging, SLA flag |
| `queue_time_series.csv` | Periodic queue and station snapshots |
| `scenario_summary.csv` | Executive-level KPIs by scenario |

## KPI Definitions

| KPI | Interpretation |
|---|---|
| Throughput per hour | Completed orders divided by simulated hours |
| Average cycle time | Mean time from order creation to completion |
| P90 cycle time | Tail-latency indicator for operational risk |
| Queue wait | Time before a robot starts processing an order |
| Station wait | Time waiting for constrained station capacity |
| Robot utilization | Share of available robot time spent working |
| Station utilization | Share of available station time spent processing |
| SLA attainment | Share of completed orders under the configured SLA threshold |

## Public-Safe Assumption Policy

All parameters are synthetic. The project does not use private employer data, real warehouse layout, actual throughput rates, production failure rates, customer volumes, or proprietary dispatch rules.
