## ADDED Requirements

### Requirement: 1.1.9.3 Upcoming pairings
For each upcoming regular-season week, a Forecast SHALL report every team's mean simulated score and, for every pair of teams, the share of runs in which each outscores the other, ties counted as half.

**Rationale:** Strength of schedule compares teams that do not meet that week, using the same simulated scores as the Forecasts.
**Traces to:** 1.1.9; 4.10.3
**Verified by:** Test: `tests/test_simulate.py::test_upcoming_pairings`

#### Scenario: Pair that does not meet
- **WHEN** a Forecast is made after week 11 and teams A and B do not meet in week 12
- **THEN** it still gives A's and B's week 12 mean scores and A's win share against B, the two shares summing to 1 within 0.001
