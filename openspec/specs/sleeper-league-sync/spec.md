# sleeper-league-sync Specification

## Purpose

Keeps a complete local copy of each configured Sleeper league's history: settings, users, rosters, matchups, brackets and transactions for every season, so the rest of the app works from stored data instead of calling Sleeper live. It delivers need 6, Durable Record.

## Requirements

### Requirement: 6.2 Configured leagues
The system SHALL sync the leagues listed in `config/leagues.yaml`, each with its current Sleeper league ID and a short display key, and no others.

**Traces to:** 6
**Verified by:** Test: `tests/test_config.py::test_repo_config_loads_both_leagues`; Test: `tests/test_config.py::test_valid_config_parses_overrides`

#### Scenario: Both leagues configured
- **WHEN** the configuration lists dynasty league `1339662153812025344` and redraft league `1389347876550770688`
- **THEN** a sync pulls data for both leagues and for no others

### Requirement: 6.2.1 Configuration checked
Loading the configuration SHALL fail with an error naming the field on any missing, unknown or invalid value, the simulation, rating and rival settings included.

**Traces to:** 6.2; 10
**Verified by:** Test: `tests/test_config.py::test_unknown_top_level_key_rejected`; Test: `tests/test_config.py::test_invalid_residual_scale_rejected`

#### Scenario: Invalid residual scale
- **WHEN** the residual scale is set to 0, a negative number or text
- **THEN** loading the configuration fails with an error naming the residual scale

### Requirement: 6.2.2 Full season history
For each configured league, the sync SHALL follow `previous_league_id` back to the earliest season Sleeper has, storing each season as a separate league-season.

**Traces to:** 6.2
**Verified by:** Test: `tests/test_sync.py::test_walk_full_dynasty_chain_newest_last`; Test: `tests/test_sync.py::test_walk_guards_against_cycles`

#### Scenario: Dynasty history
- **WHEN** the dynasty league is synced
- **THEN** league-seasons 2022 to 2026 are stored, each with its own Sleeper league ID

#### Scenario: New season for the redraft league
- **WHEN** the configuration is changed to the redraft league's new season ID
- **THEN** the next sync follows the chain back through every prior season under the same display key

### Requirement: 6.2.2.1 End of the chain
A `previous_league_id` that is empty, null or `0` SHALL end the history walk at that season.

**Traces to:** 6.2.2
**Verified by:** Test: `tests/test_sync.py::test_walk_three_season_chain_stops_on_terminator`

#### Scenario: Chain ends
- **WHEN** a league-season's `previous_league_id` is `0`
- **THEN** that season is the earliest and the walk stops

### Requirement: 6.2.3 League data per season
For each league-season, the sync SHALL store the league settings, users, rosters, the matchups of every regular-season and playoff week, and the winners and losers brackets.

**Traces to:** 6.2
**Verified by:** Test: `tests/test_sync.py::test_fetch_and_store_completed_season`; Test: `tests/test_sync.py::test_season_weeks_cover_regular_season_and_three_playoff_rounds`

#### Scenario: Completed season
- **WHEN** a completed league-season is synced
- **THEN** matchups for every week from the start week through the final playoff week, and both brackets, are stored

### Requirement: 6.2.3.1 Unplayed weeks
For a season in progress, the sync SHALL store any matchup data Sleeper returns for later weeks as unplayed.

**Traces to:** 6.2.3
**Verified by:** Test: `tests/test_sync.py::test_in_progress_season_stores_unplayed_weeks`

#### Scenario: Season in progress
- **WHEN** the 2026 league-season is synced during week 10
- **THEN** weeks 1 to 9 are stored with scores and later weeks as unplayed

### Requirement: 6.2.4 Settings per season
Each league-season's scoring, roster slots and playoff settings SHALL be read from its own stored settings.

**Traces to:** 6.2; 6.2.3
**Verified by:** Test: `tests/test_sync.py::test_fetch_and_store_completed_season`; Test: `tests/test_league.py::test_starter_slots_for_both_leagues`

#### Scenario: Settings differ between seasons
- **WHEN** the dynasty FAAB budget is 100 in 2024 and 150 in 2025
- **THEN** each league-season's settings show its own value

### Requirement: 6.2.4.1 Scoring overrides
A manual override in the configuration SHALL replace a scoring setting for one league-season from a given week on, earlier weeks keeping Sleeper's stored settings.

**Traces to:** 6.2.4
**Verified by:** Test: `tests/test_league.py::test_resolve_settings_override_applies_from_week`; Test: `tests/test_league.py::test_resolve_settings_without_override_matches_sleeper`

