"""Discrete-event simulation for a robotic warehouse fleet.

The model is intentionally compact enough to read in one sitting while still
covering the operating behaviors a senior simulation/data-science portfolio
project should demonstrate:

- stochastic order arrivals
- limited robot fleet capacity
- limited pick/drop station capacity
- travel, pick, drop-off, charging, and failure/repair time
- order-level records for