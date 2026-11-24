# replacement-level Specification

## Purpose

Who counts as a free agent in a league, and what a replacement-level Player is worth at each position, week by week and over a season: the building block for the simulation's floor and for valuing Players against what a free agent would provide. It serves need 3, Player Value, and the simulation's floor (`playoff-odds-simulation` 1.1.4.1); the formula is in `Calculations.txt`, section 14.

## Requirements

### Requirement: 3.5 Weekly replacement level
For each league, season, week and position, the projected replacement level SHALL be the mean projection of the N free agents with the highest projected points under the league's scoring, N set in the configuration and 3 by default.

**Rationale:** Calculations.txt section 14.
**Traces to:** 3; 1.1.4.1
**Verified by:** Test: `tests/test_replacement.py::test_weekly_level_chooses_by_projection_and_scores_both_ways`; Test: `tests/test_config.py::test_replacement_settings_default_and_parse`

#### Scenario: Projected level
- **WHEN** the three best-projected free-agent receivers for week 8 project 9.4, 8.9 and 8.1
- **THEN** the week-8 WR projected level is 8.8

#### Scenario: Different leagues differ
- **WHEN** the same week is computed for the dynasty and redraft leagues
- **THEN** each league's levels use its own rosters and scoring

### Requirement: 3.5.1 Thin positions
A position with fewer than N free agents SHALL average those it has, a position with none having a level of 0.

**Traces to:** 3.5
**Verified by:** Test: `tests/test_replacement.py::test_weekly_level_edge_cases`

#### Scenario: Thin position
- **WHEN** only two free-agent tight ends have a positive projection for a week
- **THEN** the TE projected level is the mean of those two

### Requirement: 3.5.2 Free agents
For a league, season and week, the free agents SHALL be the Players with a positive projection for that week who are on no roster in that league.

**Traces to:** 3.5
**Verified by:** Test: `tests/test_replacement.py::test_free_agents_exclude_rostered_and_zero_projections`

#### Scenario: Zero projection
- **WHEN** an unrostered receiver projects 0 for the week
- **THEN** he is not a free agent for the replacement level

### Requirement: 3.5.2.1 Rostered Players
A Player SHALL count as rostered when he is on a week's matchup rosters for a stored week, or on a current roster, reserve and taxi included, for the present and future weeks.

**Traces to:** 3.5.2
**Verified by:** Test: `tests/test_replacement.py::test_rostered_sets_from_season_data`

#### Scenario: Historic week
- **WHEN** free agents are determined for redraft 2024 week 6
- **THEN** a Player on any team's week-6 roster is excluded and a projected Player on no week-6 roster is included

#### Scenario: Current week
- **WHEN** free agents are determined for the current season's remaining weeks
- **THEN** a Player on any current roster, reserve and taxi included, is excluded

### Requirement: 3.5.3 Realised replacement level
For the same replacement Players, the realised level SHALL be the mean of their actual points under the league's scoring, a Player with no stat line counting as 0, for each week with stored stats.

**Traces to:** 3.5
**Verified by:** Test: `tests/test_replacement.py::test_weekly_level_chooses_by_projection_and_scores_both_ways`; Test: `tests/test_replacement.py::test_weekly_level_edge_cases`

#### Scenario: Scored after the games
- **WHEN** the week-8 replacement receivers chosen by projection score 14.0, 3.2 and 7.6
- **THEN** the week-8 WR realised level is 8.27

#### Scenario: Week not yet played
- **WHEN** the replacement level is computed for a future week
- **THEN** the projected level is present and the realised level absent

### Requirement: 3.5.4 Season replacement value
For each league, season and position, the season value SHALL be the mean realised weekly level so far shrunk toward a prior, (n × mean + k × prior) / (n + k), n being the played weeks and k a configured number of weeks, 4 by default.

**Traces to:** 3.5
**Verified by:** Test: `tests/test_replacement.py::test_season_value_shrinkage`

#### Scenario: Before any game
- **WHEN** the season value is computed with no week played
- **THEN** it equals the prior

#### Scenario: Shrinkage fades
- **WHEN** 12 weeks are played with a mean realised level of 8.0 and a prior of 6.0, with k = 4
- **THEN** the season value is 7.5

### Requirement: 3.5.4.1 Replacement prior
The prior SHALL be the 50/30/20 weighted mean of the final season values of the league's three most recent earlier seasons with the same scoring and roster settings, renormalised when fewer exist.

**Traces to:** 3.5.4
**Verified by:** Test: `tests/test_replacement.py::test_prior_from_seasons`; Test: `tests/test_replacement.py::test_write_replacement_covers_every_season_and_uses_comparable_priors`

#### Scenario: Three earlier seasons
- **WHEN** the 2025, 2024 and 2023 final values are 8.0, 7.0 and 6.0
- **THEN** the 2026 prior is 7.3

### Requirement: 3.5.4.2 First season prior
With no comparable earlier season, the prior SHALL be the mean of the current season's projected weekly levels.

**Traces to:** 3.5.4; 3.5.4.1
**Verified by:** Test: `tests/test_replacement.py::test_prior_from_seasons`

#### Scenario: First stored season
- **WHEN** the season value is computed for redraft 2021
- **THEN** the prior is the mean of 2021's projected weekly levels

### Requirement: 3.5.5 Replacement levels stored
The system SHALL write, per league and season, `data/replacement/<league>/<season>.json` holding the weekly projected and realised levels by position, the season values, the N used and the free-agent counts.

**Traces to:** 3.5; 6
**Verified by:** Test: `tests/test_replacement.py::test_write_replacement_covers_every_season_and_uses_comparable_priors`

#### Scenario: Past seasons
- **WHEN** the replacement command runs
- **THEN** every stored season of every configured league gets a file

### Requirement: 3.5.5.1 Refreshed by the cold run
Every cold run SHALL rewrite the current season's replacement file.

**Traces to:** 3.5.5; 5
**Verified by:** Test: `tests/test_refresh.py::test_refresh_runs_every_step_when_sources_work`

#### Scenario: Week 11 cold run
- **WHEN** a cold run happens in week 11
- **THEN** the 2026 file lists weeks 1 to 17 with projected levels for every position and realised levels for the played weeks
