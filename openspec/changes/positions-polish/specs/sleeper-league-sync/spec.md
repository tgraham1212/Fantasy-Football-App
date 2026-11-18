## MODIFIED Requirements

### Requirement: Owner identity
The system SHALL link each roster in each league-season to its owner's Sleeper user ID and display name. Owners SHALL be identified by user ID, not roster slot.

A roster stored with no owner in a season (a vacant roster) SHALL be read as owned by the most recent owner of that roster slot in an earlier stored season of the same league, with that owner's display name and team name as last stored. When no earlier season has an owner for the slot, the first later owner SHALL be used. A roster with no owner in any stored season SHALL stay vacant. Every reader of stored rosters and users SHALL see the inherited owner. The stored files SHALL keep Sleeper's data as fetched.

Rationale: a manager who quits before the league year officially ends leaves a roster Sleeper reports with no owner, although that manager played the season. Dynasty 2023 roster 11 is the case in the stored data: owned by DeekBurg in 2022, empty in 2023, taken over in 2024.

#### Scenario: Owner turnover
- **WHEN** roster slot 4 has a different owner in 2022 than in 2026
- **THEN** the stored data shows two different owners for that slot in those seasons

#### Scenario: Owner quit before the year ended
- **WHEN** roster 11 is owned by DeekBurg in 2022, has no owner in 2023, and is owned by another user in 2024
- **THEN** roster 11 reads as DeekBurg's in 2023, with his name and team name from 2022

#### Scenario: Vacant in the first stored season
- **WHEN** a roster has no owner in 2021, the first stored season, and is owned by a user from 2022
- **THEN** it reads as that user's in 2021

#### Scenario: Never owned
- **WHEN** a roster has no owner in any stored season
- **THEN** it stays vacant

#### Scenario: Stored files untouched
- **WHEN** a vacant roster is read with an inherited owner
- **THEN** the stored rosters and users files are unchanged
