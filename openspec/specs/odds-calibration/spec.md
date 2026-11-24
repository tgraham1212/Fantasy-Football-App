# odds-calibration Specification

## Purpose

How well the Forecasts match what happened: completed seasons replayed from stored data, the probabilities the simulation would have published compared with real results, the report, and the calibration page that shows it and explains how the Forecasts are made. It delivers need 7, Checked Forecasts, and, through the explanation, need 8, Open Methods; the formulas are in `Calculations.txt`, section 18.

## Requirements

### Requirement: 7.1 Season replay
The system SHALL replay every stored completed league-season through the season simulation, as of every week from 0 (preseason) through the week before the final playoff round, using only that season's stored data.

**Rationale:** Calculations.txt section 18.
**Traces to:** 7; 1.1
**Verified by:** Test: `tests/test_calibrate.py::test_replay_season_stores_every_as_of_week_and_leaves_other_seasons_alone`; Test: `tests/test_calibrate.py::test_run_calibration_end_to_end_on_fixture`

#### Scenario: Replay a completed season
- **WHEN** calibration runs with the 2024 redraft season stored as complete
- **THEN** Forecasts exist for the 2024 redraft season as of weeks 0 to 16

### Requirement: 7.1.1 Replays stored as history
Each replay SHALL be stored in the Forecast history under its league, season and as-of week.

**Traces to:** 7.1; 1.2
**Verified by:** Test: `tests/test_calibrate.py::test_replay_season_stores_every_as_of_week_and_leaves_other_seasons_alone`

#### Scenario: Replayed weeks
- **WHEN** the 2025 dynasty season is replayed
- **THEN** its as-of-week Forecasts are stored under dynasty, 2025 and each week

### Requirement: 7.1.2 Completed seasons only
Calibration SHALL replay only completed seasons, leaving the season in progress unchanged.

**Traces to:** 7.1
**Verified by:** Test: `tests/test_calibrate.py::test_completed_seasons_excludes_the_season_in_progress`

#### Scenario: Current season is not replayed
- **WHEN** calibration runs while the 2026 season is in progress
- **THEN** no 2026 Forecast is produced or changed by calibration

### Requirement: 7.1.3 Leave-season-out model
A replay's error pools and drift fit SHALL come only from seasons other than the one replayed.

**Rationale:** A replay must never learn from the season it forecasts.
**Traces to:** 7.1; 1.1.5; 1.1.6.1
**Verified by:** Test: `tests/test_noise.py::test_residuals_from_stored_data`; Test: `tests/test_calibrate_model.py::test_replay_leaves_the_replayed_season_out_of_the_drift_model`

#### Scenario: Pools exclude the replayed season
- **WHEN** the 2023 dynasty season is replayed
- **THEN** no 2023 residual from either league is in the error pools, and the dynasty drift fit uses the other dynasty seasons only

### Requirement: 7.1.4 Replacement levels as they stood
A replayed week's replacement levels SHALL come from that week's free agents as they stood then.

**Traces to:** 7.1; 1.1.4.1
**Verified by:** Test: `tests/test_replacement.py::test_rostered_sets_from_season_data`; Test: `tests/test_replacement.py::test_write_replacement_covers_every_season_and_uses_comparable_priors`

#### Scenario: Week 6 of 2024
- **WHEN** week 6 of 2024 is replayed
- **THEN** its replacement levels come from the Players unrostered in week 6 of 2024

### Requirement: 7.2 Score calibration
For every replayed as-of week, the report SHALL give, per league and overall, where each team's actual next-week score fell in its simulated distribution, the share of actual scores inside the 50%, 80% and 95% central intervals, and the mean simulated-minus-actual difference.

**Traces to:** 7
**Verified by:** Test: `tests/test_calibrate.py::test_pit_and_coverage_on_calibrated_noise`; Test: `tests/test_calibrate.py::test_pit_edge_cases`

#### Scenario: Noise too narrow
- **WHEN** actual scores land outside the simulated 80% interval in 35% of team-weeks
- **THEN** the report shows 65% observed coverage against the 80% nominal interval

