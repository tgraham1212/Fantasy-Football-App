## ADDED Requirements

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
