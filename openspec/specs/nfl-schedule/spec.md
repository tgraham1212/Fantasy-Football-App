# nfl-schedule Specification

## Purpose

The current season's NFL schedule from ESPN's public scoreboard: every game's teams, kickoff time, state and score, so other features can tell when a Player locks and when the refresh mode changes. It delivers need 6, Durable Record, and serves need 5, Current Data.

## Requirements

### Requirement: 6.5 Weekly schedule stored
For the current season, the system SHALL store, per NFL week, every game's home and away team, kickoff time in UTC, state (scheduled, in progress or final) and both teams' scores, refreshed each run for the current and next weeks.

**Traces to:** 6; 5
**Verified by:** Test: `tests/test_schedule.py::test_refresh_stores_current_and_next_week`; Test: `tests/test_schedule.py::test_parse_scoreboard_maps_states_teams_and_byes`

#### Scenario: Week stored
- **WHEN** the schedule step runs during week 11
- **THEN** weeks 11 and 12 are stored with every game's teams, kickoff time and state

### Requirement: 6.5.1 Live clock in the rebuilt copy
Each game's quarter and game clock SHALL be kept in the rebuilt live copy of the schedule, out of the committed week files.

**Rationale:** The clock changes every run; committing it would add a commit each time.
**Traces to:** 6.5; 6.1.4
**Verified by:** Test: `tests/test_store_tiers.py::test_nfl_week_record_has_no_live_clocks`

#### Scenario: Game in progress
- **WHEN** a game is in the third quarter with 4:12 left and the home team leading 17-10
- **THEN** the live copy holds quarter 3 and clock 4:12, and the committed week holds the state and the scores 17 and 10

### Requirement: 6.5.2 Sleeper team abbreviations
Team abbreviations SHALL match Sleeper's.

**Traces to:** 6.5
**Verified by:** Test: `tests/test_schedule.py::test_team_aliases`

#### Scenario: Washington abbreviation
- **WHEN** ESPN lists Washington's game
- **THEN** it is stored under Sleeper's abbreviation WAS

### Requirement: 6.5.3 Kickoff lookup
The system SHALL answer, for a week and an NFL team, the team's kickoff time and whether its game has kicked off at a given moment, a team without a game being on bye.

**Traces to:** 6.5; 1.1.12
**Verified by:** Test: `tests/test_schedule.py::test_kickoff_lookup`

#### Scenario: Thursday game
- **WHEN** the lookup asks on Saturday about a team that played on Thursday
- **THEN** it reports the game as kicked off

#### Scenario: Bye
- **WHEN** a team has no game in week 11
- **THEN** the lookup reports it on bye for week 11

### Requirement: 6.5.4 Scoreboard failures
A failing scoreboard request, or one in an unexpected shape, SHALL leave the stored schedule unchanged, the step reporting the failure.

**Traces to:** 6.5; 5.5.4
**Verified by:** Test: `tests/test_schedule.py::test_refresh_failure_leaves_stored_weeks_unchanged`; Test: `tests/test_schedule.py::test_parse_scoreboard_rejects_unexpected_shapes`

#### Scenario: Scoreboard unavailable
- **WHEN** ESPN's scoreboard returns errors for every retry
- **THEN** the stored week files are unchanged and the step reports the failure

### Requirement: 6.5.5 Anonymous requests
Scoreboard requests SHALL carry a generic client identifier, with no league or personal identifiers.

**Traces to:** 6.5; 12
**Verified by:** Test: `tests/test_sleeper.py::test_success_returns_json_and_sets_user_agent`; Test: `tests/test_schedule.py::test_refresh_stores_current_and_next_week`

#### Scenario: Request headers
- **WHEN** the schedule step calls ESPN
- **THEN** the request names a generic client and carries no league ID or email