### Requirement: 7.3 Game calibration
For every replayed as-of week, the report SHALL group each team's win probability for its next game into 10-point bins, with the observed win rate and count in each bin, and give the Brier score.

**Traces to:** 7; 2.3
**Verified by:** Test: `tests/test_calibrate.py::test_reliability_bins_and_brier`; Test: `tests/test_calibrate.py::test_win_probability_counts_ties_half`

#### Scenario: Reliability bins
- **WHEN** 80 games had a simulated favourite at 60-70%
- **THEN** the 60-70% bin shows how many of those 80 the favourite won

### Requirement: 7.4 Season outcome calibration
For each season outcome (playoffs, bye, final, title, losers bracket, last place, avoiding the bottom two), the report SHALL give 10-point reliability bins with observed rates and counts, and the Brier score, against the outcomes in the stored standings and brackets.

**Traces to:** 7; 1.1.9
**Verified by:** Test: `tests/test_calibrate.py::test_season_outcomes_from_standings_and_bracket`; Test: `tests/test_calibrate.py::test_season_rows_have_expected_shape`

#### Scenario: Thirty percent means thirty percent
- **WHEN** teams were shown a 25-35% playoff probability in 150 team-weeks
- **THEN** the 30% bin reports how many of those 150 made the playoffs

#### Scenario: Actual outcomes from stored data
- **WHEN** the 2025 dynasty winners bracket names roster 4 as champion
- **THEN** roster 4's title outcome for every 2025 as-of week is true and every other roster's false

### Requirement: 7.4.1 Decided outcomes left out
An outcome already decided as of a week SHALL be left out of that week's comparison.

**Traces to:** 7.4
**Verified by:** Test: `tests/test_calibrate.py::test_included_as_of_weeks_stop_before_the_deciding_week`

#### Scenario: Regular season over
- **WHEN** the regular season is over as of week 14
- **THEN** playoff, bye, losers-bracket, last-place and bottom-two probabilities from week 14 on are left out, while title and final probabilities count until the round that decides them

### Requirement: 7.5 Naive baseline
For each season outcome, the report SHALL give the Brier score of a naive baseline and the simulation's skill against it.

**Traces to:** 7; 7.4
**Verified by:** Test: `tests/test_calibrate.py::test_baseline_is_base_rate_before_the_season`

#### Scenario: Better than the standings
- **WHEN** the simulation's Brier score for playoffs is lower than the baseline's
- **THEN** the report shows a positive skill score for playoffs

### Requirement: 7.5.1 Baseline before the season
Before any week is played, the baseline SHALL give every team the outcome's league-wide base rate.

**Traces to:** 7.5
**Verified by:** Test: `tests/test_calibrate.py::test_baseline_is_base_rate_before_the_season`

#### Scenario: Preseason baseline
- **WHEN** the baseline is evaluated as of week 0 of a 12-team league
- **THEN** every team's baseline playoff probability is 50% and title probability 8.3%

### Requirement: 7.5.2 Baseline during the season
Once weeks are played, the baseline SHALL extrapolate each team's record over the remaining weeks and rank teams on it, moving from the base rate toward that ranking as the season goes on.

**Traces to:** 7.5
**Verified by:** Test: `tests/test_calibrate.py::test_baseline_mid_season_lies_between_base_rate_and_indicator`; Test: `tests/test_calibrate.py::test_baseline_follows_standings_when_the_season_is_over`

#### Scenario: Mid-season
- **WHEN** a team is 7-2 after week 9
- **THEN** its baseline playoff probability lies between the base rate and its standings ranking

### Requirement: 7.6 Lineup gap
For every stored team-week with projections, the report SHALL give, per league, the mean projected-points and actual-points gap between the best projected lineup and the lineup the Manager started.

**Rationale:** Measures the simulation's assumption that Managers start their best lineup.
**Traces to:** 7; 1.1.4
**Verified by:** Test: `tests/test_calibrate.py::test_lineup_gap_is_zero_when_starters_are_optimal_and_positive_when_not`

