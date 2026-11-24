# game-predictions Specification

## Purpose

Game Forecasts from the season simulation: each game's scores and win probabilities, the projected playoff bracket, the log of how each game's Forecast moved before kickoff, the Forecast of record each finished game is judged against, the Model and Actual lineup views, lineup choices, and the season Forecast saved after each slate. It delivers need 2, Game Forecasts; the formulas are in `Calculations.txt`, sections 10 and 11.

## Requirements

### Requirement: 2.3 Game Forecasts
For every week the simulation plays, the stored result SHALL include, for each game, each team's mean simulated score, a histogram of its simulated scores in 2-point bins, and its win probability.

**Rationale:** Calculations.txt section 10.
**Traces to:** 2; 1.1
**Verified by:** Test: `tests/test_forecast.py::test_regular_week_games_cover_the_schedule`; Test: `tests/test_forecast.py::test_histogram_shares_sum_to_one_on_shared_bins`

#### Scenario: Regular-season game
- **WHEN** the simulation runs as of week 9
- **THEN** the stored result lists every week-10 to week-14 game with both teams' mean score, histogram and win probability

### Requirement: 2.3.1 Ties in the win probability
A simulated tie SHALL count as half a win in each team's win probability.

**Traces to:** 2.3
**Verified by:** Test: `tests/test_forecast.py::test_win_probability_splits_ties`

#### Scenario: Tied runs
- **WHEN** a team wins 60% of runs, loses 38% and ties 2%
- **THEN** its win probability is 61%

### Requirement: 2.3.2 Model lineup in the Forecast
Each game Forecast SHALL include each team's model lineup, with every slot's Player, position and projected points.

**Traces to:** 2.3; 1.1.4
**Verified by:** Test: `tests/test_forecast.py::test_regular_week_games_cover_the_schedule`

#### Scenario: Lineup stored
- **WHEN** a week-10 Forecast is stored
- **THEN** each team's model lineup lists every slot with its Player, position and projection

### Requirement: 2.3.2.1 Replacement fill marked
A slot filled at replacement level SHALL be marked as a free-agent fill.

**Traces to:** 2.3.2; 1.1.4.1
**Verified by:** Test: `tests/test_forecast.py::test_replacement_fill_is_marked`

#### Scenario: Replacement fill
- **WHEN** the model fills a team's TE slot with the replacement level of 6.4
- **THEN** that slot is stored as a free-agent TE fill projected at 6.4

### Requirement: 2.3.3 Projected playoff bracket
For a playoff week whose pairings Sleeper has not set, the system SHALL project the league's bracket: seeds by expected seed from the simulations, pairings by the league's bracket rules, and the team with the higher win probability advancing from each projected game.

**Traces to:** 2.3; 1.1.8
**Verified by:** Test: `tests/test_forecast.py::test_projected_bracket_seeds_by_expectation_and_favourite_advances`

#### Scenario: Semifinal projection
- **WHEN** seed 3 is favoured over seed 6 in the projected first round
- **THEN** the projected semifinal pairs seed 3 with the seed the bracket rules send it to

### Requirement: 2.3.3.1 Pairing frequency
Each projected playoff game SHALL carry how often that pairing occurred across the simulations.

**Traces to:** 2.3.3
**Verified by:** Test: `tests/test_forecast.py::test_pairing_frequency`

#### Scenario: Semifinal share
- **WHEN** the projected semifinal occurred in 41% of runs
- **THEN** the projected game carries 41%

### Requirement: 2.3.3.2 Brackets projected
Only the winners bracket, and the toilet bowl in a league that plays one, SHALL be projected.

**Traces to:** 2.3.3
**Verified by:** Test: `tests/test_forecast.py::test_toilet_bowl_is_projected_and_advances_the_likelier_lower_scorer`

#### Scenario: Consolation league
- **WHEN** a league plays a consolation bracket rather than a toilet bowl
- **THEN** only its winners-bracket games are projected

### Requirement: 2.3.4 Real playoff pairings
Once Sleeper sets a playoff week's pairings, that week's games SHALL be the real ones, forecast like regular-season games, in place of any projected games.

**Traces to:** 2.3
**Verified by:** Test: `tests/test_forecast.py::test_real_pairings_only_after_the_previous_week_is_final`

#### Scenario: Pairings set
- **WHEN** Sleeper has set the week-15 pairings
- **THEN** week 15 shows those real games and no projected ones

### Requirement: 2.4 Forecast log
Each cold run SHALL append, for each game of the current week, an entry holding the run time, each team's model lineup and win probability, and every rostered Player's projected points with whether his NFL game has kicked off.

**Rationale:** Shows how each game's Forecast moved before kickoff, and keeps the projections the Forecast of record needs.
**Traces to:** 2; 6
**Verified by:** Test: `tests/test_games.py::test_weekend_log_freezes_a_player_at_kickoff`

#### Scenario: Weekend runs
- **WHEN** cold runs happen Thursday, Saturday and Sunday morning during week 11 and projections change between each run
- **THEN** each week-11 game has three log entries

