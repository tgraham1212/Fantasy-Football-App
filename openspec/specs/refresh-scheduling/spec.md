# refresh-scheduling Specification

## Purpose

Decides when the full refresh runs, so forecasts are refreshed just before games kick off and soon after they finish without running more often than every three hours.

## Requirements

### Requirement: Hourly check
The scheduled job SHALL wake every hour and decide from the stored NFL schedule, refreshed from the scoreboard, whether to run the full refresh. When it decides not to, it SHALL end without committing or deploying anything.

#### Scenario: Quiet Wednesday
- **WHEN** the job wakes on a Wednesday afternoon with no kickoff in the next hour and no game finished since the last run
- **THEN** it ends without running the refresh

### Requirement: Run triggers
The check SHALL run the full refresh when a game kicks off within the next 60 minutes, when a game has gone final since the last full run, or when it is the daily run at 11:00 UTC. A manual start SHALL always run.

#### Scenario: Before the 1 pm games
- **WHEN** the job wakes at 12:20 pm Eastern on a Sunday with games kicking off at 1:00 pm
- **THEN** it runs the full refresh

#### Scenario: After the night game
- **WHEN** the Thursday night game went final after the last full run
- **THEN** the next check runs the full refresh

### Requirement: Run spacing
Apart from the daily run and manual starts, the full refresh SHALL NOT start within three hours of the previous full run's start. The time of each full run SHALL be stored with the data.

#### Scenario: Back-to-back windows
- **WHEN** a full run started at 12:20 pm and the 4:05 pm games are 40 minutes away at 3:25 pm
- **THEN** the check runs the full refresh, since three hours have passed

#### Scenario: Too soon
- **WHEN** a full run started at 12:20 pm and a 1:00 pm game goes final at 2:30 pm
- **THEN** the 3:00 pm check does not run the full refresh

### Requirement: Check failures
If the scoreboard cannot be read during a check, the check SHALL skip that hour unless it is the daily run, which SHALL run the full refresh anyway.

#### Scenario: Scoreboard down at the daily run
- **WHEN** the scoreboard fails at 11:00 UTC
- **THEN** the full refresh runs and the schedule step reports the failure as a skipped step
