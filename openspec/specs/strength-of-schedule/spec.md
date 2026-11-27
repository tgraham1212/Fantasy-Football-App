# strength-of-schedule Specification

## Purpose

The league's strength of schedule figures behind the League sub-tab's Strength of Schedule tab: Weekly Ranks (how strong each Manager's opponents were) and Schedule Swap (each Manager's wins with every other Manager's schedule, and the Schedule Difficulty Index), for every stored season, with upcoming weeks taken from the season Forecast. It serves need 4, Manager History, through `strength-of-schedule-page`; the formulas are in `Calculations.txt`.

## Requirements

### Requirement: 4.10 Strength of schedule export
The export SHALL write one strength of schedule file per league, holding the Weekly Ranks and Schedule Swap figures for every stored season of that league.

**Traces to:** 4
**Verified by:** Test: `tests/test_schedule_strength.py::test_export_writes_schedule_file`

#### Scenario: Build
- **WHEN** `python -m ffapp build` runs
- **THEN** each configured league has a strength of schedule file in the site data with an entry for each stored season

### Requirement: 4.10.1 Regular season only
Strength of schedule figures SHALL use regular-season weeks only.

**Rationale:** Playoff opponents are earned, not scheduled.
**Traces to:** 4.10
**Verified by:** Test: `tests/test_schedule_strength.py::test_regular_season_only`

#### Scenario: Playoff week
- **WHEN** a dynasty season has 14 regular-season weeks and 3 playoff weeks
- **THEN** each team's figures cover exactly 14 weeks

### Requirement: 4.10.2 Weekly rank
Each regular-season week, a team's weekly rank SHALL be 1 plus the number of teams that scored more than it that week.

**Rationale:** Equal scores then share the better rank.
**Traces to:** 4.10
**Verified by:** Test: `tests/test_schedule_strength.py::test_weekly_rank_ties_share_the_better_rank`

#### Scenario: Two equal scores
- **WHEN** two teams both score 131.20, the second-highest score of the week
- **THEN** both have weekly rank 2 and the next team has rank 4

### Requirement: 4.10.2.1 Opponent rank averages
For each team, the export SHALL give the mean of its opponents' weekly ranks over the played weeks, the upcoming weeks and the whole regular season, each to 0.01.

**Traces to:** 4.10.2
**Verified by:** Test: `tests/test_schedule_strength.py::test_opponent_rank_averages`

#### Scenario: Week 11 of 14
- **WHEN** a team's opponents ranked 2, 6 and 4 in weeks 1-3 and 11 more weeks follow
- **THEN** its played average includes 2, 6 and 4 and its season average covers all 14 weeks

### Requirement: 4.10.2.2 Weekly Ranks order
Teams SHALL be ranked by their season mean opponent rank, lowest first, as the hardest schedule, with equal means sharing a rank.

**Traces to:** 4.10.2
**Verified by:** Test: `tests/test_schedule_strength.py::test_weekly_ranks_order`

#### Scenario: Toughest opponents
- **WHEN** a team's season mean opponent rank is 4.43, the lowest in the league
- **THEN** it ranks 1st, the hardest schedule

### Requirement: 4.10.3 Upcoming weeks
For a regular-season week not yet final, a team's weekly score SHALL be its mean forecast score from the latest season Forecast.

**Rationale:** Upcoming weeks then match the Forecasts shown elsewhere on the site.
**Traces to:** 4.10; 1.1.9.3
**Verified by:** Test: `tests/test_schedule_strength.py::test_upcoming_weeks_use_the_forecast`

#### Scenario: Week in progress
- **WHEN** week 12 has kicked off but is not final
- **THEN** week 12 uses the forecast scores from the latest Forecast and counts as upcoming

### Requirement: 4.10.4 Schedule swap wins
For each pair of Managers A and B, the export SHALL give A's wins using A's weekly scores against B's opponent each week, A playing B in the weeks B's opponent is A.

**Traces to:** 4.10
**Verified by:** Test: `tests/test_schedule_strength.py::test_swap_substitutes_the_schedule_manager`

#### Scenario: Schedule's Manager plays you
- **WHEN** B's schedule has B playing A in week 5
- **THEN** A's week 5 under B's schedule compares A's score with B's

#### Scenario: Own schedule
- **WHEN** A and B are the same Manager
- **THEN** the wins equal A's actual wins plus A's forecast wins

### Requirement: 4.10.4.1 Played week wins
In a played week, a swapped game SHALL count 1 for a higher score, 0.5 for an equal score and 0 for a lower score.

**Traces to:** 4.10.4
**Verified by:** Test: `tests/test_schedule_strength.py::test_played_week_wins`

#### Scenario: Equal scores
- **WHEN** A and the swapped opponent both score 98.40
- **THEN** that game counts 0.5 wins

### Requirement: 4.10.4.2 Upcoming week wins
In a week not yet final, a swapped game SHALL count the win probability of that pairing from the latest season Forecast.

**Rationale:** Forecast wins are then fractional, as in the Forecasts, not a sure win for whoever has the higher mean.
**Traces to:** 4.10.4; 1.1.9.3
**Verified by:** Test: `tests/test_schedule_strength.py::test_upcoming_week_wins_use_pair_probabilities`

#### Scenario: Close pairing
- **WHEN** the Forecast gives A a 0.47 win probability against the swapped opponent in week 13
- **THEN** that game counts 0.47 wins

### Requirement: 4.10.4.3 Schedule Difficulty Index
For each Manager, the export SHALL give the Schedule Difficulty Index, the mean of their wins across all N schedules, their own included, minus their wins on their own schedule, to 0.01.

**Traces to:** 4.10.4
**Verified by:** Test: `tests/test_schedule_strength.py::test_difficulty_index`

#### Scenario: Unlucky schedule
- **WHEN** a Manager has 1.56 wins on their own schedule and averages 3.87 wins across all 12 schedules
- **THEN** their Schedule Difficulty Index is +2.31

### Requirement: 4.10.4.4 Schedule Swap order and range
Managers SHALL be ranked by Schedule Difficulty Index, highest first, as the hardest schedule, each with their lowest and highest wins across all N schedules.

**Traces to:** 4.10.4
**Verified by:** Test: `tests/test_schedule_strength.py::test_swap_order_and_range`

#### Scenario: Range
- **WHEN** a Manager's wins across the 12 schedules run from 7.3 to 13.5
- **THEN** their range is 7.3 to 13.5