### Requirement: 2.4.1 Logged only on change
An entry SHALL be appended only when a lineup, projection, kickoff state or win probability differs from the game's previous entry.

**Traces to:** 2.4
**Verified by:** Test: `tests/test_games.py::test_unchanged_run_adds_no_entry`

#### Scenario: Nothing changed
- **WHEN** a run produces the same lineups, projections, kickoff states and win probabilities as the previous entry
- **THEN** no entry is appended

### Requirement: 2.4.2 Projection frozen at kickoff
A Player's logged projection SHALL stay at its last pre-kickoff value once his game kicks off.

**Traces to:** 2.4
**Verified by:** Test: `tests/test_games.py::test_weekend_log_freezes_a_player_at_kickoff`

#### Scenario: Thursday starter
- **WHEN** a Thursday starter's projection changes on Saturday
- **THEN** the Saturday and Sunday entries keep his Thursday projection

### Requirement: 2.4.3 Current week only
Only the current week's games SHALL be logged.

**Traces to:** 2.4
**Verified by:** Test: `tests/test_store_tiers.py::test_only_the_current_week_is_logged`

#### Scenario: Next week not logged
- **WHEN** a cold run happens during week 11 while week 12's projections change
- **THEN** week 12's games get no log entries

### Requirement: 2.5 Forecast of record
Once a week is final, each game's Forecast of record SHALL be simulated with the same model as the Forecasts, from the lineup each Manager started, each Player at his last logged projection before kickoff.

**Rationale:** Judges each game against what was known at kickoff, not against later news.
**Traces to:** 2; 7
**Verified by:** Test: `tests/test_games.py::test_record_from_log_once_the_week_is_final`

#### Scenario: News before Sunday
- **WHEN** a Sunday starter's projection drops from 14 to 2 on Saturday after he is ruled out, and Thursday starters locked at their Thursday projections
- **THEN** the record uses 2 for the Sunday starter and the Thursday projections for the Thursday starters

#### Scenario: Manager starts an unexpected Player
- **WHEN** a Manager starts a Player the model's lineup never included
- **THEN** the record uses that Player in that slot at his last logged pre-kickoff projection

### Requirement: 2.5.1 Starter never logged
A starter never logged before his kickoff SHALL use his stored projection for that week in the Forecast of record.

**Traces to:** 2.5
**Verified by:** Test: `tests/test_games.py::test_last_unlocked_and_record_lineup`

#### Scenario: Late pickup
- **WHEN** a Manager picks up and starts a Player after the last cold run before his kickoff
- **THEN** the record uses that Player's stored week projection

### Requirement: 2.5.2 Record fields
The Forecast of record SHALL hold the same fields as a game Forecast.

**Traces to:** 2.5; 2.3
**Verified by:** Test: `tests/test_games.py::test_record_from_log_once_the_week_is_final`

#### Scenario: Record shape
- **WHEN** a week's records are stored
- **THEN** each has both teams' means, histograms, win probabilities and lineups

### Requirement: 2.5.3 Weeks before the log
For a finished week with no log entries, the Forecast of record SHALL be the game Forecast from the previous week's as-of Forecast, marked as a pre-week Forecast.

**Traces to:** 2.5
**Verified by:** Test: `tests/test_games.py::test_pre_week_record_for_weeks_before_the_log`

#### Scenario: Early 2026 weeks
- **WHEN** week 6 of 2026 finished before the log existed
- **THEN** its games' record is the as-of-week-5 Forecast, marked as a pre-week Forecast

### Requirement: 2.6 Game files committed
The system SHALL commit, per league, season and week, the log entries and, once the week is final, the Forecast of record with each team's actual score and the winner.

**Traces to:** 2; 6
**Verified by:** Test: `tests/test_store_tiers.py::test_game_file_split_round_trip`

#### Scenario: Final week
- **WHEN** week 10 is final
- **THEN** its committed file holds the log and each game's record, actual scores and winner

### Requirement: 2.6.1 Views rebuilt, not committed
The latest Forecast and the lineup views SHALL be rebuilt by each run and kept out of git.

**Traces to:** 2.6
**Verified by:** Test: `tests/test_storage_tiers.py::test_no_rebuilt_path_is_tracked`

#### Scenario: Fresh clone
- **WHEN** someone clones the repository
- **THEN** it holds no latest-Forecast or lineup-view files, and a build rebuilds them

### Requirement: 2.6.2 Re-runs change nothing
Re-running on unchanged data SHALL leave the committed week files unchanged.

**Traces to:** 2.6
**Verified by:** Test: `tests/test_store_tiers.py::test_unchanged_game_record_is_not_rewritten`; Test: `tests/test_games.py::test_unchanged_run_adds_no_entry`

#### Scenario: Re-run without news
- **WHEN** the games step runs twice with no new projections and no new runs of the simulation
- **THEN** the second run leaves the committed week files unchanged

### Requirement: 2.7 Lineup views
For every finished week and the live week, each game SHALL be stored in two views, Model and Actual, each with its own lineups, means, histogram, win probabilities and margin, simulated with the same model and without results.

