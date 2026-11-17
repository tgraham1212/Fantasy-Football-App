# Spec Delta

## MODIFIED Requirements

### Requirement: Weekly schedule stored
For the current season, the system SHALL store per NFL week every game's home and away team, kickoff time in UTC, state (scheduled, in progress or final), quarter, game clock and both teams' scores, refreshed on every run for the current week and the next. Team abbreviations SHALL match Sleeper's.

#### Scenario: Week stored
- **WHEN** the schedule step runs during week 11
- **THEN** weeks 11 and 12 are stored with every game's teams, kickoff time and state

#### Scenario: Washington abbreviation
- **WHEN** ESPN lists Washington's game
- **THEN** it is stored under Sleeper's abbreviation WAS

#### Scenario: Game in progress
- **WHEN** a game is in the third quarter with 4:12 left and the home team leading 17-10
- **THEN** the stored game has state in progress, quarter 3, clock 4:12 and scores 17 and 10
