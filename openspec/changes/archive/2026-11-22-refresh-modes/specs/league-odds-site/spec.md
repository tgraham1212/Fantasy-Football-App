## MODIFIED Requirements

### Requirement: Scheduled refresh
The cold run SHALL run on the cadence of its refresh mode (see `refresh-scheduling`), at least daily, and SHALL be startable by hand. It SHALL:
- update league data, projections, stats, the NFL schedule, injury statuses and the start-percentage snapshot;
- recompute ratings, replacement levels, WAR, the odds for the current as-of week, and the game logs and records;
- commit only the changed records (see `data-storage-tiers`);
- republish the site only on change.

In Live it SHALL skip the simulation, which the hot runs own.

#### Scenario: Day after Monday night
- **WHEN** the scheduled run happens the day after Monday night's game ends and week 10 is final in Sleeper
- **THEN** the published site shows results as of week 10

#### Scenario: Failed refresh
- **WHEN** any step of the scheduled job fails
- **THEN** the previously published site stays online unchanged, no partial data is committed, and the job run is marked failed

#### Scenario: Stats and replacement levels refreshed
- **WHEN** the scheduled run completes
- **THEN** the current season's stats for played weeks are committed when they changed, and the current season's replacement levels are rebuilt and published alongside the odds

#### Scenario: Ratings refreshed
- **WHEN** the scheduled run completes after week 10 is final
- **THEN** every league's rebuilt ratings include week 10 and the published table shows the updated ELO values

#### Scenario: Snapshot and WAR refreshed
- **WHEN** the scheduled run completes during week 11
- **THEN** the week-11 start-percentage snapshot is stored and every league's current-season WAR and leaderboard reflect the weeks scored so far

#### Scenario: ESPN unavailable
- **WHEN** the snapshot capture fails during a scheduled run
- **THEN** the failure is logged, the remaining steps still run using the snapshots already stored, the odds are still refreshed and published, and the run ends with a warning naming the skipped step and the reason, shown as an annotation on the job run

#### Scenario: Games refreshed before kickoff
- **WHEN** a Quiet cold run happens 40 minutes before Sunday's 1 pm games
- **THEN** the NFL schedule, injury statuses and every current-week game log are updated and the Games page shows the new forecasts

### Requirement: Deploy on code push
A push to the main branch that changes site code (anything under the site folder other than its data files) SHALL:
1. build the site data, by restoring the latest build cache or by the offline build;
2. run the tests and the layout check;
3. when they pass, deploy the site with that data.

It SHALL never run at the same time as a cold run. It may run alongside hot runs.

#### Scenario: Code pushed
- **WHEN** a commit changing the Games page script is pushed
- **THEN** the site deploys with it within a few minutes, without waiting for the next data refresh

#### Scenario: Data-only push
- **WHEN** the cold run pushes its data commit
- **THEN** no code-push deploy runs
