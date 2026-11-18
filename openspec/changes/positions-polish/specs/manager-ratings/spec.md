## MODIFIED Requirements

### Requirement: Ratings follow the manager
Ratings SHALL be keyed by the roster owner's Sleeper user ID for that season, not by roster slot, so a manager keeps one rating across roster changes and former members keep their last rating. A roster with no owner on record SHALL be rated under the owner it inherits (the most recent earlier owner of that roster slot, else the first later one). Only a roster with no owner in any stored season SHALL be rated as a distinct vacant manager for that season, so the week's ranking stays complete, and SHALL be marked as vacant.

#### Scenario: Roster slot changes hands
- **WHEN** roster 4 is owned by one user in 2023 and another in 2024
- **THEN** each user's rating covers only the seasons they owned a roster

#### Scenario: Former member
- **WHEN** a manager last played in 2023
- **THEN** their rating history ends at their last rated week and is still stored

#### Scenario: Vacant roster with an earlier owner
- **WHEN** dynasty roster 11 has no owner in 2023 and was DeekBurg's in 2022
- **THEN** its 2023 weeks are rated as DeekBurg's, continuing his rating history

#### Scenario: Vacant roster
- **WHEN** a 2023 roster has no owner in any stored season
- **THEN** its weekly points still rank against the other teams, under a vacant entry for that season marked as not a manager
