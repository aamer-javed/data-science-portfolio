# Warehouse Digital Twin Scenario Planner

## Objective

Build a warehouse digital twin prototype that allows users to test what-if scenarios before making physical or production system changes.

## Example Scenario Inputs

- Robot fleet size
- Pick station count
- Order arrival rate
- Travel-time assumptions
- Pick/service-time distribution
- Robot failure probability
- Charging time
- Shift length

## Example Outputs

- Expected throughput
- Average order wait time
- Robot utilization
- Station utilization
- Bottleneck classification
- Recommended capacity action
- Scenario comparison table

## Planned Interface

The first version can use a notebook. Later versions can use Streamlit or Tableau for interactive scenario testing.

## Business Questions

- Can the warehouse handle demand growth without adding stations?
- Is the bottleneck robot count, station capacity, downtime, or charging?
- Which scenario provides the best throughput improvement per added resource?
- What operational risks should be tested before production deployment?

## Skills Demonstrated

Digital twin architecture, scenario testing, capacity planning, simulation output visualization, executive communication, Python, pandas, SimPy, Streamlit/Tableau.
