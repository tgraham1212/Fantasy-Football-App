# Spec Delta

## Purpose

Defines who counts as a free agent in a league and what a replacement-level player is worth at each position, week by week and over a season, as a shared building block for the simulation and later value features.

## ADDED Requirements

### Requirement: Free agents
For a league, season and week, the free agents SHALL be the players with a stored projection for that week who are on no roster in that league. For a stored week, rostered players are those listed in that week's matchup rosters; for the present and future, those on the current rosters including reserve and taxi slots.

#### Scenario: Historic week
- **WHEN** free agents are determined for redraft 2024 week 6
- **THEN** a player on any team's week-6 roster is excluded and a projected player on no week-6 roster is included

#### Scenario: Current week
- **WHEN** free agents are determined for the current season's remaining weeks
- **THEN** a player on any current roster, including reserve and taxi, is excluded

### Requirement: Weekly replacement level
For each league, season, week and position, the replacement players SHALL be the N free agents with the highest projected points for that week under the league's scoring (N configurable, default 3), and the projected level SHALL be the mean of their projections. Fewer than N free agents SHALL average those available; none SHALL give 0.

#### Scenario: Projected level
- **WHEN** the three best-projected free-agent receivers for week 8 project 9.4, 8.9 and 8.1
- **THEN** the week-8 WR projected level is 8.8

#### Scenario: Thin position
- **WHEN** only two free-agent tight ends have a positive projection for a week
- **THEN** the TE projected level is the mean of those two

#### Scenario: Different leagues differ
- **WHEN** the same week is computed for the dynasty and redraft leagues
- **THEN** each league's levels use its own rosters and scoring, so they differ

### Requirement: Realised replacement level
For the same replacement players, the realised level SHALL be the mean of their actual points from stored stats under the league's scoring, counting a player with no stat line as 0. It SHALL be absent when the week has no stored stats.

#### Scenario: Scored after the games
- **WHEN** the week-8 replacement receivers chosen by projection score 14.0, 3.2 and 7.6
- **THEN** the week-8 WR realised level is 8.27

#### Scenario: Week not yet played
- **WHEN** the replacement level is computed for a future week
- **THEN** the projected level is present and the realised level is absent

### Requirement: Season replacement value
For each league, season and position, the season value SHALL be the mean of the realised weekly levels so far, shrunk toward a prior: `(n × mean + k × prior) / (n + k)`, with n the number of played weeks and k a configurable number of weeks (default 4).

#### Scenario: Before any game
- **WHEN** the season value is computed with no week played
- **THEN** it equals the prior

#### Scenario: Shrinkage fades
- **WHEN** 12 weeks are played with a mean realised level of 8.0 and a prior of 6.0, with k = 4
- **THEN** the season value is 7.5

### Requirement: Replacement prior
The prior for a league-season and position SHALL be the 50/30/20 weighted mean of the final season values of the three most recent earlier seasons of that league with the same scoring and roster settings, renormalised when fewer exist. With no such season the prior SHALL be the mean of the current season's projected weekly levels.

#### Scenario: Three earlier seasons
- **WHEN** the 2025, 2024 and 2023 final values are 8.0, 7.0 and 6.0
- **THEN** the 2026 prior is 7.3

#### Scenario: First stored season
- **WHEN** the season value is computed for redraft 2021
- **THEN** the prior is the mean of 2021's projected weekly levels

### Requirement: Replacement levels stored
The system SHALL write, per league and season, the weekly projected and realised levels by position, the season values, the N used and the free-agent counts, to `data/replacement/<league>/<season>.json`, and SHALL refresh the current season's file on every scheduled refresh.

#### Scenario: File contents
- **WHEN** the replacement command runs for the dynasty league
- **THEN** `data/replacement/dynasty/2026.json` lists weeks 1 through 17 with projected levels for every position, realised levels for the played weeks, and the season values

#### Scenario: Past seasons
- **WHEN** the replacement command runs
- **THEN** every stored season of every configured league gets a file
