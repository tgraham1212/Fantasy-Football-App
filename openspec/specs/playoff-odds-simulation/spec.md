# playoff-odds-simulation Specification

## Purpose

Forecasts each team's regular-season and playoff outcomes by simulating the rest of a league's season many times, and keeps those Forecasts week by week. It delivers need 1, Season Forecasts; the formulas are in `Calculations.txt`, sections 4 to 9.

## Requirements

### Requirement: 1.1 Season simulation
Each season Forecast SHALL come from simulating the rest of the league's season, from the as-of week through the final playoff round, at least 10,000 times.

**Rationale:** 10,000 runs put the sampling error of a 50% outcome near ±0.5 percentage point.
**Traces to:** 1
**Verified by:** Inspection: `src/ffapp/cli.py`, every `--runs` default is 10,000

#### Scenario: A Forecast is made
- **WHEN** a cold run forecasts a league's season
- **THEN** the Forecast counts outcomes over at least 10,000 simulated seasons

### Requirement: 1.1.1 As-of week
Each Forecast SHALL be made as of the last week Sleeper has fully scored, with that week's and every earlier week's results taken from stored matchups.

**Rationale:** A week with only its Thursday game played is not yet scored, so it counts as unplayed (Calculations.txt section 7).
**Traces to:** 1.1
**Verified by:** Test: `tests/test_odds.py::test_as_of_is_last_scored_week_not_calendar_week`; Test: `tests/test_odds.py::test_fixed_records_only_count_completed_weeks`

#### Scenario: Mid-season run
- **WHEN** a Forecast is made for 2026 with weeks 1 to 9 scored
- **THEN** the results of weeks 1 to 9 are fixed and weeks 10 to 14 and the playoffs are simulated

#### Scenario: Week partly played
- **WHEN** a Forecast is made on the Friday after week 10's Thursday game
- **THEN** the as-of-week-9 Forecast treats week 10 as unplayed

### Requirement: 1.1.2 Real schedule
The simulation SHALL play each league's Sleeper matchup pairings for every remaining regular-season week.

**Traces to:** 1.1
**Verified by:** Test: `tests/test_odds.py::test_build_inputs_covers_remaining_schedule_and_playoffs`

#### Scenario: Remaining matchups
- **WHEN** week 12 pairs roster 3 against roster 8 in Sleeper
- **THEN** every simulated season plays roster 3 against roster 8 in week 12

### Requirement: 1.1.3 Rosters at the as-of week
Each team SHALL play every remaining week with the roster it held at the as-of week: its current Sleeper roster in a current run, or the roster it carried into the following week in a backfilled run.

**Traces to:** 1.1
**Verified by:** Test: `tests/test_odds.py::test_current_roster_excludes_reserve_and_taxi`; Test: `tests/test_odds.py::test_backfilled_roster_comes_from_next_week_matchup`

#### Scenario: Current run
- **WHEN** the Forecast is made for the current as-of week
- **THEN** each team plays with its current Sleeper roster

#### Scenario: Backfilled run
- **WHEN** the Forecast is remade as of week 5 of the current season
- **THEN** each team plays with the roster from its week-6 matchup

### Requirement: 1.1.3.1 Eligible starters
Only Players outside injured reserve and the taxi squad SHALL be eligible to start in a simulated week.

**Traces to:** 1.1.3
**Verified by:** Test: `tests/test_odds.py::test_current_roster_excludes_reserve_and_taxi`

#### Scenario: Player on injured reserve
- **WHEN** a team's best running back is on injured reserve
- **THEN** he starts in no simulated week

### Requirement: 1.1.4 Lineup selection
Each team SHALL start, in every simulated week, the legal lineup with the highest total projected points under its league's roster slots, with FLEX taking a running back, wide receiver or tight end.

**Rationale:** Managers are assumed to start their best lineup (Calculations.txt section 5).
**Traces to:** 1.1
**Verified by:** Test: `tests/test_lineup.py::test_flex_takes_the_better_of_third_rb_and_third_wr`; Test: `tests/test_lineup.py::test_bye_week_starter_is_replaced_by_bench_player`

