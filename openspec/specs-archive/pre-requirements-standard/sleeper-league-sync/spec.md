# sleeper-league-sync Specification

## Purpose

Keeps a complete local copy of each configured Sleeper league's history, including settings, owners, rosters, matchups and brackets for every season. Downstream features can then work from stored data instead of calling Sleeper live.

## Requirements

### Requirement: Configured leagues
The system SHALL read the leagues to track from a configuration file. Each entry gives a league's current Sleeper league ID and a short display key. The file MAY also carry an optional simulation section with a residual scale (positive number, default 1.0), a replacement top-N (positive integer, default 3) and prior weeks for the season replacement value (non-negative number, default 4); any other value SHALL be rejected as a configuration error.

#### Scenario: Both leagues configured
- **WHEN** the configuration lists dynasty league `1339662153812025344` and redraft league `1389347876550770688`
- **THEN** a sync pulls data for both leagues and for no others

#### Scenario: New season for the redraft league
- **WHEN** the redraft league renews and the configuration is changed to the new season's league ID
- **THEN** the next sync follows the history chain back through all prior seasons, and the league keeps its display key and earlier history

#### Scenario: Residual scale configured
- **WHEN** the configuration's simulation section sets the residual scale to 0.9
- **THEN** the configuration loads with a residual scale of 0.9

#### Scenario: Invalid residual scale
- **WHEN** the residual scale is set to 0, a negative number or text
- **THEN** loading the configuration fails with an error naming the residual scale

#### Scenario: Replacement settings configured
- **WHEN** the simulation section sets the replacement top-N to 5 and prior weeks to 2
- **THEN** the configuration loads with those values, and absent keys keep the defaults 3 and 4

#### Scenario: Invalid replacement settings
- **WHEN** the replacement top-N is 0 or a fraction, or prior weeks is negative
- **THEN** loading the configuration fails with an error naming the key

### Requirement: Full season history
For each configured league, the system SHALL follow `previous_league_id` back to the earliest season Sleeper has. It SHALL store every season as a separate league-season.

#### Scenario: Dynasty history
- **WHEN** the dynasty league is synced
- **THEN** league-seasons 2022 through 2026 are stored, each with its own Sleeper league ID

#### Scenario: Chain ends
- **WHEN** a league-season's `previous_league_id` is empty, null or `0`
- **THEN** the sync treats that season as the earliest and stops walking

### Requirement: League data per season
For each league-season, the system SHALL store the league settings, users, rosters, weekly matchups for every regular-season and playoff week, and the winners and losers brackets.

#### Scenario: Completed season
- **WHEN** a completed league-season is synced
- **THEN** matchups for every week from the start week through the final playoff week, and both brackets, are stored for it

#### Scenario: Season in progress
- **WHEN** the in-progress 2026 league-season is synced during week 10
- **THEN** matchups for weeks 1 through 9 are stored with scores, and any matchup data Sleeper returns for later weeks is stored as unplayed

### Requirement: Settings stored per season
The system SHALL store scoring settings, roster slots and playoff settings for each league-season. It SHALL never assume one season's settings apply to another.

#### Scenario: Settings differ between seasons
- **WHEN** the dynasty FAAB budget is 100 in 2024 and 150 in 2025
- **THEN** each league-season's stored settings show its own value

### Requirement: Manual settings overrides
The system SHALL accept manual overrides from configuration that replace specific scoring settings for one league-season, starting at a given week. Weeks before that week SHALL use the stored Sleeper settings.

#### Scenario: Mid-season scoring change
- **WHEN** an override sets `fgm_yds` to 0.1 for the redraft 2023 season starting at week 6
- **THEN** settings resolved for weeks 1-5 use Sleeper's stored values, and settings resolved for weeks 6 onward use 0.1

#### Scenario: No overrides
- **WHEN** no override applies to a league-season
- **THEN** settings resolved for any week of that season equal Sleeper's stored settings

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

### Requirement: Completed seasons are not re-fetched
Once a league-season is stored with status `complete`, the system SHALL NOT fetch it again unless a full re-sync is explicitly requested.

#### Scenario: Routine sync
- **WHEN** a scheduled sync runs and the 2022-2025 seasons are already stored as complete
- **THEN** only the current in-progress season is fetched from Sleeper

#### Scenario: Forced re-sync
- **WHEN** a full re-sync is explicitly requested
- **THEN** every league-season is fetched again and the stored copies are replaced

### Requirement: Sync failures leave stored data intact
If a Sleeper request fails, the system SHALL keep the data stored from the last successful sync for that league-season and SHALL report the failure.

#### Scenario: Sleeper unavailable
- **WHEN** Sleeper returns errors for every request during a sync
- **THEN** the previously stored data is unchanged and the run reports the failure with a non-zero exit status

### Requirement: Transactions stored
For each league-season, the system SHALL store Sleeper's transactions for every week of the season, one file per week: waiver claims (won and failed, with their bids), free-agent moves, trades (players, draft picks and FAAB sent) and commissioner moves.

#### Scenario: Week saved
- **WHEN** week 11 of the 2026 redraft season is synced
- **THEN** its won and failed waiver claims, free-agent moves and trades are saved in that week's transactions file

### Requirement: Transactions fetch schedule
A season stored as complete SHALL have its transactions fetched once, including seasons stored before transactions were kept. The current season's transactions SHALL be fetched again on every sync. A failed transactions fetch SHALL keep the files stored last time, report a warning, and never stop the sync or the refresh.

#### Scenario: Backfill of a completed season
- **WHEN** the 2023 dynasty season is stored as complete with no transactions
- **THEN** the next sync fetches and stores its transactions once, and later syncs do not fetch them again

#### Scenario: Current season
- **WHEN** a waiver run settles on Wednesday of week 11
- **THEN** the next sync stores the week's won and failed claims with their bids

#### Scenario: Sleeper unreachable
- **WHEN** the transactions request fails during a refresh
- **THEN** the stored transactions stay as they were, a warning names the league and season, and the refresh continues
