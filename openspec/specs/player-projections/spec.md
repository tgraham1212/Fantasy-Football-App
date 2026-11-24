# player-projections Specification

## Purpose

Keeps a lasting record of weekly Player Projections (projected stat lines) for every season in scope, and turns them into projected fantasy points under a league's scoring for a week. It delivers need 6, Durable Record, and feeds the simulation (need 1); the scoring formula is in `Calculations.txt`, sections 1 and 2.

## Requirements

### Requirement: 6.3 Projection coverage
The system SHALL fetch Projections for QB, RB, WR, TE, K and DEF for every regular-season week of every season a configured league has, played weeks and weeks to come alike.

**Traces to:** 6; 1.1.5
**Verified by:** Test: `tests/test_sleeper.py::test_projections_url_lists_all_positions`; Inspection: `src/ffapp/projections.py`, each refresh requests every regular-season week of the current season

#### Scenario: Current season refresh
- **WHEN** a refresh runs during 2026 week 10
- **THEN** Projections for 2026 weeks 1 to 17 are requested

#### Scenario: Historical backfill
- **WHEN** Projections are backfilled
- **THEN** every week of every season from 2021, the earliest league-season, is requested

### Requirement: 6.3.1 Latest version per Player-week
The system SHALL store exactly one Projection per season, week and Player, the most recent version the source returned replacing the stored one.

**Traces to:** 6.3
**Verified by:** Test: `tests/test_projections.py::test_upsert_replaces_only_newer_versions`; Test: `tests/test_projections.py::test_upsert_unchanged_when_same_version`

#### Scenario: Projection revised
- **WHEN** a later refresh returns a revised week-11 Projection for a Player
- **THEN** only the revised Projection is stored for that Player and week

### Requirement: 6.3.2 Played weeks kept
A stored Projection SHALL stay stored after its week is played, changing only when the source returns a newer version.

**Traces to:** 6.3; 6.3.1
**Verified by:** Test: `tests/test_projections.py::test_upsert_empty_response_leaves_file_untouched`

#### Scenario: Source stops returning a past week
- **WHEN** the source returns no data for a past week that has stored Projections
- **THEN** the stored Projections for that week stay unchanged

### Requirement: 6.3.3 Full stat lines kept
Each stored Projection SHALL keep the full projected stat line as returned, with the Player id, NFL team, opponent, game date, source company and the source's last-modified time.

**Rationale:** Points are computed from the stat line under each league's own scoring.
**Traces to:** 6.3
**Verified by:** Test: `tests/test_projections.py::test_upsert_drops_adp_only_rows_and_stores_records`; Test: `tests/test_projections.py::test_record_without_a_date_still_loads`

#### Scenario: Stored record contents
- **WHEN** a Projection is stored for a running back
- **THEN** the record holds every projected stat field the source gave, not only point totals

### Requirement: 6.3.4 League-specific projected points
A Player's projected points for a league and week SHALL be each projected stat times that league's scoring value for the stat in force that week, overrides included.

**Rationale:** Calculations.txt section 1.
**Traces to:** 6.3; 1.1.5; 6.2.4.1
**Verified by:** Test: `tests/test_scoring.py::test_kicker_field_goal_yards_and_extra_points`; Test: `tests/test_scoring_live_data.py::test_scored_projections_match_sleeper_half_ppr`

#### Scenario: League scoring applied
- **WHEN** a kicker is projected for 120 field goal yards and 3 extra points, under redraft settings with `fgm_yds` 0.1 and `xpm` 1
- **THEN** his projected points include 12 from field goal yards and 3 from extra points

### Requirement: 6.3.4.1 Missing Projection
A Player with no stored Projection for a week SHALL count as 0 projected points that week.

**Traces to:** 6.3.4
**Verified by:** Test: `tests/test_scoring.py::test_missing_projection_counts_as_zero`

#### Scenario: Bye week
- **WHEN** a Player's team has a bye in week 12 and the source returns no Projection
- **THEN** his projected points for week 12 are 0

### Requirement: 6.3.5 Projection source failures
A failing source, or a response in an unexpected shape, SHALL leave every stored Projection unchanged, the run reporting the failure.

**Traces to:** 6.3
**Verified by:** Test: `tests/test_projections.py::test_source_errors_write_nothing`; Test: `tests/test_projections.py::test_validate_rejects_bad_shapes`

#### Scenario: Endpoint changed
- **WHEN** the Projections endpoint returns an error or a response without the expected fields
- **THEN** no stored Projection changes and the run reports the failure
