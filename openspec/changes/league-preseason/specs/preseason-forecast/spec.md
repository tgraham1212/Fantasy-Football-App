## Purpose

The preseason Forecast made once each season when the draft is complete: every team's drafted roster played through the real schedule by the season simulation, Players valued from their preseason projected stat lines, with injury absences filled from the bench, and each team graded A+ to F from its title, playoff and last-place shares. It serves need 1, Season Forecasts, through `preseason-page`; the formulas are in `Calculations.txt`.

## ADDED Requirements

### Requirement: 1.5 Preseason Forecast
For each league-season with a complete draft, the system SHALL make one preseason Forecast and keep it unchanged as a record.

**Rationale:** A preseason grade judges the draft as it stood; later weeks must not change it.
**Traces to:** 1
**Verified by:** Test: `tests/test_preseason.py::test_preseason_forecast_made_once`

#### Scenario: Second cold run
- **WHEN** the 2026 redraft preseason Forecast is stored and another cold run starts
- **THEN** the stored Forecast is left byte for byte as it was

### Requirement: 1.5.1 Preseason values
A Player's preseason per-game value SHALL be his preseason projected season stat line scored with the league-season's scoring, divided by 17, and 0 in his NFL team's bye week.

**Rationale:** A full-season line carries no week-to-week opponent effect.
**Traces to:** 1.5
**Verified by:** Test: `tests/test_preseason.py::test_preseason_value_from_stat_line`

#### Scenario: Running back
- **WHEN** a back's 2024 line projects 1,218 rushing yards, 12 rushing touchdowns, 67 receptions, 527 receiving yards and 4 receiving touchdowns in half-PPR scoring
- **THEN** his per-game value is 304.0 / 17 = 17.88 points, to 0.01

### Requirement: 1.5.1.1 Projection sources
Preseason stat lines SHALL come from ESPN's season projections, with kickers and defences valued from their week-1 Projection.

**Rationale:** ESPN keeps the preseason line for Players hurt early, but serves no points for kickers and defences.
**Traces to:** 1.5.1
**Verified by:** Test: `tests/test_preseason.py::test_projection_sources`

#### Scenario: Kicker
- **WHEN** a drafted kicker's week-1 Projection is 9.0 points
- **THEN** his per-game value is 9.0

### Requirement: 1.5.1.1.1 Season under way
A season already under way when its preseason Forecast is made SHALL take every Player's value from his week-1 Projection.

**Rationale:** During a season, ESPN's and Sleeper's season lines are live: updated, and blank for Players since hurt.
**Traces to:** 1.5.1.1
**Verified by:** Test: `tests/test_preseason.py::test_season_under_way_uses_week_one`

#### Scenario: 2026 backfill
- **WHEN** the 2026 preseason Forecast is first made in week 12
- **THEN** every value comes from the 2026 week-1 Projections

### Requirement: 1.5.1.1.2 2023 sources
The 2023 preseason values SHALL come from Sleeper's season projections, and for a Player Sleeper has none for, from his week-1 Projection.

**Rationale:** ESPN's 2023 season lines are blank for many top Players.
**Traces to:** 1.5.1.1
**Verified by:** Test: `tests/test_preseason.py::test_projection_sources`

#### Scenario: 2023 Player without a Sleeper line
- **WHEN** a 2023 Player has no Sleeper season projection and a week-1 Projection of 11.2 points
- **THEN** his per-game value is 11.2

### Requirement: 1.5.1.2 Player matching
ESPN Players SHALL be matched to Sleeper Players by normalised name, position and NFL team, with defences matched by team.

**Traces to:** 1.5.1; 1.5.1.1
**Verified by:** Test: `tests/test_preseason.py::test_espn_matching`

#### Scenario: Name suffix
- **WHEN** ESPN lists "Kenneth Walker III" and Sleeper lists "Kenneth Walker", both Seattle running backs
- **THEN** the two are matched

### Requirement: 1.5.2 Preseason rosters
The preseason rosters SHALL be the drafted rosters in redraft and the week-1 rosters without taxi Players in dynasty.

**Traces to:** 1.5
**Verified by:** Test: `tests/test_preseason.py::test_preseason_rosters`

#### Scenario: Dynasty taxi
- **WHEN** a dynasty roster in week 1 holds 3 taxi Players
- **THEN** its preseason roster leaves those 3 out

### Requirement: 1.5.2.1 Missing kicker or defence
A team with no kicker or no defence on its preseason roster SHALL score that position's preseason replacement level in that slot each week: the mean value of the 3 best unrostered Players at the position.

**Rationale:** Kickers and defences are often streamed; the level shares the values' projections and scale.
**Traces to:** 1.5.2; 3.5
**Verified by:** Test: `tests/test_preseason.py::test_missing_kicker_scores_replacement_level`

#### Scenario: No kicker drafted
- **WHEN** a redraft team drafted no kicker
- **THEN** its kicker slot scores the mean preseason value of the 3 best kickers on no roster each week

### Requirement: 1.5.3 Absences
In each simulated week, each rostered Player SHALL miss the game with his position's injury rate: QB 10.6%, RB 11.9%, WR 11.4%, TE 10.2%, K 4.4%, DEF 0%, each to 0.1%.

