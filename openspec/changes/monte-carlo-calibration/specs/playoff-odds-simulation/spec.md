# Spec Delta

## MODIFIED Requirements

### Requirement: Score noise from past results
A player's simulated score SHALL be the player's projected points plus a random error. Errors SHALL be drawn from stored past differences between projected and actual points for players at the same position with similar projections, multiplied by the configured residual scale (1.0 unless set). Actual points SHALL come from stored matchups.

#### Scenario: Error pool
- **WHEN** a WR projected for 14 points is simulated
- **THEN** the error is drawn from past actual-minus-projected differences for WRs with projections near 14 points

#### Scenario: Few past results
- **WHEN** a position and projection range has fewer past results than the minimum pool size
- **THEN** errors are drawn from that position's results across all projection ranges

#### Scenario: Residual scale not configured
- **WHEN** the configuration has no residual scale
- **THEN** errors are used exactly as stored, and results are identical to those before the scale existed

#### Scenario: Residual scale configured
- **WHEN** the residual scale is set to 1.2 and a sampled residual is +5.0 points
- **THEN** the error applied is +6.0 points

### Requirement: Odds history
The system SHALL save each simulation's per-team results, keyed by league, season and as-of week, whether the season is current or a completed season being replayed. Saving a result for a key that already has one SHALL replace it. Results for other as-of weeks and seasons SHALL be kept. Each saved result SHALL record the residual scale it was produced with.

#### Scenario: Weekly accumulation
- **WHEN** simulations have run as of weeks 0 through 10 of 2026
- **THEN** eleven sets of results are stored for each league's 2026 season

#### Scenario: Same week re-run
- **WHEN** a second simulation runs as of week 10 after a projection refresh
- **THEN** the as-of-week-10 results are replaced and the other weeks' results are unchanged

#### Scenario: Replayed season stored beside the current one
- **WHEN** the 2024 season is replayed while 2026 results are stored
- **THEN** 2024 results are stored under the 2024 season and the 2026 results are unchanged
