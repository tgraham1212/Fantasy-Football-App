# odds-calibration Specification

## Purpose

Measures how well the playoff odds simulation is calibrated by replaying completed seasons from stored data and comparing the chances it would have published with what actually happened.

## Requirements

### Requirement: Season replay
The system SHALL be able to replay every stored league-season with status complete through the playoff odds simulation, as of every week from 0 (preseason) through the week before the final playoff round, using only data stored for that season (schedules, matchup rosters, projections, playoff results). Each replay SHALL be saved in the odds history under its league, season and as-of week.

#### Scenario: Replay a completed season
- **WHEN** calibration runs with the 2024 redraft season stored as complete
- **THEN** odds-history results exist for the 2024 redraft season as of weeks 0 through 16

#### Scenario: Current season is not replayed
- **WHEN** calibration runs while the 2026 season is in progress
- **THEN** no 2026 results are produced or changed by calibration

### Requirement: Replay uses leave-season-out noise
When replaying a season, the score noise and the roster-drift factors SHALL be estimated only from stored results of other seasons, so a replay never learns from the season it is predicting. Replacement levels for a replayed week SHALL come from that week's free agents as they stood then.

#### Scenario: Pools exclude the replayed season
- **WHEN** the 2023 dynasty season is replayed
- **THEN** no 2023 actual-minus-projected residual from either league is in the noise pools, and residuals from every other stored season are

#### Scenario: Drift excludes the replayed season
- **WHEN** the 2023 dynasty season is replayed
- **THEN** the dynasty drift factors used are estimated from the other dynasty seasons only

### Requirement: Score-level calibration
For every replayed as-of week, the system SHALL compare each team's simulated score distribution for the next week with the points that team actually scored. It SHALL report, per league and overall: where actual scores fall in the simulated distribution, the share of actual scores inside the 50%, 80% and 95% central intervals, and the average simulated-minus-actual difference.

#### Scenario: Noise too narrow
- **WHEN** actual scores land outside the simulated 80% interval in 35% of team-weeks
- **THEN** the report shows 65% observed coverage against the 80% nominal interval

#### Scenario: Well calibrated noise
- **WHEN** the simulated noise matches reality
- **THEN** observed coverage is within sampling error of each nominal interval and percentile ranks are spread evenly from 0 to 100

### Requirement: Game-level calibration
For every replayed as-of week, the system SHALL compare the simulated chance that each team wins its next matchup with the real result. It SHALL report win chances grouped in 10-point bins with the observed win rate and count in each bin, and the Brier score of the win chances.

#### Scenario: Reliability bins
- **WHEN** 80 games had a simulated favourite at 60-70%
- **THEN** the 60-70% bin shows how many of those 80 the favourite actually won

### Requirement: Season-level calibration
For every replayed as-of week and team, the system SHALL compare the simulated chance of each season outcome (playoffs, first-round bye, final, title, losers bracket, last place, avoiding the bottom two) with whether it happened, taking actual outcomes from stored standings and brackets. For each outcome the report SHALL give 10-point reliability bins with observed rates and counts, and the Brier score.

#### Scenario: Thirty percent means thirty percent
- **WHEN** teams were shown a 25-35% playoff chance in 150 team-weeks
- **THEN** the 30% bin reports how many of those 150 made the playoffs, so an observed rate near 30% shows calibration and a rate near 50% shows the model is too cautious

#### Scenario: Actual outcomes from stored data
- **WHEN** the 2025 dynasty season's winners bracket names roster 4 as champion
- **THEN** roster 4's title outcome for every 2025 as-of week is true and every other roster's is false

#### Scenario: Decided outcomes are not scored
- **WHEN** the regular season is over as of week 14
- **THEN** playoff, bye, losers-bracket, last-place and bottom-two chances as of week 14 and later are left out of the season-level comparison, while title and final chances are compared until the round that decides them

### Requirement: Naive baseline
For each season outcome, the report SHALL also give the Brier score of a naive baseline and the simulation's skill against it. Before any week is played the baseline SHALL give every team the outcome's league-wide base rate; afterwards it SHALL extrapolate each team's current record over the remaining weeks and rank teams on it, moving from the base rate toward that ranking as the season goes on.

#### Scenario: Better than the standings
- **WHEN** the simulation's Brier score for playoffs is lower than the baseline's
- **THEN** the report shows a positive skill score for playoffs

#### Scenario: Preseason baseline
- **WHEN** the baseline is evaluated as of week 0 of a 12-team league
- **THEN** every team's baseline playoff chance is 50% and title chance is 8.3%

### Requirement: Lineup gap
For every stored team-week with projections, the system SHALL compare the lineup the simulation would have started (best projected) with the lineup actually started, and report the average projected-points gap and the average actual-points gap per league.

