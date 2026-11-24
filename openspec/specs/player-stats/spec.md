# player-stats Specification

## Purpose

Keeps a lasting record of weekly actual Player stat lines for every season in scope, free agents included, and scores them under a league's rules. It delivers need 6, Durable Record, and gives the simulation's error pools and WAR their actual points; the scoring formula is in `Calculations.txt`, sections 1 and 2.

## Requirements

### Requirement: 6.4 Stats coverage
The system SHALL fetch actual weekly stat lines for QB, RB, WR, TE, K and DEF for every regular-season and playoff week of the current season on each cold run, and of every season in scope on a backfill.

**Traces to:** 6
**Verified by:** Test: `tests/test_stats.py::test_refresh_scope`

#### Scenario: Current season refresh
- **WHEN** a cold run happens during 2026 week 10
- **THEN** stats for 2026 weeks 1 to 17 are requested and the played weeks stored

### Requirement: 6.4.1 Played rows only
Only stat rows carrying a points total, from Players who played, SHALL be stored.

**Traces to:** 6.4
**Verified by:** Test: `tests/test_stats.py::test_upsert_drops_did_not_play_rows_and_stores_records`; Test: `tests/test_stats.py::test_empty_or_unplayed_response_leaves_store_alone`

#### Scenario: Week not yet played
- **WHEN** the source returns rows without a points total for a future week
- **THEN** nothing is stored for that week

### Requirement: 6.4.2 One stat line per Player-week
The system SHALL store one stat record per season, week and Player, the most recent version returned, with the full stat line, Player id, position, NFL team, opponent and the source's last-modified time.

**Traces to:** 6.4
**Verified by:** Test: `tests/test_stats.py::test_upsert_keeps_newer_version_only`

#### Scenario: Stat correction
- **WHEN** a later refresh returns a newer version of a Player's week-6 stat line
- **THEN** only the newer version is stored

### Requirement: 6.4.2.1 Stats kept
A stored stat record SHALL stay stored when its week is over or the source stops returning it.

**Traces to:** 6.4.2
**Verified by:** Test: `tests/test_stats.py::test_empty_or_unplayed_response_leaves_store_alone`

#### Scenario: Source stops returning a past week
- **WHEN** the source returns no rows for a past week with stored stats
- **THEN** the stored stats for that week stay unchanged

### Requirement: 6.4.3 League-specific actual points
A Player's actual points for a league and week SHALL come from the stored stat line under that league's scoring in force that week, overrides included, and match Sleeper's credited points for at least 99% of rostered Player-weeks within 0.05 points.

**Traces to:** 6.4; 6.2.4.1
**Verified by:** Test: `tests/test_stats.py::test_actual_points_match_players_points`

#### Scenario: Matches Sleeper's credited points
- **WHEN** actual points are computed for every rostered Player-week of a stored season
- **THEN** at least 99% are within 0.05 points of the `players_points` in that week's matchups

#### Scenario: Free agent scored
- **WHEN** actual points are computed for a Player on no roster that week
- **THEN** the league's scoring is applied to his stored stat line

### Requirement: 6.4.4 Stats source failures
A failing source, or a response in an unexpected shape, SHALL leave every stored stat unchanged, the run reporting the failure.

**Traces to:** 6.4; 5.5.3
**Verified by:** Test: `tests/test_stats.py::test_source_errors_write_nothing`; Test: `tests/test_stats.py::test_bad_shape_is_a_stats_error`

#### Scenario: Endpoint error
- **WHEN** the stats endpoint returns an error or rows without the expected fields
- **THEN** no stored stat changes and the run reports the failure
