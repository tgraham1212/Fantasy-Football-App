# player-stats Specification

## Purpose

Keeps a lasting record of weekly actual player stat lines for every season in scope, covering free agents as well as rostered players, and scores them under a specific league's rules.

## Requirements

### Requirement: Stats coverage
The system SHALL pull actual weekly stat lines for fantasy positions QB, RB, WR, TE, K and DEF for every regular-season and playoff week of the current season on each refresh, and for every week of every season in scope when a backfill is requested. Only rows that carry a points total (players who played) SHALL be stored.

#### Scenario: Current season refresh
- **WHEN** a refresh runs during 2026 week 10
- **THEN** stats for 2026 weeks 1 through 17 are requested and the weeks with played games are stored

#### Scenario: Historical backfill
- **WHEN** stats are backfilled
- **THEN** stats are requested for every week of every season from 2021 onward

#### Scenario: Week not yet played
- **WHEN** the source returns rows without a points total for a future week
- **THEN** nothing is stored for that week

### Requirement: One stat line per player-week
The system SHALL store exactly one stat record per season, week and player: the most recent version the source returned, keeping the full stat line plus the player ID, position, NFL team, opponent and the source's last-modified time. A newer version (a stat correction) SHALL replace the stored one; a stored record SHALL never be deleted because the week is over or the source stops returning it.

#### Scenario: Stat correction
- **WHEN** a player's week-6 stat line is stored and a later refresh returns a newer version
- **THEN** only the newer version is stored for that player and week

#### Scenario: Source stops returning a past week
- **WHEN** the source returns no rows for a past week that already has stored stats
- **THEN** the stored stats for that week stay unchanged

### Requirement: League-specific actual points
The system SHALL compute a player's actual fantasy points for a given league and week from the stored stat line and that league's scoring settings in force for that week, including manual overrides, so that the result reproduces the points Sleeper credited for rostered players.

#### Scenario: Matches Sleeper's credited points
- **WHEN** actual points are computed for every rostered player-week of a stored season
- **THEN** at least 99% of them are within 0.05 points of the `players_points` Sleeper stored in that week's matchups

#### Scenario: Free agent scored
- **WHEN** actual points are computed for a player who was on no roster that week
- **THEN** the league's scoring is applied to that player's stored stat line

### Requirement: Stats source failures leave stored data intact
If the stats source fails or returns data in an unexpected shape, the system SHALL keep the stats already stored and SHALL report the failure.

#### Scenario: Endpoint error
- **WHEN** the stats endpoint returns an error or rows without the expected fields
- **THEN** no stored stats are changed and the run reports the failure
