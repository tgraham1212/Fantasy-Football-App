# Spec Delta

## MODIFIED Requirements

### Requirement: Scheduled refresh
A scheduled job SHALL run at least once a day. It SHALL sync league data, refresh projections and player stats, refresh replacement levels, run the simulation for the current as-of week, save the results, commit the stored data to the repository and republish the site. It SHALL also be possible to start the job by hand.

#### Scenario: Day after Monday night
- **WHEN** the scheduled run happens the day after Monday night's game ends and week 10 is final in Sleeper
- **THEN** the published site shows results as of week 10

#### Scenario: Failed refresh
- **WHEN** any step of the scheduled job fails
- **THEN** the previously published site stays online unchanged, no partial data is committed, and the job run is marked failed

#### Scenario: Stats and replacement levels refreshed
- **WHEN** the scheduled run completes
- **THEN** the current season's stats for played weeks and the current season's replacement levels are stored alongside the odds

### Requirement: Calibration page
The site SHALL have a calibration page, reachable from every league page, that shows how well past odds matched real outcomes: for each season outcome, predicted chance against observed rate with the number of cases behind each point; observed against nominal coverage of the score intervals; the Brier skill against the baseline; the lineup gap per league; when the calibration was produced, how many seasons it covers and the residual scale used; and the known caveats. It SHALL also explain, in plain language for league members, how the odds are made: projections, score noise from past seasons, best lineups with the replacement-level floor, and roster drift, with each league's current replacement levels and how much of a team's edge the model expects to survive weeks ahead.

#### Scenario: Visitor checks the odds
- **WHEN** a visitor opens the calibration page after a calibration report has been published
- **THEN** they can see, for playoff chances, how often teams shown at each level of chance actually made the playoffs

#### Scenario: Calibration not yet run
- **WHEN** the site is published without a calibration report
- **THEN** the calibration page says calibration has not been run and the league pages work as before

#### Scenario: Data from published files
- **WHEN** the calibration page loads
- **THEN** all figures come from a file published with the site, with no server code

#### Scenario: Member reads how it works
- **WHEN** a league member opens the calibration page
- **THEN** they can read what a replacement-level player is, see this week's replacement level per position for each league, and see how many of a 20-point edge the model expects a team to keep two and twelve weeks out, computed from the published drift model

#### Scenario: Model switches shown
- **WHEN** the calibration page shows a report
- **THEN** it states whether the replacement floor and roster drift were on for that report and the N used

## ADDED Requirements

### Requirement: Replacement levels exported
Each league's site data SHALL include the current season's replacement levels: the next unplayed week's projected level per position, the season values, the N used, and the drift model in force, so the calibration page can explain the model with live numbers. The export SHALL succeed when the replacement or model files are missing, leaving those fields absent.

#### Scenario: Levels present
- **WHEN** the export runs after the replacement and simulate commands
- **THEN** the dynasty and redraft site files carry the replacement levels for the next unplayed week and the drift factors

#### Scenario: Levels absent
- **WHEN** the export runs on a store without replacement files
- **THEN** the league files are written without the replacement fields and the page explains the model without the live numbers
