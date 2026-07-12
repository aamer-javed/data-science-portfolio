# Digital Twin Enhancements

This document explains the second professional layer added to the robotic warehouse DES project.

## Implemented capabilities

### 1. Grid-based warehouse layout

The simulation now uses a synthetic rectangular grid with:

- Inbound location
- Outbound location
- Storage cells
- Pick/drop stations
- Charging stations

Travel distance is calculated using Manhattan distance. This keeps the model simple and reviewable while making travel time depend on layout instead of a fixed random duration.

### 2. Task assignment rules

The model supports transparent dispatching policies:

| Policy | Behavior |
|---|---|
| `fifo` | Assigns the oldest order first |
| `priority_fifo` | Prioritizes urgent work, then FIFO |
| `nearest_robot` | Chooses the order closest to the robot's current location |
| `shortest_queue_priority` | Combines priority work, distance, and queue pressure |

These are baseline policies, not claims of production optimality. They are intentionally simple so they can be compared against future optimization or RL policies.

### 3. Congestion-aware travel time

Travel time is based on grid distance and a congestion multiplier derived from order queue length, station queue length, and charger queue length.

This provides a simple way to show how the same route can take longer when the system is crowded.

### 4. Charging station constraints

Charging is now modeled as a constrained SimPy resource. Robots must queue for a charger when the charging station pool is saturated.

The model records:

- Charging wait time
- Charger utilization
- Charging-constrained bottleneck classification

### 5. Calibration workflow

The `calibration.py` module estimates simulation inputs from public-safe, Kaggle-style event logs. It can estimate:

- Arrival rate
- Mean travel time
- Mean pick time
- Mean drop-off time
- Failure probability
- Mean repair time

The sample file under `data/sample/kaggle_style_event_log.csv` demonstrates the expected shape.

### 6. Historical KPI validation

The model now includes a validation pattern that compares simulated KPIs against historical KPI targets.

The output file `historical_kpi_validation_error.csv` shows signed and absolute error for shared metrics.

### 7. Streamlit digital twin dashboard

The dashboard under `app/streamlit_app.py` allows interactive scenario planning across:

- Robot count
- Station count
- Charging station count
- Demand rate
- Dispatching policy
- Congestion sensitivity
- Failure rate
- Charging threshold

Run it with:

```bash
streamlit run app/streamlit_app.py
```

## Production upgrade path

A production-grade version would add:

1. Real warehouse graph with restricted paths and blocked aisles.
2. Calibrated time distributions by site, zone, shift, bot generation, and SKU/order class.
3. Real dispatching policy replay from event logs.
4. Experiment tracking in MLflow or a database-backed scenario registry.
5. Scenario review workflow with versioned configs and approval status.
6. Integration with Tableau/Grafana for executive and operator-facing views.