**Rationale:** Calculations.txt section 11.
**Traces to:** 2; 2.1.13
**Verified by:** Test: `tests/test_views.py::test_views_for_pre_log_and_logged_weeks`; Test: `tests/test_games_export.py::test_export_lineup_views`

#### Scenario: Same lineup
- **WHEN** a Manager started exactly the model's lineup
- **THEN** both views have the same lineups and probabilities

### Requirement: 2.7.1 Model view
The Model view SHALL hold each team's best legal lineup from its roster that week, every Player at his last projection before kickoff, with the week's replacement-level floor.

**Traces to:** 2.7; 1.1.4
**Verified by:** Test: `tests/test_views.py::test_model_lineup_uses_frozen_projections_and_fills_short_slots`

#### Scenario: Different picks
- **WHEN** a Manager started a receiver projected 6.4 over one projected 6.6
- **THEN** the Model view has the 6.6 receiver in that slot

### Requirement: 2.7.1.1 Model view before the log
For a finished week with no log entries, the Model view SHALL be the pre-week Forecast.

**Traces to:** 2.7.1; 2.5.3
**Verified by:** Test: `tests/test_views.py::test_views_for_pre_log_and_logged_weeks`

#### Scenario: Week 10 of 2026
- **WHEN** week 10 finished before the log existed
- **THEN** its Model view is the as-of-week-9 Forecast

### Requirement: 2.7.2 Actual view
The Actual view SHALL hold the starters each Manager used, at the same projections as the Model view.

**Traces to:** 2.7
**Verified by:** Test: `tests/test_views.py::test_views_for_pre_log_and_logged_weeks`

#### Scenario: Different picks
- **WHEN** a Manager started a receiver projected 6.4 over one projected 6.6
- **THEN** the Actual view has the 6.4 receiver in that slot, with its own win probability

### Requirement: 2.7.2.1 Rebuilt Actual view
For a finished week with no log entries, the Actual view SHALL be simulated from the real starters at their stored projections for that week, marked as rebuilt.

**Traces to:** 2.7.2
**Verified by:** Test: `tests/test_views.py::test_views_for_pre_log_and_logged_weeks`

#### Scenario: Week 10 of 2026
- **WHEN** week 10 finished before the log existed
- **THEN** its Actual view is rebuilt from the starters each Manager used, marked rebuilt

### Requirement: 2.7.3 Live week views
During the live week, the Actual view SHALL be the live Forecast, with locked starters at their results and open slots as the model picks them, while the Model view stays the model lineup at frozen pre-kickoff projections.

**Traces to:** 2.7
**Verified by:** Test: `tests/test_live.py::test_live_forecast_rows_and_log_keep_pre_kickoff_projections`

#### Scenario: Saturday of week 11
- **WHEN** a visitor opens week 11 on Saturday
- **THEN** the Actual view shows the live probabilities and the Model view the model's pre-kickoff Forecast

### Requirement: 2.8 Lineup choices
For each team in a finished or live game, the system SHALL compute lineup choices: the actual starters' points minus the model lineup's points, a replacement fill counting the week's realised replacement level for its position.

**Rationale:** Calculations.txt section 11.
**Traces to:** 2; 2.1.14
**Verified by:** Test: `tests/test_views.py::test_lineup_choices_examples_and_live_rule`

#### Scenario: Better choice
- **WHEN** the Manager's starters scored 104.3 and the model lineup's Players scored 96.9
- **THEN** the team's lineup choices are +7.4

#### Scenario: Benched the better Player
- **WHEN** the model lineup would have scored 12 more points
- **THEN** the team's lineup choices are -12.0

### Requirement: 2.8.1 Lineup choices while live
During the live week, lineup choices SHALL count only Players whose games have kicked off on both sides, with replacement fills counted once the week is final.

**Traces to:** 2.8
**Verified by:** Test: `tests/test_views.py::test_lineup_choices_examples_and_live_rule`

#### Scenario: Sunday afternoon
- **WHEN** a team's model pick plays Sunday night and its actual starter played Thursday
- **THEN** only the Thursday starter counts until the Sunday night game kicks off

### Requirement: 1.2.5 Slate Forecasts
When a slate goes final, the cold run SHALL store the league's season Forecast at that moment in the week's slate file, keyed by the slate's kickoff time.

**Rationale:** Shows how each slate moved the season Forecast.
**Traces to:** 1.2
**Verified by:** Test: `tests/test_store_tiers.py::test_final_slates`; Test: `tests/test_store_tiers.py::test_slate_forecasts_are_stored_once`

#### Scenario: Sunday's slates
- **WHEN** the 1:00 pm, 4:05 pm and Sunday night slates of week 11 go final
- **THEN** week 11's slate file holds three Forecasts, one per slate

### Requirement: 1.2.5.1 Slate Forecast kept
A stored slate Forecast SHALL stay as first stored.

**Traces to:** 1.2.5; 6
**Verified by:** Test: `tests/test_store_tiers.py::test_slate_forecasts_are_stored_once`

#### Scenario: Later run
- **WHEN** a cold run after the 4:05 pm slate goes final runs again
- **THEN** the 1:00 pm slate's stored Forecast is unchanged
