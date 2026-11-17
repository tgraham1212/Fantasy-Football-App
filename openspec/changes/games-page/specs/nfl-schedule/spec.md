# Spec Delta

## Purpose

Stores the NFL schedule for the current season from ESPN's public scoreboard: every game's teams, kickoff time and state, so other features can tell when a player locks and when to run the refresh.

## ADDED Requirements

### Requirement: Weekly schedule stored
For the current season, the system SHALL store per NFL week every game's home and away team, kickoff time in UTC and state (scheduled, in progress or final), refreshed on every run for the current week and the next. Team abbreviations SHALL match Sleeper's.

#### Scenario: Week stored
- **WHEN** the schedule step runs during week 11
- **THEN** weeks 11 and 12 are stored with every game's teams, kickoff time and state

#### Scenario: Washington abbreviation
- **WHEN** ESPN lists Washington's game
- **THEN** it is stored under Sleeper's abbreviation WAS

### Requirement: Kickoff lookup
The system SHALL answer, for a week and an NFL team, the team's kickoff time and whether its game has kicked off at a given moment. A team with no game that week SHALL be reported as on bye.

#### Scenario: Thursday game
- **WHEN** the lookup asks on Saturday about a team that played on Thursday
- **THEN** it reports the game as kicked off

#### Scenario: Bye
- **WHEN** a team has no game in week 11
- **THEN** the lookup reports it on bye for week 11

### Requirement: Schedule source failures leave stored data intact
If the scoreboard request fails or returns an unexpected shape, the system SHALL keep the stored schedule and report the failure. Requests SHALL carry a generic client identifier and no league or personal identifiers.

#### Scenario: Scoreboard unavailable
- **WHEN** ESPN's scoreboard returns errors for every retry
- **THEN** the stored week files are unchanged and the step reports the failure