#### Scenario: Flex choice
- **WHEN** a team's third-best running back projects 9.1 and its third-best wide receiver projects 11.4
- **THEN** the wide receiver fills the FLEX slot

#### Scenario: Bye week
- **WHEN** a team's starting tight end is on a bye and a bench tight end projects 5.0
- **THEN** the bench tight end starts at tight end

### Requirement: 1.1.4.1 Replacement floor
Every lineup slot SHALL be worth at least that week's projected replacement level for its position, and a FLEX slot at least the best of the running back, wide receiver and tight end levels.

**Rationale:** A hole is worth what a waiver pickup would score, not zero (Calculations.txt section 5).
**Traces to:** 1.1.4
**Verified by:** Test: `tests/test_odds.py::test_floor_fills_holes_and_weak_slots_but_leaves_strong_starters`

#### Scenario: Hole filled at replacement level
- **WHEN** a team has no tight end with a positive projection in week 12 and the week-12 tight end replacement level is 6.8
- **THEN** the team's tight end slot is worth 6.8 projected points that week

#### Scenario: Weak starter floored
- **WHEN** a team's best available second running back projects 3.1 and the running back replacement level is 7.5
- **THEN** the slot is worth 7.5 projected points

#### Scenario: Strong starter unaffected
- **WHEN** a team's starter projects 14.0 and the replacement level is 7.5
- **THEN** the slot is worth 14.0

### Requirement: 1.1.4.1.1 Replacement fill error
A slot filled at replacement level SHALL draw its score error like a Player with that projection at that position.

**Traces to:** 1.1.4.1; 1.1.5
**Verified by:** Test: `tests/test_odds.py::test_replacement_fill_draws_error_like_a_player_at_that_level`

#### Scenario: Floored tight end
- **WHEN** a tight end slot is filled at a replacement level of 6.8
- **THEN** its simulated score is 6.8 plus an error drawn from tight ends projected near 6.8

### Requirement: 1.1.5 Score error
Each Player's simulated score in every regular-season and playoff week SHALL be their Projection plus an error drawn at random from the residuals of Players at the same position and projection band.

**Rationale:** Empirical pools keep the real skew of busts and booms (Calculations.txt section 4).
**Traces to:** 1.1
**Verified by:** Test: `tests/test_noise.py::test_band_assignment`; Test: `tests/test_noise.py::test_residuals_from_stored_data`

#### Scenario: Error pool
- **WHEN** a wide receiver projected for 14 points is simulated
- **THEN** the error is drawn from past residuals of wide receivers projected 14 to 18 points

### Requirement: 1.1.5.1 Small pool fallback
A position and projection band with fewer than 200 residuals SHALL draw its errors from all of that position's residuals.

**Rationale:** Below 200 residuals a pool's shape is too noisy to trust (Calculations.txt section 4).
**Traces to:** 1.1.5
**Verified by:** Test: `tests/test_noise.py::test_small_band_falls_back_to_position_pool`

#### Scenario: Few past results
- **WHEN** kickers projected 18 to 22 points have 40 past residuals
- **THEN** errors for such a kicker are drawn from all kicker residuals

### Requirement: 1.1.5.2 Residual scale
Each drawn error SHALL be multiplied by the configured residual scale, which is 1.0 when not set.

**Rationale:** Only calibration may change the scale (Calculations.txt section 4).
**Traces to:** 1.1.5
**Verified by:** Test: `tests/test_noise.py::test_scale_multiplies_draws_and_one_is_identity`

#### Scenario: Residual scale not configured
- **WHEN** the configuration has no residual scale
- **THEN** errors are used exactly as drawn

#### Scenario: Residual scale configured
- **WHEN** the residual scale is 1.2 and a drawn residual is +5.0 points
- **THEN** the error applied is +6.0 points

### Requirement: 1.1.6 Roster drift
At k weeks ahead, each team's projected strength SHALL be moved toward the league mean by the reversion slope for horizon k, plus a random walk, kept for the whole run, whose spread at horizon k is the drift spread.