#### Scenario: Mid-season scoring change
- **WHEN** an override sets `fgm_yds` to 0.1 for the redraft 2023 season starting at week 6
- **THEN** weeks 1 to 5 use Sleeper's stored value and weeks 6 on use 0.1

### Requirement: 6.2.5 Managers by user id
Each roster in each league-season SHALL be linked to its Manager's Sleeper user id, display name and Team Name.

**Traces to:** 6.2; 4.5
**Verified by:** Test: `tests/test_league.py::test_owner_mapping_uses_user_ids_and_team_names`; Test: `tests/test_league.py::test_owner_turnover_between_seasons`

#### Scenario: Turnover
- **WHEN** roster slot 4 has a different Manager in 2022 than in 2026
- **THEN** the stored data shows two different Managers for that slot

### Requirement: 6.2.5.1 Vacant rosters inherit
Every reader of stored rosters SHALL see a roster without a Manager as held by the most recent earlier Manager of that slot, else the first later one, with that Manager's last stored names.

**Rationale:** A Manager who quits early leaves a roster Sleeper reports empty.
**Traces to:** 6.2.5; 4.5
**Verified by:** Test: `tests/test_vacant_owner.py::test_owner_quit_before_the_year_ended`; Test: `tests/test_vacant_owner.py::test_vacant_in_the_first_stored_season_takes_the_later_owner`

#### Scenario: Manager quit before the year ended
- **WHEN** roster 11 was DeekBurg's in 2022, has no Manager in 2023, and another user's in 2024
- **THEN** roster 11 reads as DeekBurg's in 2023, with his names from 2022

### Requirement: 6.2.5.2 Stored files as fetched
The stored rosters and users files SHALL keep Sleeper's data as fetched, the inherited Manager applied only when read.

**Traces to:** 6.2.5; 6.2.5.1
**Verified by:** Test: `tests/test_vacant_owner.py::test_stored_files_untouched`

#### Scenario: Stored files untouched
- **WHEN** a vacant roster is read with an inherited Manager
- **THEN** the stored rosters and users files are unchanged

### Requirement: 6.2.6 Completed seasons kept
A league-season stored as complete SHALL be fetched again only when a full re-sync is requested.

**Traces to:** 6.2; 11
**Verified by:** Test: `tests/test_sync.py::test_routine_sync_skips_complete_seasons_and_full_refetches`

#### Scenario: Routine sync
- **WHEN** a sync runs with 2022 to 2025 stored as complete
- **THEN** only the current season is fetched from Sleeper

### Requirement: 6.2.7 Sync failures
A failed Sleeper request SHALL leave the stored data from the last successful sync byte for byte, the run reporting the failure with a non-zero exit status.

**Traces to:** 6.2
**Verified by:** Test: `tests/test_sync.py::test_failed_fetch_leaves_stored_files_byte_identical`; Test: `tests/test_sync.py::test_history_walk_failure_is_reported`

#### Scenario: Sleeper unavailable
- **WHEN** Sleeper returns errors for every request during a sync
- **THEN** the stored data is unchanged and the run exits with a non-zero status

### Requirement: 6.2.8 Transactions stored
For each league-season, the sync SHALL store Sleeper's transactions, one file per week: won and failed waiver claims with their bids, free-agent moves, trades with Players, picks and FAAB, and commissioner moves.

**Traces to:** 6.2; 4.5.10
**Verified by:** Test: `tests/test_sync.py::test_transactions_saved_for_every_week`

#### Scenario: Week saved
- **WHEN** week 11 of the 2026 redraft season is synced
- **THEN** its claims, free-agent moves and trades are saved in that week's file

### Requirement: 6.2.8.1 Transactions fetch schedule
A completed season's transactions SHALL be fetched once, and the current season's on every sync.

**Traces to:** 6.2.8
**Verified by:** Test: `tests/test_sync.py::test_completed_season_without_transactions_is_backfilled_once`

#### Scenario: Backfill of a completed season
- **WHEN** the 2023 dynasty season is stored as complete with no transactions
- **THEN** the next sync fetches them once, and later syncs do not

### Requirement: 6.2.8.2 Transactions failure
A failed transactions fetch SHALL keep the files stored last time, with a warning naming the league and season, while the sync and the cold run carry on.

**Traces to:** 6.2.8; 5.5.4
**Verified by:** Test: `tests/test_sync.py::test_transactions_failure_keeps_files_and_only_warns`

#### Scenario: Sleeper unreachable
- **WHEN** the transactions request fails during a cold run
- **THEN** the stored transactions stay as they were, a warning names the league and season, and the run continues
