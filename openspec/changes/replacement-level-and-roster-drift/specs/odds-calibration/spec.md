# Spec Delta

## MODIFIED Requirements

### Requirement: Replay uses leave-season-out noise
When replaying a season, the score noise and the roster-drift factors SHALL be estimated only from stored results of other seasons, so a replay never learns from the season it is predicting. Replacement levels for a replayed week SHALL come from that week's free agents as they stood then.

#### Scenario: Pools exclude the replayed season
- **WHEN** the 2023 dynasty season is replayed
- **THEN** no 2023 actual-minus-projected residual from either league is in the noise pools, and residuals from every other stored season are

#### Scenario: Drift excludes the replayed season
- **WHEN** the 2023 dynasty season is replayed
- **THEN** the dynasty drift factors used are estimated from the other dynasty seasons only

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

## ADDED Requirements

### Requirement: Roster drift diagnostic
The calibration report SHALL include, per league and for several horizons, how well a team's projected strength predicts its true strength that many weeks ahead (the reversion slope and the drift noise), both under the frozen roster and under the replacement-floored roster, with the N used, so the floor's effect and the choice of N can be judged from roster facts rather than from outcomes.

#### Scenario: Diagnostic present
- **WHEN** calibration finishes
- **THEN** the report shows, for each league, slopes and drift noise at horizons including 2, 5 and 12 weeks for both roster treatments