**Rationale:** Rosters change, so an edge only partly survives (Calculations.txt section 6).
**Traces to:** 1.1
**Verified by:** Test: `tests/test_drift.py::test_slope_shrinks_edge_toward_mean`; Test: `tests/test_drift.py::test_drift_noise_grows_and_persists`

#### Scenario: Far weeks are less certain
- **WHEN** the redraft reversion slope is 0.89 at two weeks and 0.73 at twelve weeks
- **THEN** a team 20 points above the league mean is simulated at +17.8 two weeks out and +14.6 twelve weeks out, before the random walk

#### Scenario: Drift persists within a run
- **WHEN** a run's random walk puts a team at +3.0 in week 10
- **THEN** that team's week-11 drift in the same run starts from +3.0, not from zero

### Requirement: 1.1.6.1 Drift fit
The reversion slope and drift spread for each horizon SHALL be fitted per league by least squares from its stored completed seasons.

**Rationale:** Redraft rosters churn far more than dynasty ones, so each league gets its own fit (Calculations.txt section 6).
**Traces to:** 1.1.6
**Verified by:** Test: `tests/test_drift.py::test_slope_recovered_and_smoothed`; Test: `tests/test_drift.py::test_one_season_gives_identity_model`

#### Scenario: Only one season stored
- **WHEN** a league has a single completed season
- **THEN** the fit leaves strengths unchanged: slope 1.0 and spread 0 at every horizon

### Requirement: 1.1.7 Standings
Simulated standings SHALL rank teams by wins, a tie counting as half a win, then by total points scored.

**Traces to:** 1.1
**Verified by:** Test: `tests/test_standings.py::test_hand_checked_four_team_season_with_a_tie`; Test: `tests/test_standings.py::test_points_break_equal_records`

#### Scenario: Tied records
- **WHEN** two teams both finish 8-6 and one has more points scored
- **THEN** the team with more points scored ranks higher

### Requirement: 1.1.7.1 Seeding
The top six teams in the simulated standings SHALL make the playoffs, with seeds 1 and 2 taking first-round byes.

**Traces to:** 1.1.7
**Verified by:** Test: `tests/test_standings.py::test_seeds_match_round_one_of_real_bracket`

#### Scenario: Final standings
- **WHEN** a simulated regular season ends
- **THEN** the top six teams are seeded 1 to 6 and seeds 1 and 2 skip round 1

### Requirement: 1.1.8 Bracket simulation
The simulation SHALL play the winners bracket for seeds 1 to 6 and the losers bracket for seeds 7 to 12 by the league's Sleeper bracket rules: re-seeding after round 1 or not, and a consolation bracket or a toilet bowl.

**Rationale:** Calculations.txt section 8.
**Traces to:** 1.1
**Verified by:** Test: `tests/test_bracket.py::test_reseed_bracket_pairs_seed_one_with_lowest_survivor`; Test: `tests/test_bracket.py::test_toilet_bowl_advances_the_lower_scorer`

#### Scenario: First round
- **WHEN** simulated seeding is complete
- **THEN** round 1 (week 15) plays seed 3 against 6 and seed 4 against 5 while seeds 1 and 2 sit out

### Requirement: 1.1.8.1 Supported playoff size
The simulation SHALL stop with an error naming the league, the season and the configured playoff size whenever a league's Sleeper settings give a playoff size other than six teams.

**Rationale:** The bracket logic plays only six-team brackets; a wrong Forecast is worse than none.
**Traces to:** 1.1.8
**Verified by:** Test: `tests/test_odds.py::test_unsupported_playoff_size_fails_loudly`

#### Scenario: League moves to eight playoff teams
- **WHEN** a league's settings give 8 playoff teams
- **THEN** the run stops with an error naming the league, the season and the size 8, and the published Forecasts stay as they were

#### Scenario: Six-team league
- **WHEN** a league's settings give 6 playoff teams
- **THEN** the simulation runs as before

### Requirement: 1.1.8.2 Completed playoff rounds
A playoff round already played SHALL take its results from Sleeper's stored bracket instead of simulating them.

**Traces to:** 1.1.8
**Verified by:** Test: `tests/test_simulate.py::test_completed_playoff_round_uses_real_points`