#### Scenario: Managers leave points on the bench
- **WHEN** the best projected lineup averages 3.2 more projected points than the lineups Managers started
- **THEN** the report shows a 3.2-point projected lineup gap for that league

### Requirement: 7.7 Calibration report
The system SHALL write the results as `data/calibration/report.json` and a Markdown summary, `data/calibration/report.md`, each recording when it was produced, the runs per replay, the residual scale, the seasons replayed and the sample count behind every rate.

**Traces to:** 7
**Verified by:** Test: `tests/test_calibrate.py::test_report_json_and_markdown_agree_and_rerun_replaces`

#### Scenario: Report written
- **WHEN** calibration finishes
- **THEN** both report files are written and agree on every figure

### Requirement: 7.7.1 Re-run replaces the report
A new calibration run SHALL replace both report files.

**Traces to:** 7.7
**Verified by:** Test: `tests/test_calibrate.py::test_report_json_and_markdown_agree_and_rerun_replaces`

#### Scenario: Different residual scale
- **WHEN** calibration runs again with a different residual scale
- **THEN** both report files are replaced and name the new residual scale

### Requirement: 7.7.2 Roster drift diagnostic
The report SHALL give, per league at horizons including 2, 5 and 12 weeks, the reversion slope and drift spread under both the frozen and the replacement-floored roster, with the N used.

**Rationale:** Lets the floor's effect and the choice of N be judged from roster facts rather than outcomes.
**Traces to:** 7.7; 1.1.6.1
**Verified by:** Test: `tests/test_calibrate_model.py::test_report_records_switches_models_and_diagnostic`

#### Scenario: Diagnostic present
- **WHEN** calibration finishes
- **THEN** each league shows slopes and drift spreads at 2, 5 and 12 weeks for both roster treatments

### Requirement: 7.8 Calibration on demand
Calibration SHALL run as its own command, outside the cold run.

**Rationale:** A full replay takes far longer than a refresh.
**Traces to:** 7; 5
**Verified by:** Inspection: `src/ffapp/cli.py`, the cold run's steps include no calibration

#### Scenario: Scheduled job unaffected
- **WHEN** the cold run runs
- **THEN** no season replay or calibration report is produced

### Requirement: 7.8.1 Repeatable report
Given the same stored data, runs and seed, calibration SHALL produce an identical report apart from its production time.

**Traces to:** 7.8; 1.1.10
**Verified by:** Test: `tests/test_calibrate.py::test_same_data_runs_and_seed_give_an_identical_report`

#### Scenario: Run twice
- **WHEN** calibration runs twice on the same data with the same runs and seed
- **THEN** both reports carry the same figures

### Requirement: 7.8.2 Command-line settings
The calibrate command SHALL take the run count, a residual scale and switches that turn off the replacement floor or the roster drift, leaving the configuration file unchanged.

**Traces to:** 7.8
**Verified by:** Test: `tests/test_calibrate_model.py::test_switches_reach_the_replay`; Test: `tests/test_noise.py::test_build_pools_takes_scale_from_config_or_argument`

#### Scenario: Measure one piece alone
- **WHEN** calibration runs with the roster drift switched off
- **THEN** the replay applies the replacement floor but no drift, and the report records that drift was off

### Requirement: 7.9 Calibration page
The site SHALL have a calibration page titled "How Good Are These Forecasts?", linked from every league page.

**Traces to:** 7; 9
**Verified by:** Test: `tests/layout/test_calibration_page.py::test_page_is_titled_and_linked_from_the_league_pages`

#### Scenario: Open the page
- **WHEN** a visitor follows the footer link on a league page
- **THEN** the calibration page opens with its title

### Requirement: 7.9.1 Calibration page contents
The calibration page SHALL show each season outcome's Forecast against its observed rate with the count behind each point, the score coverage against nominal, the Brier skill against the baseline, the lineup gap per league, when the report was produced, the seasons it covers, the residual scale and the known caveats.

