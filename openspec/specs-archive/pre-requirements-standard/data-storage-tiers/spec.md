# data-storage-tiers Specification

## Purpose

Keeps the repository's history to data worth keeping. Records are committed to git, only when they change. Derived data is rebuilt by each run and never committed. Live data lives only in the relay's bundle. Every tier is documented, and the documentation is enforced by a test.

## Requirements

### Requirement: Records committed
Git SHALL hold the records:
- league data and transactions;
- stats for played weeks, injury statuses, player details, trending and ESPN snapshots;
- projections for the current and earlier weeks;
- forecasts of record per completed as-of week, and slate forecasts;
- each game file's log and prediction of record;
- the NFL schedule's teams, kickoffs, states and final scores;
- the calibration report.

A cold run SHALL commit only when one of these changed.

#### Scenario: Nothing new
- **WHEN** a Quiet cold run finds no new transaction, stat, status or projection
- **THEN** it makes no commit

### Requirement: Touched records are not changes
A projection or stat that differs from the stored one only in Sleeper's `last_modified` time SHALL NOT replace the stored record or count as a change.

#### Scenario: Sleeper touches a projection
- **WHEN** Sleeper returns a projection with a newer `last_modified` and the same values
- **THEN** the stored projection is kept and no commit is made for it

### Requirement: Tallies committed once a day
Trending and the ESPN snapshots are running tallies that change on every fetch. Each cold run SHALL fetch them and publish the latest on the site. Git SHALL keep at most one copy a day: a changed tally file SHALL be committed only when it is new or its committed copy was saved on an earlier UTC day.

#### Scenario: Tallies move within the day
- **WHEN** a cold run at 15:00 UTC finds new trending counts and ESPN percentages, and the committed copies were saved at 01:00 UTC the same day
- **THEN** the site shows the new values and no commit is made for them

### Requirement: Derived data rebuilt
Derived data SHALL NOT be tracked by git: `site/data`, ratings, replacement levels, WAR, the roster-drift model, future-week projections, the live forecast, the game files' forecast, views and baseline, the scoreboard's live copy, and the run files (last run, schedule summary, site hash).

Each cold run SHALL rebuild them and save them as a GitHub Actions build cache; later runs restore the newest one. Their history from before this change SHALL stay in git.

#### Scenario: A WAR file changes
- **WHEN** a cold run recomputes WAR after a stat correction
- **THEN** the new WAR reaches the published site and the build cache, and no commit is made for it

### Requirement: Offline build
A `build` command SHALL rebuild every derived file from the committed records without network access, so a fresh clone can produce the site. The code-push deploy SHALL build the site data this way, or restore it from the latest build cache, before testing and deploying.

#### Scenario: Fresh clone
- **WHEN** someone clones the repository and runs `python -m ffapp build` with no network
- **THEN** `site/data` is produced and the site opens with the data as of the last commit

### Requirement: Deploy only on change
A cold run SHALL deploy the site only when it made a commit, or when the rebuilt site differs from the last deployed build, ignoring timestamps.

#### Scenario: Quiet Tuesday run
- **WHEN** a cold run on Tuesday afternoon finds nothing new
- **THEN** it neither commits nor deploys

### Requirement: Tiers documented and enforced
`docs/refresh-modes.md` SHALL list every committed and every rebuilt path, with what rebuilds each derived path and what reads it. A test SHALL fail:
- when a rebuilt path is tracked by git;
- when a path under `data/` is in neither list;
- when the build from committed records alone fails.

#### Scenario: New derived file
- **WHEN** a change adds a new derived folder under `data/` without listing it
- **THEN** the tier test fails naming the folder
