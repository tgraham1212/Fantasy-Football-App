# start-percentage-snapshots Specification

## Purpose

ESPN start-percentage snapshots for every Player, per season and per week, and the crosswalk linking ESPN Players to Sleeper Player ids, so WAR can rank Players by how widely they are started. It delivers need 6, Durable Record, and feeds `player-war` (need 3).

## Requirements

### Requirement: 6.7 Season snapshot
For every season a configured league has stored, the system SHALL store one start-percentage snapshot holding, per ESPN Player, the ESPN id, name, position, NFL team, percent started and percent owned.

**Traces to:** 6; 3.3.3
**Verified by:** Test: `tests/test_espn.py::test_capture_backfills_missing_seasons_and_writes_current_week`; Test: `tests/test_espn.py::test_slim_snapshot_keeps_fantasy_positions_with_ownership_only`

#### Scenario: Backfill past seasons
- **WHEN** the snapshot command runs with none stored and leagues stored for 2021 to 2026
- **THEN** one season snapshot per season from 2021 to 2026 is written

### Requirement: 6.7.1 When a season snapshot is fetched
A season snapshot SHALL be fetched when none is stored and on every run while any configured league has that season in progress, a season every league has stored as complete staying as last captured.

**Traces to:** 6.7
**Verified by:** Test: `tests/test_espn.py::test_capture_refreshes_the_in_progress_season`; Test: `tests/test_espn.py::test_capture_freezes_a_season_once_complete`

#### Scenario: Frozen on completion
- **WHEN** every configured league has 2026 stored as complete
- **THEN** the 2026 season snapshot is left as last captured and not requested again

### Requirement: 6.7.2 Weekly snapshot
Every run during a season SHALL store a snapshot for the current NFL week as Sleeper reports it, replacing that week's earlier snapshot and keeping past weeks.

**Traces to:** 6.7; 3.3.7.1
**Verified by:** Test: `tests/test_espn.py::test_capture_skips_stored_seasons_and_overwrites_only_the_current_week`; Test: `tests/test_espn.py::test_capture_week_rollover_keeps_the_earlier_week`

#### Scenario: Daily captures within one week
- **WHEN** the command runs on Thursday, Sunday and Monday while Sleeper reports week 11
- **THEN** a single week-11 snapshot is stored holding Monday's values

### Requirement: 6.7.2.1 No weekly snapshot in the offseason
A run while Sleeper reports no season in progress SHALL write no weekly snapshot and still succeed.

**Traces to:** 6.7.2
**Verified by:** Test: `tests/test_espn.py::test_capture_offseason_writes_no_week`

#### Scenario: Offseason
- **WHEN** the command runs in March
- **THEN** no weekly snapshot is written and the command succeeds

### Requirement: 6.7.3 Snapshot source failures
A failing ESPN request, or one in an unexpected shape, SHALL leave every stored snapshot as it was, the run reporting the failure.

**Traces to:** 6.7; 5.5.4
**Verified by:** Test: `tests/test_espn.py::test_capture_failure_writes_nothing`; Test: `tests/test_espn.py::test_failed_refresh_keeps_the_stored_in_progress_snapshot`

#### Scenario: ESPN unavailable
- **WHEN** ESPN returns an error for every retry
- **THEN** no snapshot file is written or removed and the command reports the failure

### Requirement: 6.7.4 Player crosswalk
Each ESPN Player SHALL be mapped to a Sleeper Player id by, in order, Sleeper's stored ESPN id, an alias table of known name differences, then a normalised name and position match with the NFL team as tiebreak, defences mapping by NFL team.

**Traces to:** 6.7; 3.3.3
**Verified by:** Test: `tests/test_espn.py::test_match_by_espn_id_alias_name_and_team`; Test: `tests/test_espn.py::test_normalise`

#### Scenario: Suffix and punctuation differences
- **WHEN** ESPN lists "Travis Etienne Jr." and Sleeper lists "Travis Etienne" at RB
- **THEN** the two are matched

#### Scenario: Known alias
- **WHEN** ESPN lists "Kenneth Gainwell" and Sleeper lists "Kenny Gainwell"
- **THEN** the alias table matches them

### Requirement: 6.7.4.1 Ambiguous Players unmapped
An ESPN Player matching no Sleeper Player, or more than one with the same name, position and team, SHALL stay unmapped.

**Rationale:** A wrong match would credit one Player's start percentage to another.
**Traces to:** 6.7.4
**Verified by:** Test: `tests/test_espn.py::test_match_by_espn_id_alias_name_and_team`; Test: `tests/test_espn.py::test_match_real_fixture_leaves_nothing_relevant_unmatched`

#### Scenario: Ambiguous
- **WHEN** two Sleeper Players share the name, position and team
- **THEN** the ESPN Player is left unmapped

### Requirement: 6.7.4.2 Unmatched report
Each snapshot run SHALL report every unmapped ESPN Player started in at least 2% of leagues, with his position, season or week and percentage.

**Rationale:** The report shows where the alias table needs an entry.
**Traces to:** 6.7.4
**Verified by:** Inspection: `src/ffapp/espn.py`, the unmatched report and its 2% threshold

#### Scenario: Report after capture
- **WHEN** a 2025 season snapshot leaves a 64%-started running back unmapped
- **THEN** the run output names him with his position and percentage

### Requirement: 6.7.5 Anonymous ESPN requests
Requests to ESPN SHALL carry a generic client identifier, with no league, user or personal identifiers.

**Traces to:** 6.7; 12
**Verified by:** Test: `tests/test_espn.py::test_espn_client_url_and_filter_header`

#### Scenario: Request headers
- **WHEN** the snapshot command calls ESPN
- **THEN** the request names a generic client and carries no league ID or email