**Traces to:** 7.9; 7.2; 7.4
**Verified by:** Inspection: the live calibration page, each listed figure is present

#### Scenario: Visitor checks the Forecasts
- **WHEN** a visitor opens the calibration page after a report has been published
- **THEN** they can see how often teams shown at each playoff probability made the playoffs

### Requirement: 7.9.2 Calibration not yet run
Without a published report, the calibration page SHALL say that calibration has not been run.

**Traces to:** 7.9
**Verified by:** Test: `tests/layout/test_calibration_page.py::test_not_run_message_without_a_report`

#### Scenario: Calibration not yet run
- **WHEN** the site is published without a calibration report
- **THEN** the calibration page says calibration has not been run and the league pages work as before

### Requirement: 7.10 Calibration report exported
The export SHALL include the stored calibration report in the site data when one exists.

**Traces to:** 7; 7.9; 7.7
**Verified by:** Test: `tests/test_export.py::test_export_includes_calibration_report_when_present`

#### Scenario: Report present
- **WHEN** the export runs after calibration has been run
- **THEN** the site data contains the stored report

### Requirement: 7.10.1 Export without a report
The export SHALL succeed on a store that has never been calibrated.

**Traces to:** 7.10
**Verified by:** Test: `tests/test_export.py::test_exported_schema`

#### Scenario: Report absent
- **WHEN** the export runs on a store that has never been calibrated
- **THEN** the league files are written as usual and the export succeeds

### Requirement: 8.1 Forecasts explained
The calibration page SHALL explain in plain language how the Forecasts are made: Projections, score error from past seasons, best lineups with the replacement-level floor, and roster drift.

**Traces to:** 8; 7.9
**Verified by:** Inspection: the live calibration page, the "how it works" card covers the four parts

#### Scenario: Member reads the explanation
- **WHEN** a Manager opens the calibration page
- **THEN** they can read what a replacement-level Player is and how each part works

### Requirement: 8.1.1 Live model numbers
The explanation SHALL show each league's current replacement level per position and how much of a 20-point edge the model expects a team to keep 2 and 12 weeks ahead, from the published drift fit.

**Traces to:** 8.1; 1.1.6
**Verified by:** Test: `tests/layout/test_calibration_page.py::test_explanation_uses_the_published_model`

#### Scenario: Edge kept
- **WHEN** the redraft drift slopes are 0.89 at two weeks and 0.73 at twelve
- **THEN** the page says a team 20 points better keeps about 18 points two weeks out and 15 twelve weeks out

### Requirement: 8.1.2 Model switches stated
The calibration page SHALL state whether the replacement floor and roster drift were on for the shown report, and the N used.

**Traces to:** 8.1; 7.7
**Verified by:** Test: `tests/layout/test_calibration_page.py::test_switches_and_n_are_stated`

#### Scenario: Switches stated
- **WHEN** the calibration page shows a report run with both switches on and N of 5
- **THEN** it says "replacement floor on (best 5 free agents)" and "roster drift on"

### Requirement: 8.1.3 Replacement levels exported
Each league's site data SHALL include the current season's replacement levels, the next unplayed week's level per position, the season values and the N used, with the drift model in force.

**Traces to:** 8.1; 8.1.1
**Verified by:** Test: `tests/test_export.py::test_export_carries_replacement_levels_and_model_when_present`

#### Scenario: Levels present
- **WHEN** the export runs after the replacement and simulate commands
- **THEN** both league files carry the next unplayed week's replacement levels and the drift fit

### Requirement: 8.1.3.1 Export without replacement levels
The export SHALL succeed without replacement or model files, leaving those fields out so that the page explains the model without the live numbers.

**Traces to:** 8.1.3
**Verified by:** Test: `tests/test_export.py::test_export_carries_replacement_levels_and_model_when_present`

#### Scenario: Levels absent
- **WHEN** the export runs on a store without replacement files
- **THEN** the league files are written without the replacement fields
