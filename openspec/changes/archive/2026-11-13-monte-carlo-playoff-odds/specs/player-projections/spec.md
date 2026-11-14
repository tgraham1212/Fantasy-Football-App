# Spec Delta

## Purpose

Keeps a lasting record of weekly player projections (projected stat lines) for every season in scope, and turns them into projected fantasy points under a specific league's scoring rules for a specific week.

## ADDED Requirements

### Requirement: Projection coverage
The system SHALL pull projections for fantasy positions QB, RB, WR, TE, K and DEF for every regular-season week of every season in which a configured league has a league-season. This includes weeks already played and weeks still to come.

#### Scenario: Current season refresh
- **WHEN** a refresh runs during 2026 week 10
- **THEN** projections for 2026 weeks 1 through 17 are requested

#### Scenario: Historical backfill
- **WHEN** projections are backfilled
- **THEN** projections are requested for every week of every season from 2021 onward, the earliest configured league-season

### Requirement: Latest version per player-week
The system SHALL store exactly one projection record per season, week and player: the most recent version the source returned. A newer version SHALL replace the stored one. Earlier versions SHALL NOT be kept.

#### Scenario: Projection revised
- **WHEN** a player's week-11 projection is stored and a later refresh returns a revised week-11 projection for that player
- **THEN** only the revised projection is stored for that player and week

#### Scenario: Unchanged projection
- **WHEN** a refresh returns the same projection that is already stored
- **THEN** the stored record is left as it is

### Requirement: Played weeks are kept
The system SHALL keep projection records for weeks that have been played. A record SHALL only change if the source returns a newer version, and SHALL never be deleted because the week is over.

#### Scenario: Week completes
- **WHEN** week 10 finishes and the next refresh runs
- **THEN** the week-10 projection records are still stored, updated to the latest version the source returns

#### Scenario: Source stops returning a past week
- **WHEN** the source returns no data for a past week that already has stored projections
- **THEN** the stored projections for that week stay unchanged

### Requirement: Raw stat lines and source details
Each stored projection SHALL keep the full projected stat line as the source returned it, plus the player ID, NFL team, opponent, source company and the source's last-modified time.

#### Scenario: Stored record contents
- **WHEN** a projection is stored for a running back
- **THEN** the record includes every projected stat field the source gave (e.g., rushing yards, receptions, first downs), not just precomputed point totals

### Requirement: League-specific projected points
The system SHALL compute a player's projected fantasy points for a given league and week. It SHALL multiply each projected stat by that league's scoring value for the stat, using the settings in force for that week, including manual overrides.

#### Scenario: League scoring applied
- **WHEN** projected points are computed for a kicker projected for 120 field goal yards and 3 extra points, under redraft settings with `fgm_yds` 0.1 and `xpm` 1
- **THEN** the kicker's projected points include 12 from field goal yards and 3 from extra points

#### Scenario: Same player, two leagues
- **WHEN** projected points for one player and week are computed for both the dynasty and redraft leagues
- **THEN** each result uses its own league's scoring settings

### Requirement: Missing projections
A player with no stored projection for a week SHALL count as 0 projected points for that week.

#### Scenario: Bye week
- **WHEN** a player's NFL team has a bye in week 12 and the source returns no projection
- **THEN** the player's projected points for week 12 are 0

### Requirement: Source failures leave stored data intact
If the projections source fails or returns data in an unexpected shape, the system SHALL keep the projections already stored and SHALL report the failure.

#### Scenario: Endpoint changed
- **WHEN** the projections endpoint returns an error or a response without the expected fields
- **THEN** no stored projections are changed and the run reports the failure
