## ADDED Requirements

### Requirement: 2.8.2 Lineup choices for past seasons
For every finished week of a past season, the system SHALL compute each team's lineup choices from the stored weekly Projections, the stored matchup rosters and that week's realised replacement level.

**Rationale:** The game log behind lineup choices began in 2026; the season league records for lineup choices cover every season.
**Traces to:** 2.8; 4.8.6
**Verified by:** Test: `tests/test_views.py::test_past_season_lineup_choices`

#### Scenario: 2023 week 5
- **WHEN** the build runs after this change
- **THEN** every team in 2023 week 5 has lineup choices computed from that week's stored Projections