**Rationale:** The rates are the share of team games preseason starters missed while IR, PUP or Out in 2021 to 2025, pooled across seasons.
**Traces to:** 1.5
**Verified by:** Test: `tests/test_preseason.py::test_absence_rates`

#### Scenario: 100,000 running-back weeks
- **WHEN** 100,000 running-back weeks are simulated
- **THEN** between 11.6% and 12.2% of them are absences

### Requirement: 1.5.3.1 Bench fills in
An absent starter's slot SHALL be filled by the highest-valued healthy bench Player eligible for it and worth at least the slot's replacement level, else by that replacement level.

**Rationale:** A Manager would pick up a free agent rather than start a bench Player worth less than one.
**Traces to:** 1.5.3
**Verified by:** Test: `tests/test_preseason.py::test_bench_fills_absent_starter`

#### Scenario: Backup running back
- **WHEN** a team's RB1 is absent and its best healthy bench running back is worth 9.0 points a game
- **THEN** that week the RB slot scores from the 9.0-point back

### Requirement: 1.5.4 Preseason outcomes
For each team, the preseason Forecast SHALL give the title, playoff and last-place shares to 0.001, the forecast wins and losses to 0.1 and the points per week to 0.1.

**Traces to:** 1.5; 1.1.9
**Verified by:** Test: `tests/test_preseason.py::test_outcomes`

#### Scenario: Shares add up
- **WHEN** the 2025 redraft preseason Forecast is made
- **THEN** the title shares add to 1.000, within 0.001

### Requirement: 1.5.4.1 Wins Saved
For each team, the preseason Forecast SHALL give its Wins Saved to 0.01: its mean wins, minus its mean wins on the same draws when only its own absent starters are replaced at replacement level.

**Traces to:** 1.5.4; 1.5.3.1
**Verified by:** Test: `tests/test_preseason.py::test_wins_saved`

#### Scenario: Empty bench
- **WHEN** a team's bench holds no Player eligible for any starting slot
- **THEN** its Wins Saved is 0.00

### Requirement: 1.5.5 Preseason grade
Each team SHALL be graded, in this order: A for a title share of 15% or more; B for 11% or more, or a playoff share of 65% or more; F for a last-place share of 20% or more; C for a playoff share of 35% or more; D otherwise.

**Rationale:** An F needs a team truly likely to finish last, so many seasons have none.
**Traces to:** 1.5; 1.5.4
**Verified by:** Test: `tests/test_preseason.py::test_grade_letters`

#### Scenario: Title contender
- **WHEN** a team's title share is 29.7%
- **THEN** its grade letter is A

### Requirement: 1.5.5.1 Plus and minus
A grade SHALL carry a plus or minus near the edges of its band: A+ for a title share of 25% or more and A- below 18%; B+ for 11% or more; B- for a playoff share below 72%; C+ for 58% or more and C- below 42%; D+ for 28% or more; D- for a last-place share of 13% or more.

**Traces to:** 1.5.5
**Verified by:** Test: `tests/test_preseason.py::test_plus_and_minus`

#### Scenario: Near last place
- **WHEN** a team's playoff share is 30% and its last-place share 15.5%
- **THEN** its grade is D-

### Requirement: 1.5.6 Actual finish
For a finished season, the preseason Forecast export SHALL give each team's final place beside its grade.

**Traces to:** 1.5
**Verified by:** Test: `tests/test_preseason.py::test_actual_finish`

#### Scenario: 2025 champion
- **WHEN** the 2025 redraft season is complete
- **THEN** the champion's row shows final place 1

### Requirement: 1.5.6.1 Draft strength
For a redraft season, the preseason Forecast export SHALL give each team's draft strength: its rank by preseason points per week, 1 for the highest, equal values sharing a rank.

**Rationale:** In redraft, preseason strength has not predicted results (backtest 2021 to 2025), but who drafted best on paper is still worth seeing.
**Traces to:** 1.5.6; 1.5.4
**Verified by:** Test: `tests/test_preseason.py::test_draft_strength_rank`

#### Scenario: Strongest draft
- **WHEN** a redraft team's preseason points per week is 109.9, the highest of the season
- **THEN** its draft strength is 1

### Requirement: 1.5.7 Preseason export
The export SHALL write one preseason file per league, holding every stored preseason Forecast of that league.

**Traces to:** 1.5
**Verified by:** Test: `tests/test_preseason.py::test_export_writes_preseason_file`

#### Scenario: Build
- **WHEN** `python -m ffapp build` runs
- **THEN** each configured league has a preseason file with an entry for each season that has a preseason Forecast

### Requirement: 1.5.8 Preseason Forecast timing
A season's preseason Forecast SHALL be made at the first cold run after its draft is complete and its preseason values are available.

**Traces to:** 1.5
**Verified by:** Test: `tests/test_preseason.py::test_made_after_the_draft`

#### Scenario: Draft day
- **WHEN** the 2027 redraft draft completes on Saturday
- **THEN** the next cold run makes the 2027 preseason Forecast, and no run before the draft completes does