#### Scenario: Playoffs in progress
- **WHEN** a Forecast is made after week 15 is complete
- **THEN** week 15's bracket results come from Sleeper and only later rounds are simulated

### Requirement: 1.1.8.3 Bracket logic matches history
For every completed league-season, the bracket logic, seeded with the real final standings and given the real results, SHALL reproduce every winners and losers bracket pairing Sleeper stored.

**Rationale:** Checks the bracket rules against nine real seasons (`python -m ffapp verify-brackets`).
**Traces to:** 1.1.8; 7
**Verified by:** Test: `tests/test_verify.py::test_real_brackets_are_reproduced`

#### Scenario: Historical check passes
- **WHEN** the bracket check runs against the 2025 dynasty season
- **THEN** every pairing produced matches Sleeper's stored 2025 brackets

### Requirement: 1.1.8.3.1 Bracket mismatch reported
A bracket pairing that does not match Sleeper's SHALL fail the bracket check, naming the league-season and the pairing.

**Traces to:** 1.1.8.3
**Verified by:** Test: `tests/test_verify.py::test_mismatch_is_reported_with_league_season_and_pairing`

#### Scenario: Historical check fails
- **WHEN** a produced pairing does not match Sleeper's stored bracket
- **THEN** the check fails and names the league-season and the mismatched pairing

### Requirement: 1.1.9 Per-team results
For each team, a Forecast SHALL report the mean simulated wins, losses, ties and points, the seed distribution, and the share of runs reaching the playoffs, a bye, the semifinal, the final, the title, the losers bracket and last place.

**Rationale:** Last place means the lowest regular-season seed.
**Traces to:** 1.1
**Verified by:** Test: `tests/test_simulate.py::test_outcome_rates_sum_correctly`

#### Scenario: Team row
- **WHEN** a Forecast completes
- **THEN** each team has its projected record, seed distribution and seven outcome probabilities

### Requirement: 1.1.9.1 Outcomes add up
Across a 12-team league, outcome probabilities SHALL sum, each within 1 percentage point, to 600% (playoffs), 200% (bye), 400% (semifinal), 200% (final), 100% (title), 600% (losers bracket) and 100% (last place).

**Traces to:** 1.1.9
**Verified by:** Test: `tests/test_simulate.py::test_outcome_rates_sum_correctly`

#### Scenario: Results add up
- **WHEN** a Forecast completes for a 12-team league
- **THEN** the title probabilities of all teams sum to 100% within 1 percentage point

### Requirement: 1.1.9.2 Clinched spot
A team that has clinched a playoff spot under the stored results SHALL have a playoff probability of 100%.

**Traces to:** 1.1.9
**Verified by:** Test: `tests/test_simulate.py::test_clinched_team_has_certain_playoff_spot`

#### Scenario: Clinched team
- **WHEN** a team has clinched a playoff spot
- **THEN** its playoff probability is 100%

### Requirement: 1.1.9.3 Upcoming pairings
For each upcoming regular-season week, a Forecast SHALL report every team's mean simulated score and, for every pair of teams, the share of runs in which each outscores the other, ties counted as half.

**Rationale:** Strength of schedule compares teams that do not meet that week, using the same simulated scores as the Forecasts.
**Traces to:** 1.1.9; 4.10.3
**Verified by:** Test: `tests/test_simulate.py::test_upcoming_pairings`

#### Scenario: Pair that does not meet
- **WHEN** a Forecast is made after week 11 and teams A and B do not meet in week 12
- **THEN** it still gives A's and B's week 12 mean scores and A's win share against B, the two shares summing to 1 within 0.001

### Requirement: 1.1.10 Repeatability
Given the same stored data and random seed, the simulation SHALL produce identical results.

**Rationale:** A past Forecast can be reproduced exactly; each Forecast's seed comes from its league, season and as-of week.
**Traces to:** 1.1; 6
**Verified by:** Test: `tests/test_simulate.py::test_same_seed_gives_identical_results`

#### Scenario: Re-run with same seed
- **WHEN** the simulation is run twice with the same stored data and seed
- **THEN** both runs report identical per-team results

