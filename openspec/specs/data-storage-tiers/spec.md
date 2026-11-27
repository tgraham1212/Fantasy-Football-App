# data-storage-tiers Specification

## Purpose

Keeps the repository's history to data worth keeping: records are committed to git only when they change, derived data is rebuilt by each run and never committed, and live data lives only in the relay's bundle. Every tier is documented in `docs/refresh-modes.md`, and a test enforces the documentation. It delivers need 6, Durable Record, within need 11's free limits.

## Requirements

### Requirement: 6.1 Records committed
Git SHALL hold the records: league data, drafts and transactions; stats for played weeks, injury statuses, Player details, trending, ADP and ESPN snapshots; nflverse injury reports; current and earlier weeks' Projections; as-of and slate Forecasts; each game file's log and Forecast of record; the NFL schedule; and the calibration report.

**Traces to:** 6
**Verified by:** Test: `tests/test_storage_tiers.py::test_every_data_folder_is_listed_in_the_document`

#### Scenario: Fresh clone
- **WHEN** someone clones the repository
- **THEN** every record listed is in it

### Requirement: 6.1.1 Commit only on change
A cold run SHALL commit only when a record changed.

**Traces to:** 6.1; 11
**Verified by:** Test: `tests/test_workflows.py::test_cold_run_has_no_gate_or_test_suite_and_deploys_on_change`

#### Scenario: Nothing new
- **WHEN** a Quiet cold run finds no new transaction, stat, status or Projection
- **THEN** it makes no commit

### Requirement: 6.1.2 Touched records are not changes
A Projection or stat that differs from the stored one only in Sleeper's `last_modified` time SHALL leave the stored record as it is.

**Traces to:** 6.1; 6.1.1
**Verified by:** Test: `tests/test_projections.py::test_upsert_ignores_a_touched_but_unchanged_record`; Test: `tests/test_stats.py::test_upsert_ignores_a_touched_but_unchanged_record`

#### Scenario: Sleeper touches a Projection
- **WHEN** Sleeper returns a Projection with a newer `last_modified` and the same values
- **THEN** the stored Projection is kept and no commit is made for it

### Requirement: 6.1.3 Tallies committed once a day
A changed tally file, trending or an ESPN snapshot, SHALL be committed only when it is new or its committed copy was saved on an earlier UTC day, while each cold run still publishes the latest values.

**Rationale:** Tallies change on every fetch; git keeps at most one copy a day.
**Traces to:** 6.1; 6.1.1
**Verified by:** Test: `tests/test_tallies.py::test_same_day_tallies_are_held_and_restored`; Test: `tests/test_tallies.py::test_a_tally_from_an_earlier_day_is_committed`

#### Scenario: Tallies move within the day
- **WHEN** a cold run at 15:00 UTC finds new trending counts, and the committed copies were saved at 01:00 UTC the same day
- **THEN** the site shows the new values and no commit is made for them

### Requirement: 6.1.4 Derived data rebuilt
The derived data (`site/data`, ratings, replacement levels, WAR, the drift model, future-week Projections, the live Forecast, the game files' Forecast, views and baseline, the scoreboard's live copy, and the run files) SHALL be kept out of git and rebuilt by each cold run.

**Traces to:** 6.1
**Verified by:** Test: `tests/test_storage_tiers.py::test_no_rebuilt_path_is_tracked`; Test: `tests/test_workflows.py::test_gitignore_matches_the_rebuilt_paths`

#### Scenario: A WAR file changes
- **WHEN** a cold run recomputes WAR after a stat correction
- **THEN** the new WAR reaches the published site and no commit is made for it

### Requirement: 6.1.4.1 Build cache
Each cold run SHALL save its derived data as a GitHub Actions build cache after a successful deploy, for later runs to restore.

**Traces to:** 6.1.4; 5.2.2
**Verified by:** Test: `tests/test_workflows.py::test_cold_run_has_no_gate_or_test_suite_and_deploys_on_change`; Test: `tests/test_workflows.py::test_every_workflow_carries_the_same_rebuilt_paths`

#### Scenario: Next run
- **WHEN** a hot run starts after a cold run
- **THEN** it restores the cold run's derived data from the cache

### Requirement: 6.1.5 Offline build
`python -m ffapp build` SHALL rebuild every derived file from the committed records without network access.

**Rationale:** A fresh clone can produce the site, and need 6 asks for every past figure to be reproducible.
**Traces to:** 6.1; 6
**Verified by:** Test: `tests/test_storage_tiers.py::test_build_from_committed_records_alone`; Test: `tests/test_build_last_refresh.py::test_last_commit_time_is_the_commit_in_utc`

#### Scenario: Fresh clone
- **WHEN** someone clones the repository and runs the build with no network
- **THEN** `site/data` is produced and the site opens with the data as of the last commit

### Requirement: 6.1.6 Deploy only on change
A cold run SHALL deploy the site only when it made a commit or the rebuilt site differs from the last deployed build, ignoring timestamps.

**Traces to:** 6.1; 11
**Verified by:** Test: `tests/test_workflows.py::test_cold_run_has_no_gate_or_test_suite_and_deploys_on_change`; Test: `tests/test_store_tiers.py::test_site_hash_ignores_refresh_times`

#### Scenario: Quiet Tuesday run
- **WHEN** a cold run on Tuesday afternoon finds nothing new
- **THEN** it neither commits nor deploys

### Requirement: 6.1.7 Tiers documented
`docs/refresh-modes.md` SHALL list every committed and every rebuilt path, with what rebuilds each derived path and what reads it, so that a path under `data/` in neither list fails the tier test.

**Traces to:** 6.1; 5.1.8
**Verified by:** Test: `tests/test_storage_tiers.py::test_every_data_folder_is_listed_in_the_document`

#### Scenario: New derived file
- **WHEN** a change adds a new derived folder under `data/` without listing it
- **THEN** the tier test fails naming the folder
