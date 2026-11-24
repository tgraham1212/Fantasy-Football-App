## ADDED Requirements

### Requirement: 1.1.8.1 Supported playoff size
The simulation SHALL stop with an error naming the league, the season and the configured playoff size whenever a league's Sleeper settings give a playoff size other than six teams.

**Rationale:** The bracket logic plays only six-team brackets; a wrong Forecast is worse than none.
**Traces to:** 1.1.8
**Verified by:** Test: `tests/test_odds.py::test_unsupported_playoff_size_fails_loudly`

#### Scenario: League moves to eight playoff teams
- **WHEN** a league's settings give 8 playoff teams
- **THEN** the run stops with an error naming the league, the season and the size 8, and the published Forecasts stay as they were

#### Scenario: Six-team league
- **WHEN** a league's settings give 6 playoff teams
- **THEN** the simulation runs as before