### Requirement: 1.1.11 Simulation time
A full-season simulation of 10,000 runs SHALL finish within 60 seconds.

**Rationale:** Hot runs simulate every minute during games and must finish before the next one starts.
**Traces to:** 1.1; 5
**Verified by:** Test: `tests/test_simulate.py::test_full_season_runs_fast_enough`

#### Scenario: Preseason Forecast
- **WHEN** a Forecast simulates all 14 regular-season weeks and the playoffs
- **THEN** the 10,000 runs finish within 60 seconds

### Requirement: 1.2 Forecast history
Each as-of Forecast SHALL be stored by league, season and as-of week, for current and replayed seasons alike, keeping every other week's and season's Forecast.

**Rationale:** The history shows how each team's Forecast changed week by week.
**Traces to:** 1; 6
**Verified by:** Test: `tests/test_odds.py::test_run_as_of_writes_history_and_rerun_replaces_only_same_week`

#### Scenario: Weekly accumulation
- **WHEN** Forecasts have been made as of weeks 0 to 10 of 2026
- **THEN** eleven Forecasts are stored for each league's 2026 season

#### Scenario: Replayed season stored beside the current one
- **WHEN** the 2024 season is replayed while 2026 Forecasts are stored
- **THEN** 2024 Forecasts are stored under 2024 and the 2026 Forecasts are unchanged

### Requirement: 1.2.1 Re-run replaces
A new Forecast for a league, season and as-of week that already has one SHALL replace it, unless that as-of week is frozen.

**Traces to:** 1.2
**Verified by:** Test: `tests/test_odds.py::test_run_as_of_writes_history_and_rerun_replaces_only_same_week`

#### Scenario: Same week re-run
- **WHEN** a second Forecast is made as of week 10 after a projection refresh
- **THEN** the as-of-week-10 Forecast is replaced and the other weeks' Forecasts are unchanged

### Requirement: 1.2.2 Model recorded
Each stored Forecast SHALL record its residual scale, its drift slopes and spreads by horizon, the seasons they were fitted from, and whether the replacement floor and the drift were on.

**Rationale:** A figure can be checked or reproduced only with the settings that made it.
**Traces to:** 1.2; 8
**Verified by:** Test: `tests/test_drift.py::test_simulate_league_records_model_and_writes_file`; Test: `tests/test_drift.py::test_switches_recorded_when_off`

#### Scenario: Recorded in results
- **WHEN** a Forecast is stored
- **THEN** it records the residual scale, the drift by horizon, the fitted seasons and both switches

### Requirement: 1.2.3 Frozen as-of Forecast
Once the first game of the week after an as-of week kicks off, the stored Forecast for that as-of week SHALL stay unchanged while runs save the league's single live Forecast instead.

**Rationale:** The history never sees a partly played week.
**Traces to:** 1.2
**Verified by:** Test: `tests/test_live.py::test_live_run_writes_live_file_and_leaves_the_as_of_result_frozen`

#### Scenario: Run after a kickoff
- **WHEN** a Forecast is made as of week 10 after week 11's Thursday game kicked off
- **THEN** the as-of-week-10 Forecast is unchanged and the league's live Forecast is replaced

### Requirement: 1.2.3.1 Week becomes final
When the live week becomes final, the next run SHALL store that week's as-of Forecast and remove the live Forecast.

**Traces to:** 1.2.3
**Verified by:** Test: `tests/test_live.py::test_non_live_run_removes_a_stale_live_file`

#### Scenario: Week becomes final
- **WHEN** week 11 is final in Sleeper
- **THEN** the next run stores the as-of-week-11 Forecast and removes the live Forecast until week 12's first kickoff

### Requirement: 1.2.4 Current-season backfill
The simulation SHALL produce, from stored data, the as-of Forecast for every earlier week of the current season, from week 0 (preseason) to the current as-of week.

**Traces to:** 1.2
**Verified by:** Test: `tests/test_odds.py::test_backfill_stores_every_as_of_week_of_the_current_season`

#### Scenario: 2026 backfill
- **WHEN** the backfill runs during 2026 week 10
- **THEN** Forecasts as of weeks 0 to 9 are made and stored for both leagues
