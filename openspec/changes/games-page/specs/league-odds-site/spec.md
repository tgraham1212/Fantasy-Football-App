# Spec Delta

## MODIFIED Requirements

### Requirement: League pages
The site SHALL have a page for each configured league that shows that league's current season. Visitors SHALL be able to switch between leagues. Each league page SHALL have three sub-tabs in this order: "Predictions" (the odds table and charts), "Games" and "Player WAR", with the selected sub-tab kept in the page URL so a link opens on that sub-tab, and the sub-tab kept when switching league.

#### Scenario: Switch league
- **WHEN** a visitor on the dynasty page picks the redraft league
- **THEN** the redraft league's odds are shown

#### Scenario: Open the WAR sub-tab
- **WHEN** a visitor on the redraft Predictions sub-tab picks "Player WAR"
- **THEN** the redraft Player WAR page is shown and the URL identifies both the league and the sub-tab

#### Scenario: Link to a sub-tab
- **WHEN** a visitor opens a link whose URL names the dynasty league and the Player WAR sub-tab
- **THEN** the page opens on the dynasty Player WAR page

#### Scenario: Open the Games sub-tab
- **WHEN** a visitor picks "Games", which sits between "Predictions" and "Player WAR"
- **THEN** the league's Games page is shown and the URL identifies the league and the Games sub-tab

### Requirement: Scheduled refresh
A scheduled job SHALL check hourly, following the game-aware schedule, whether to refresh, and SHALL refresh at least daily. A refresh SHALL update league data, projections, stats, the NFL schedule, injury statuses and the start-percentage snapshot; recompute ratings, replacement levels, WAR, the odds for the current as-of week and the game logs and records; commit the stored data and republish the site. The job SHALL also be startable by hand.

#### Scenario: Day after Monday night
- **WHEN** the scheduled run happens the day after Monday night's game ends and week 10 is final in Sleeper
- **THEN** the published site shows results as of week 10

#### Scenario: Failed refresh
- **WHEN** any step of the scheduled job fails
- **THEN** the previously published site stays online unchanged, no partial data is committed, and the job run is marked failed

#### Scenario: Stats and replacement levels refreshed
- **WHEN** the scheduled run completes
- **THEN** the current season's stats for played weeks and the current season's replacement levels are stored alongside the odds

#### Scenario: Ratings refreshed
- **WHEN** the scheduled run completes after week 10 is final
- **THEN** every league's rating file includes week 10 and the published table shows the updated ELO values

#### Scenario: Snapshot and WAR refreshed
- **WHEN** the scheduled run completes during week 11
- **THEN** the week-11 start-percentage snapshot is stored and every league's current-season WAR file and leaderboard reflect the weeks scored so far

#### Scenario: ESPN unavailable
- **WHEN** the snapshot capture fails during a scheduled run
- **THEN** the failure is logged, the remaining steps still run using the snapshots already stored, the odds are still refreshed and published, and the run ends with a warning naming the skipped step and the reason, shown as an annotation on the job run

#### Scenario: Games refreshed before kickoff
- **WHEN** the refresh runs 40 minutes before Sunday's 1 pm games
- **THEN** the NFL schedule, injury statuses and every current-week game log are updated and the Games page shows the new forecasts
