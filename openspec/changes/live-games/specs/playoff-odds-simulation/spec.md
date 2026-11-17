# Spec Delta

## ADDED Requirements

### Requirement: Frozen as-of results
Once the first game of the week after an as-of week kicks off, the stored result for that as-of week SHALL stay as it was, and later runs SHALL save a single live result per league instead. When that week becomes final, the next run SHALL store the new as-of result and remove the live result until the following week's first kickoff.

#### Scenario: Run after a kickoff
- **WHEN** a simulation runs as of week 10 after week 11's Thursday game kicked off
- **THEN** the as-of-week-10 result is left unchanged and the league's live result is replaced

#### Scenario: Week becomes final
- **WHEN** week 11 is final in Sleeper
- **THEN** the next run stores an as-of-week-11 result and removes the live result until week 12's first kickoff

## MODIFIED Requirements

### Requirement: As-of point
Each simulation SHALL run as of a given number of completed weeks: the regular-season weeks whose results are final in Sleeper. Results of completed weeks SHALL be taken from stored matchups. Every later week SHALL be simulated, except that a live run SHALL score the live week as the live-scoring capability describes.

#### Scenario: Mid-season run
- **WHEN** a simulation runs for the 2026 season with weeks 1-9 complete
- **THEN** the actual results of weeks 1-9 are fixed and weeks 10-14 plus the playoffs are simulated

#### Scenario: Week partly played
- **WHEN** a simulation runs on a Friday after the week-10 Thursday game
- **THEN** the stored as-of-week-9 result still treats week 10 as fully unplayed, and the live result uses the Thursday game's actual points

### Requirement: Odds history
The system SHALL save each simulation's per-team results, keyed by league, season and as-of week, whether the season is current or a completed season being replayed. Saving a result for a key that already has one SHALL replace it, unless that as-of week is frozen. Results for other as-of weeks and seasons SHALL be kept. Each saved result SHALL record the residual scale it was produced with.

#### Scenario: Weekly accumulation
- **WHEN** simulations have run as of weeks 0 through 10 of 2026
- **THEN** eleven sets of results are stored for each league's 2026 season

#### Scenario: Same week re-run
- **WHEN** a second simulation runs as of week 10 after a projection refresh
- **THEN** the as-of-week-10 results are replaced and the other weeks' results are unchanged

#### Scenario: Replayed season stored beside the current one
- **WHEN** the 2024 season is replayed while 2026 results are stored
- **THEN** 2024 results are stored under the 2024 season and the 2026 results are unchanged