#### Scenario: Managers leave points on the bench
- **WHEN** the best projected lineup averages 3.2 more projected points than the lineup managers actually started
- **THEN** the report shows a 3.2-point projected lineup gap for that league

### Requirement: Calibration report
The system SHALL write the calibration results as a machine-readable report and a human-readable Markdown summary in the data directory. Each SHALL record when it was produced, the number of simulation runs per replay, the residual scale in force, the seasons replayed, and the sample counts behind every rate.

#### Scenario: Report written
- **WHEN** calibration finishes
- **THEN** `data/calibration/report.json` and `data/calibration/report.md` are written and agree on every figure

#### Scenario: Re-run replaces the report
- **WHEN** calibration runs a second time with a different residual scale
- **THEN** both report files are replaced and name the new residual scale

### Requirement: Calibration is on demand and repeatable
Calibration SHALL run as its own command, not as part of the scheduled refresh. Given the same stored data, run count and seed, it SHALL produce an identical report. The run count, a residual scale, and switches that turn off the replacement-level floor or the roster drift for the replay SHALL be settable on the command line, with a default run count that completes all stored seasons in minutes.

#### Scenario: Evaluate a candidate scale without changing configuration
- **WHEN** calibration is run with a residual scale of 0.9 on the command line
- **THEN** the replay uses that scale, the report names 0.9, and the configuration file is unchanged

#### Scenario: Scheduled job unaffected
- **WHEN** the daily refresh runs
- **THEN** no season replay or calibration report is produced

#### Scenario: Measure one piece alone
- **WHEN** calibration is run with the roster drift switched off
- **THEN** the replay applies the replacement floor but no drift, and the report records that drift was off

### Requirement: Roster drift diagnostic
The calibration report SHALL include, per league and for several horizons, how well a team's projected strength predicts its true strength that many weeks ahead (the reversion slope and the drift noise), both under the frozen roster and under the replacement-floored roster, with the N used, so the floor's effect and the choice of N can be judged from roster facts rather than from outcomes.

#### Scenario: Diagnostic present
- **WHEN** calibration finishes
- **THEN** the report shows, for each league, slopes and drift noise at horizons including 2, 5 and 12 weeks for both roster treatments

### Requirement: Calibration page
The site SHALL have a calibration page, reachable from every league page, titled "How Good Are These Forecasts?", that shows how well past forecasts matched real outcomes: for each season outcome, forecast percentage against observed rate with the number of cases behind each point; observed against nominal coverage of the score intervals; the Brier skill against the baseline; the lineup gap per league; when the calibration was produced, how many seasons it covers and the residual scale used; and the known caveats.

#### Scenario: Visitor checks the odds
- **WHEN** a visitor opens the calibration page after a calibration report has been published
- **THEN** they can see, for the playoff forecast, how often teams shown at each forecast level actually made the playoffs

#### Scenario: Calibration not yet run
- **WHEN** the site is published without a calibration report
- **THEN** the calibration page says calibration has not been run and the league pages work as before

#### Scenario: Data from published files
- **WHEN** the calibration page loads
- **THEN** all figures come from a file published with the site, with no server code

### Requirement: Calibration report exported
The export SHALL include the stored calibration report in the site data when one exists, and SHALL succeed without one.

#### Scenario: Report present
- **WHEN** the export runs after calibration has been run
- **THEN** the site data contains the calibration report that was stored

#### Scenario: Report absent
- **WHEN** the export runs on a store that has never been calibrated
- **THEN** the league files are written as usual and the export succeeds

### Requirement: Replacement levels exported
Each league's site data SHALL include the current season's replacement levels: the next unplayed week's projected level per position, the season values, the N used, and the drift model in force, so the calibration page can explain the model with live numbers. The export SHALL succeed when the replacement or model files are missing, leaving those fields absent.

#### Scenario: Levels present
- **WHEN** the export runs after the replacement and simulate commands
- **THEN** the dynasty and redraft site files carry the replacement levels for the next unplayed week and the drift factors

#### Scenario: Levels absent
- **WHEN** the export runs on a store without replacement files
- **THEN** the league files are written without the replacement fields and the page explains the model without the live numbers

### Requirement: Odds model explained
The calibration page SHALL explain, in plain language for league members, how the odds are made: projections, score noise from past seasons, best lineups with the replacement-level floor, and roster drift, with each league's current replacement levels and how much of a team's edge the model expects to survive weeks ahead. It SHALL state whether the replacement floor and roster drift were on for the shown report and the N used.

#### Scenario: Member reads the explanation
- **WHEN** a league member opens the calibration page
- **THEN** they can read what a replacement-level player is, see this week's replacement level per position for each league, and see how much of a 20-point edge the model expects a team to keep two and twelve weeks out, computed from the published drift model

#### Scenario: Switches stated
- **WHEN** the calibration page shows a report
- **THEN** it states whether the replacement floor and roster drift were on for that report and the N used
