# Spec Delta

## Purpose

Captures and stores ESPN start-percentage snapshots for every player, per season and per week, and links ESPN players to Sleeper player IDs so other features can rank players by how widely they are started.

## ADDED Requirements

### Requirement: Season snapshot
For every season a configured league has stored, the system SHALL store one start-percentage snapshot holding, per ESPN player, the ESPN id, name, position, NFL team, percent started and percent owned. A season snapshot SHALL be fetched only when none is stored for that season.

#### Scenario: Backfill past seasons
- **WHEN** the snapshot command runs with no snapshots stored and leagues stored for 2021 to 2026
- **THEN** one season snapshot per season from 2021 to 2026 is written

#### Scenario: Stored season not re-fetched
- **WHEN** the snapshot command runs and 2024 already has a season snapshot
- **THEN** 2024 is not requested again and its stored snapshot is unchanged

### Requirement: Weekly snapshot
Every run of the snapshot command during a season SHALL store a start-percentage snapshot for the current NFL week as reported by Sleeper, replacing any earlier snapshot for that same week, so the last capture of a week is the one kept. Past weeks SHALL never be overwritten.

#### Scenario: Daily captures within one week
- **WHEN** the command runs on Thursday, Sunday and Monday while Sleeper reports week 11
- **THEN** a single week-11 snapshot is stored holding Monday's values

#### Scenario: Week rolls over
- **WHEN** Sleeper reports week 12 and a week-11 snapshot exists
- **THEN** a week-12 snapshot is written and the week-11 snapshot is left as it was

#### Scenario: Offseason
- **WHEN** the command runs while Sleeper reports no season in progress
- **THEN** no weekly snapshot is written and the command succeeds

### Requirement: Snapshot source failures leave stored data intact
If the ESPN request fails or returns data in an unexpected shape, the system SHALL keep every stored snapshot and SHALL report the failure. Requests to ESPN SHALL carry a generic client identifier and no league, user or personal identifiers.

#### Scenario: ESPN unavailable
- **WHEN** ESPN returns an error for every retry
- **THEN** no snapshot file is written or removed and the command reports the failure

### Requirement: Player crosswalk
The system SHALL map each ESPN player in a snapshot to a Sleeper player ID using, in order: Sleeper's stored ESPN id, an alias table of known name differences, then a normalised name and position match with the NFL team as tiebreak. Defenses SHALL map by NFL team. A player with no match SHALL be left unmapped rather than guessed.

#### Scenario: Suffix and punctuation differences
- **WHEN** ESPN lists "Travis Etienne Jr." and Sleeper lists "Travis Etienne" at RB
- **THEN** the two are matched

#### Scenario: Known alias
- **WHEN** ESPN lists "Kenneth Gainwell" and Sleeper lists "Kenny Gainwell"
- **THEN** the alias table matches them

#### Scenario: Same name, two players
- **WHEN** two Sleeper players share a normalised name and position and only one is on the ESPN player's NFL team
- **THEN** that one is matched

#### Scenario: Ambiguous
- **WHEN** two Sleeper players share the name, position and team
- **THEN** the ESPN player is left unmapped

### Requirement: Unmatched report
Each snapshot run SHALL report every unmapped ESPN player whose percent started is at least 2, naming the player, position, season or week and the percentage, so the alias table can be extended.

#### Scenario: Report after capture
- **WHEN** a 2025 season snapshot leaves a 64%-started running back unmapped
- **THEN** the run output names him with his position and percentage
