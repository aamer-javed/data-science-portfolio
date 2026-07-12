# Multi-Agent Robot Fleet Optimization

## Objective

Model a warehouse robot fleet as a multi-agent system and compare task assignment and routing strategies under capacity, congestion, and travel-time constraints.

## Key Methods

- Grid-world warehouse representation
- A* or Dijkstra shortest-path routing
- Nearest-robot assignment baseline
- Hungarian assignment / min-cost matching
- Congestion-aware dispatching heuristic
- Fleet-size sensitivity analysis

## Business Questions

- Which dispatching strategy minimizes order cycle time?
- How many robots are needed before additional robots stop improving throughput?
- Which zones or aisles create congestion?
- How does assignment logic impact robot idle time and SLA misses?

## Planned Deliverables

- Clean Python implementation of routing and assignment baselines
- Scenario runner for different fleet sizes and demand levels
- KPI comparison table
- Congestion heatmap or path utilization chart
- Executive summary: recommended dispatching strategy and tradeoffs

## Skills Demonstrated

Multi-agent systems, routing, task allocation, optimization heuristics, graph algorithms, pandas, NumPy, matplotlib, operational decision support.
