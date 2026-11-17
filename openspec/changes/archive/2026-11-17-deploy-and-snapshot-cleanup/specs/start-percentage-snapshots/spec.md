# Spec Delta

## MODIFIED Requirements

### Requirement: Season snapshot
For every season a configured league has stored, the system SHALL store one start-percentage snapshot holding, per ESPN player, the ESPN id, name, position, NFL team, percent started and percent owned. A season snapshot SHALL be fetched when none is stored, and again on every run while any configured league has that season in progress. A season every configured league has stored as complete SHALL NOT be fetched again.

#### Scenario: Backfill past seasons
- **WHEN** the snapshot command runs with no snapshots stored and leagues stored for 2021 to 2026
- **THEN** one season snapshot per season from 2021 to 2026 is written

#### Scenario: Stored season not re-fetched
- **WHEN** the snapshot command runs and 2024 already has a season snapshot
- **THEN** 2024 is not requested again and its stored snapshot is unchanged

#### Scenario: Season in progress refreshed
- **WHEN** the snapshot command runs while 2026 is in season for a configured league and a 2026 season snapshot is stored
- **THEN** 2026's season snapshot is fetched again and replaced with the new values

#### Scenario: Frozen on completion
- **WHEN** every configured league has 2026 stored as complete
- **THEN** the 2026 season snapshot is left as last captured and not requested again

#### Scenario: Refresh fails
- **WHEN** the in-progress season's fetch fails
- **THEN** the stored season snapshot is kept and the failure is reported
