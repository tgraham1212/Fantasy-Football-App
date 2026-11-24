# games-page Specification

## Purpose

The Games sub-tab of each league page: this season's matchups week by week, with each game's Forecast, the Players it counts on and who is sitting out, the scores and win probability added once games are played, and how the result compared with the Forecast. It delivers need 2, Game Forecasts. Card states (F1 to PW) are defined in `game-card-states` and `docs/games-page-states.md`.

## Requirements

### Requirement: 2.1 Games sub-tab
The Games sub-tab SHALL show the current season's matchups one week at a time, one card per game.

**Traces to:** 2; 9.1.1
**Verified by:** Test: `tests/test_games_export.py::test_export_writes_games_index_and_weeks`

#### Scenario: Week 11
- **WHEN** a visitor opens the Games sub-tab during week 11
- **THEN** each of week 11's games has its own card

### Requirement: 2.1.1 Opens on the current week
The Games sub-tab SHALL open on the current NFL week.

**Traces to:** 2.1
**Verified by:** Test: `tests/layout/test_games_page.py::test_opens_on_the_current_week`

#### Scenario: Default week
- **WHEN** a visitor opens the Games sub-tab on a Saturday during week 11
- **THEN** week 11 is shown and selected in the week control

### Requirement: 2.1.1.1 Week list
The week control SHALL list every regular-season and playoff week of the current season, in order.

**Traces to:** 2.1.1
**Verified by:** Test: `tests/layout/test_games_page.py::test_week_list_covers_every_week_of_the_season`

#### Scenario: Whole season
- **WHEN** a visitor opens the week control
- **THEN** it lists weeks 1 to 14 and the three playoff rounds

### Requirement: 2.1.1.2 Week arrows
Previous and next arrows SHALL step one week, each disabled at its end of the season.

**Traces to:** 2.1.1
**Verified by:** Test: `tests/layout/test_games_page.py::test_arrows_step_one_week_and_stop_at_the_ends`

#### Scenario: Step back
- **WHEN** the visitor clicks the previous arrow on week 11
- **THEN** week 10 is shown

#### Scenario: First week
- **WHEN** week 1 is shown
- **THEN** the previous arrow is disabled

### Requirement: 2.1.2 Card columns
Game cards SHALL sit in two columns from 900 px wide and in one column below it, with a lone last card centred.

**Traces to:** 2.1; 9.2
**Verified by:** Test: `tests/layout/test_layout.py::test_games_cards_stack_and_team_rows_do_not_overlap_on_large_phones`; Inspection: the live site at 1280 px, two columns and a centred lone card

#### Scenario: Tablet width
- **WHEN** the page is shown at 768 px during a live week
- **THEN** cards stack in one column and no lineup's points, win probability added or game clock overlap

### Requirement: 2.1.3 Team rows
Each card SHALL stack its two team rows, each showing the Manager's colour dot, the Manager's display name with the Team Name beneath, a score block and the win probability.

**Rationale:** The colour dot is the team's colour on the Forecasts sub-tab.
**Traces to:** 2.1; 1.4.3
**Verified by:** Inspection: the live site, team rows of a week-11 card

#### Scenario: Card contents
- **WHEN** week 11's card for two teams is shown
- **THEN** each team row has its colour dot, Manager and Team Name, score block and win probability

### Requirement: 2.1.3.1 Forecast score
Before a game starts, each score block SHALL show the team's mean simulated points labelled "forecast".

**Traces to:** 2.1.3
**Verified by:** Inspection: the live site, score blocks of an upcoming week

#### Scenario: Upcoming game
- **WHEN** a team's mean simulated points are 113.4 for an unplayed game
- **THEN** its score block shows "113.4" labelled "forecast"

### Requirement: 2.1.3.2 Played score
Once a game is live or finished, each score block SHALL show the current or final score as the large number, with the Forecast beneath in smaller type labelled "forecasted".

**Traces to:** 2.1.3
**Verified by:** Test: `tests/layout/test_layout.py::test_finished_cards_show_the_actual_score_first`

#### Scenario: Finished game score
- **WHEN** a finished game's team scored 183.5 against a Forecast of 113.4
- **THEN** its score block shows 183.5 large and "113.4 forecasted" beneath it

### Requirement: 2.1.3.3 Score distributions
Each card SHALL overlay both teams' simulated score distributions in one chart, each shaded in its Manager's colour.

**Traces to:** 2.1.3
**Verified by:** Inspection: the live site, the chart of a week-11 card

#### Scenario: Two distributions
- **WHEN** a card is shown
- **THEN** its chart shows both teams' distributions in their two colours

### Requirement: 2.1.3.4 Cards on a phone
Below 600 px wide, each card SHALL place its chart beneath the team rows, which take the card's full width.

**Traces to:** 2.1.3; 9.2
**Verified by:** Test: `tests/layout/test_layout.py::test_games_cards_stack_and_team_rows_do_not_overlap_on_large_phones`

#### Scenario: Large phone
- **WHEN** the page is shown at 440 px
- **THEN** each card's team rows span the card with the chart beneath, and no Manager name is cut short while the card has room for it

### Requirement: 2.1.3.5 Win probability box on a phone
Below 600 px wide, the win probability box SHALL be narrower than at 600 px and above.

**Traces to:** 2.1.3; 9.2
**Verified by:** Inspection: the live site at 360 and 1280 px, the win probability box widths

#### Scenario: Phone card
- **WHEN** a card is shown at 360 px
- **THEN** its win probability boxes are narrower than at 1280 px

### Requirement: 2.1.4 Win probability fill
Each win probability box SHALL be filled on a diverging scale: neutral grey at 50%, a stronger green toward 100% and a stronger red toward 0%.

**Traces to:** 2.1; 2.1.3
**Verified by:** Inspection: the live site in both themes, boxes at 8%, 50% and 92%

#### Scenario: Heavy favourite
- **WHEN** a team's win probability is 92%
- **THEN** its box is a strong green and the other team's 8% box a strong red

#### Scenario: Toss-up
- **WHEN** both teams are near 50%
- **THEN** both boxes are close to the neutral grey

### Requirement: 2.1.4.1 Readable win probability
Text on every step of the win probability scale SHALL have at least 4.5:1 contrast with its fill in both themes.

**Traces to:** 2.1.4; 9
**Verified by:** Test: `tests/test_colour_contrast.py::test_colour_tokens_meet_contrast`

#### Scenario: Dark theme
- **WHEN** a card is shown in the dark theme
- **THEN** every win probability stays readable against its fill

### Requirement: 2.1.5 Key players
In states F1, F2, C and P2, each team SHALL list four key players from the lineup shown: the quarterback, the highest-projected running back, the highest-projected wide receiver, and the highest-projected remaining running back, wide receiver or tight end.

**Traces to:** 2.1; 2.10
**Verified by:** Test: `tests/test_games_export.py::test_key_players_rule`; Test: `tests/layout/test_game_states.py::test_every_state_looks_as_decided`

#### Scenario: Key four
- **WHEN** a team's model lineup has running backs projected 18 and 11, wide receivers 16 and 13, and a tight end at 9
- **THEN** its key players are the quarterback, the 18-point running back, the 16-point receiver and the 13-point receiver

### Requirement: 2.1.5.1 Full Lineup control
Where a card lists key players, a "Full Lineup" control SHALL show every lineup slot with its Player and projected points, a replacement fill reading as a free agent at replacement level.

**Traces to:** 2.1.5
**Verified by:** Test: `tests/layout/test_game_states.py::test_every_state_looks_as_decided`; Test: `tests/test_forecast.py::test_replacement_fill_is_marked`

#### Scenario: Full lineup
- **WHEN** the visitor expands a team's lineup
- **THEN** every slot is listed with its Player and projected points, and a replacement fill reads as a free agent

### Requirement: 2.1.5.1.1 Linked full lineups
Opening or closing one team's Full Lineup SHALL open or close both teams' full lineups in that card.

**Traces to:** 2.1.5.1
**Verified by:** Test: `tests/layout/test_games_page.py::test_full_lineup_opens_both_teams_together`

#### Scenario: Expand one side
- **WHEN** a visitor expands one team's Full Lineup
- **THEN** the opponent's full lineup opens too

### Requirement: 2.1.6 Not playing
Below each card, each team SHALL list its rostered Players expected not to play that week: on a bye, with a status on the shared out-status list, or inferred out in a week without saved statuses.

**Traces to:** 2.1
**Verified by:** Test: `tests/test_injuries.py::test_saved_statuses_and_bye_take_precedence`; Test: `tests/test_injuries.py::test_inferred_out_for_weeks_without_saved_statuses`

#### Scenario: Injured starter
- **WHEN** a team's receiver is Out for week 11
- **THEN** he is listed under that team

### Requirement: 2.1.6.1 Reason shown
Each Player listed as not playing SHALL carry the reason, in the shared status labels, just after the name.

**Traces to:** 2.1.6
**Verified by:** Test: `tests/test_injuries.py::test_shared_out_statuses_and_labels`

#### Scenario: Physically unable to perform
- **WHEN** a team's running back has a saved status of PUP for week 11
- **THEN** he is listed as "PUP"

### Requirement: 2.1.7 Winner check
For a finished week (PW), and for a game whose starters have all finished (O1 to O3), each card SHALL show a check mark in the winner's win probability box.

**Traces to:** 2.1; 2.10
**Verified by:** Test: `tests/layout/test_game_states.py::test_every_state_looks_as_decided`

#### Scenario: Unofficial winner
- **WHEN** every Player in a game has finished on Monday night but Sleeper has not scored the week
- **THEN** the card shows a check on the leading team beside the Unofficial chip

### Requirement: 2.1.7.1 Actual score on the chart
For a finished week or a game whose starters have all finished, each card SHALL draw each team's actual score as a vertical line on its distribution, in the team's colour.

**Traces to:** 2.1.7; 2.1.3.3
**Verified by:** Inspection: the live site, week 10's charts

#### Scenario: Week 10 look-back
- **WHEN** a visitor selects week 10 after it is final
- **THEN** both actual scores show as lines on each chart

### Requirement: 2.1.7.2 Pre-week Forecast labelled
A card showing a pre-week Forecast, for a week before the Forecast log existed, SHALL label it as pre-week.

**Traces to:** 2.1.7
**Verified by:** Test: `tests/test_views.py::test_views_for_pre_log_and_logged_weeks`

#### Scenario: Early week
- **WHEN** a visitor opens a week finished before the log began
- **THEN** each card's Forecast is labelled as a pre-week Forecast

### Requirement: 2.1.8 Projected bracket
Until Sleeper sets a playoff week's real pairings, that week SHALL show the projected bracket, with the 1 seed's side at the top and the 2 seed's side at the bottom.

**Traces to:** 2.1; 1.1.8
**Verified by:** Test: `tests/test_forecast.py::test_projected_bracket_seeds_by_expectation_and_favourite_advances`; Test: `tests/test_forecast.py::test_real_pairings_only_after_the_previous_week_is_final`

#### Scenario: Projected first round
- **WHEN** a visitor selects week 15 before pairings are set
- **THEN** the 4 v 5 game appears above the 3 v 6 game

### Requirement: 2.1.8.1 Pairing frequency
Each projected playoff card SHALL show how often that pairing happened in the simulations.

**Traces to:** 2.1.8
**Verified by:** Test: `tests/test_forecast.py::test_pairing_frequency`

#### Scenario: Likely pairing
- **WHEN** seeds 4 and 5 met in round 1 in 62% of runs
- **THEN** their projected card says 62%

### Requirement: 2.1.8.2 Bye cards
A projected first round SHALL show a bye card for each team with a first-round bye.

**Traces to:** 2.1.8
**Verified by:** Inspection: the live site, week 15 before pairings are set

#### Scenario: Seeds 1 and 2
- **WHEN** week 15 is projected
- **THEN** bye cards show for seeds 1 and 2

### Requirement: 2.1.8.3 Toilet bowl
In a league that plays a toilet bowl, the projected toilet bowl games SHALL show below the winners bracket.

**Traces to:** 2.1.8
**Verified by:** Test: `tests/test_forecast.py::test_toilet_bowl_is_projected_and_advances_the_likelier_lower_scorer`

#### Scenario: Redraft week 15
- **WHEN** a visitor opens redraft week 15 before pairings are set
- **THEN** the toilet bowl games show below the winners bracket

### Requirement: 2.1.9 LIVE badge
During the live week, a card SHALL show the "LIVE" badge and border, a signal icon with green arcs and a moving gradient, only in state L1.

**Traces to:** 2.1; 2.10
**Verified by:** Test: `tests/layout/test_game_states.py::test_every_state_looks_as_decided`

#### Scenario: Starter in progress
- **WHEN** one team in a game has a starter in the 3rd quarter of Thursday's game
- **THEN** that card shows the LIVE badge and border, and cards with no starter in that game do not

#### Scenario: Only the bench is playing
- **WHEN** a card is in L2 because only a bench Player is playing
- **THEN** it shows no LIVE badge

### Requirement: 2.1.9.1 Still badge for reduced motion
When the visitor's system asks for reduced motion, the LIVE badge SHALL show without animation.

**Traces to:** 2.1.9; 9
**Verified by:** Inspection: the live site with reduced motion turned on

#### Scenario: Reduced motion
- **WHEN** the visitor's system asks for reduced motion
- **THEN** the badge shows without animation

### Requirement: 2.1.10 Points so far
Once either team in a game has a starter whose game has kicked off, both teams SHALL show their points so far as the large number (0.0 when none), the projected final beneath labelled "forecasted", and how many starters have not kicked off.

**Traces to:** 2.1; 2.1.3.2
**Verified by:** Inspection: the live site on a Saturday of a live week

#### Scenario: Only one team has started
- **WHEN** one team has 14.2 points from Thursday and the other has no starter who has played
- **THEN** the other team shows 0.0 large, its forecasted final beneath and its count of starters to play, laid out the same as the first team

### Requirement: 2.1.11 Player game status
In every lineup on a live or finished week, each starter SHALL show his game status: in progress in green with a dot and the game clock, final in bold dark text, or not yet started in grey with the kickoff time.

**Traces to:** 2.1
**Verified by:** Test: `tests/layout/test_layout.py::test_lineup_columns_never_overlap`; Inspection: the live site, a live week's lineups

#### Scenario: Mixed slate
- **WHEN** a team has a Thursday starter (final), one in the 3rd quarter and one playing Sunday night
- **THEN** they show final in bold, "Q3 4:12" in green and the Sunday night kickoff time in grey

### Requirement: 2.1.11.1 Final tag
A starter whose game is final SHALL carry an "F" tag on the live week only.

**Traces to:** 2.1.11
**Verified by:** Inspection: the live site, a live week and finished week 9

#### Scenario: Past week
- **WHEN** a visitor opens finished week 9
- **THEN** every starter's points are bold with no "F" tag

### Requirement: 2.1.12 Win probability added shown
In the Actual view of a live or finished week, every starter with an actual score SHALL show his win probability added beside his points, green when positive and red when negative.

**Rationale:** Calculations.txt section 13.
**Traces to:** 2.1; 2.1.11
**Verified by:** Test: `tests/test_wpa.py::test_live_wpa_uses_the_pre_kickoff_baseline_and_skips_players_not_started`; Inspection: the live site, week 9's colours

#### Scenario: Past week
- **WHEN** a visitor opens finished week 9
- **THEN** each starter shows his win probability added, a +22 in green and a -9 in red

#### Scenario: Not kicked off
- **WHEN** a starter's game has not started
- **THEN** no win probability added is shown for him

### Requirement: 2.1.12.1 Win probability added note
The Games sub-tab SHALL note that win probability added shows the size of each swing and does not add up to the team's change.

**Traces to:** 2.1.12; 8
**Verified by:** Inspection: the live site, the note on the Games sub-tab

#### Scenario: Reading the values
- **WHEN** a visitor reads a finished week
- **THEN** the note explains that the values do not sum to the team's change

### Requirement: 2.1.13 Model and Actual views
Cards in states P2, L1, L2, P1, O1, O2, O3 and PW SHALL offer a "Model | Actual" toggle that switches the card's lineups, key players, means, win probabilities and chart between the two stored views.

**Traces to:** 2.1; 2.10
**Verified by:** Test: `tests/layout/test_game_states.py::test_every_state_looks_as_decided`; Test: `tests/layout/test_game_states.py::test_finished_states_show_the_full_lineup_in_the_model_view`

#### Scenario: Switch to Model
- **WHEN** the visitor clicks "Model" on a card
- **THEN** that card shows the model's lineups, probabilities and chart

### Requirement: 2.1.13.1 Opens on Actual
A card with the toggle SHALL open on the Actual view.

**Traces to:** 2.1.13
**Verified by:** Inspection: the live site, the toggle on finished week 10

#### Scenario: Look-back on Actual
- **WHEN** a visitor opens finished week 10
- **THEN** each card's Actual button is selected

### Requirement: 2.1.13.2 Actual scores in both views
Actual scores SHALL be drawn on the chart in both views.

**Traces to:** 2.1.13; 2.1.7.1
**Verified by:** Inspection: the live site, week 10 in both views

#### Scenario: Model view of a finished game
- **WHEN** the visitor switches a finished card to Model
- **THEN** the actual-score lines stay on the chart

### Requirement: 2.1.13.3 Model view only before play
Cards in states F1, F2 and C SHALL show the model view without a toggle.

**Traces to:** 2.1.13; 2.10
**Verified by:** Test: `tests/layout/test_game_states.py::test_every_state_looks_as_decided`

#### Scenario: Upcoming week
- **WHEN** a visitor opens week 13 before it starts
- **THEN** the cards show the model view and no toggle

#### Scenario: Untouched card in the live week
- **WHEN** some NFL games of the current week have started but no Player in a card has kicked off (state C)
- **THEN** that card shows no toggle

### Requirement: 2.1.13.4 Rebuilt view labelled
An Actual view rebuilt for a week before the Forecast log existed SHALL be labelled as rebuilt.

**Traces to:** 2.1.13
**Verified by:** Test: `tests/test_games_export.py::test_export_logged_week_views`

#### Scenario: Rebuilt lineups
- **WHEN** a visitor opens a week finished before the log began
- **THEN** its Actual view is labelled rebuilt

### Requirement: 2.1.14 Lineup choices shown
On live and finished cards, in both views, each team SHALL show "Lineup choices: +N" or "-N" beneath the forecasted line of its score block: its points against the model lineup, explained on hover, green when positive and red when negative.

**Rationale:** Calculations.txt section 11.
**Traces to:** 2.1; 2.1.3.2
**Verified by:** Test: `tests/test_views.py::test_lineup_choices_examples_and_live_rule`

#### Scenario: Positive choices
- **WHEN** a team's lineup choices are +7.4
- **THEN** "Lineup choices: +7.4" shows in green beneath its forecasted line, never over the scores, and hovering explains that it is points against the model lineup

### Requirement: 2.1.15 Bench tag
In the model view of a live or finished card, each model pick the Manager did not start SHALL carry a "BN" tag.

**Traces to:** 2.1; 2.1.13
**Verified by:** Inspection: the live site, the Model view of week 10

#### Scenario: Benched pick
- **WHEN** the model view lists Xavier Worthy, whom the Manager benched
- **THEN** his row shows "BN" and his points

### Requirement: 2.1.15.1 No win probability added in the model view
The model view SHALL show win probability added for no Player.

**Rationale:** Win probability added exists only for the Managers' real starters.
**Traces to:** 2.1.15; 2.1.12
**Verified by:** Inspection: the live site, the Model view of week 10

#### Scenario: Benched pick
- **WHEN** the model view lists a Player the Manager benched
- **THEN** his row shows no win probability added

### Requirement: 2.1.16 Player rows
Each Player row SHALL show, in order, the slot or position, the name with any final tag, the points or projection, the win probability added for scored starters in the Actual view, and a right-hand column for the game clock or kickoff time.

**Traces to:** 2.1
**Verified by:** Test: `tests/layout/test_layout.py::test_lineup_columns_never_overlap`

#### Scenario: Upcoming player
- **WHEN** a Player's game is on Sunday at 1:00
- **THEN** "Sun 1:00" shows in the right-hand column

### Requirement: 2.1.16.1 Empty right-hand column
The right-hand column SHALL take no width in a card with nothing to put in it.

**Traces to:** 2.1.16
**Verified by:** Test: `tests/layout/test_layout.py::test_lineup_columns_never_overlap`

#### Scenario: Finished week
- **WHEN** every game in a card is final
- **THEN** the right-hand column takes no width

### Requirement: 2.1.16.2 Aligned points
Within each team's list, the points or projections SHALL form one aligned column just after the longest name.

**Traces to:** 2.1.16
**Verified by:** Inspection: the live site at 1280 px, the points column of each list

#### Scenario: Projections line up
- **WHEN** a list is shown
- **THEN** its projections line up just after its longest name, not at the card's far edge

### Requirement: 2.1.16.3 Lists on a phone
Below 560 px wide, the two teams' lists SHALL stack, each under its Team Name, with every name in full or as first initial and last name, never cut.

**Traces to:** 2.1.16; 9.2
**Verified by:** Test: `tests/layout/test_layout.py::test_phone_lineups_show_full_names`

#### Scenario: Phone
- **WHEN** a visitor opens a card on a 360 px phone
- **THEN** the first team's lineup shows above the second's and no name is cut

### Requirement: 2.1.16.3.1 Free agent on a phone
Below 560 px wide, a replacement fill SHALL read "Free agent" on one line.

**Traces to:** 2.1.16.3
**Verified by:** Inspection: the live site at 360 px, a lineup with a replacement fill

#### Scenario: Free agent on a phone
- **WHEN** a lineup has a replacement fill on a 360 px phone
- **THEN** the row reads "Free agent" and fits on one line

### Requirement: 2.1.17 Full lineups while games are on
In states L1, L2 and P1, in both views, each team SHALL show its full lineup in place of the key players, with no Full Lineup control.

**Rationale:** Every starter's clock, final tag and points stay visible.
**Traces to:** 2.1; 2.1.5; 2.10
**Verified by:** Test: `tests/layout/test_game_states.py::test_every_state_looks_as_decided`

#### Scenario: Playing starter at FLEX
- **WHEN** a team's only playing starter is its FLEX in the 1st quarter
- **THEN** his row and green clock show without expanding anything

### Requirement: 2.1.18 Impact-ranked key players
In the Actual view of states O1, O2, O3 and PW, each team's key players SHALL be its four starters with the largest win probability added in either direction, largest first.

**Traces to:** 2.1; 2.1.5; 2.1.12
**Verified by:** Test: `tests/layout/test_game_states.py::test_finished_states_rank_key_players_by_impact`

#### Scenario: Biggest swings first
- **WHEN** a team's starters have win probability added of +31%, +23%, −15% and +13%
- **THEN** its key players are listed in that order

### Requirement: 2.1.18.1 Ties broken by position
Starters tied on the whole percentage shown SHALL be ranked by position: QB, RB, WR, TE, DEF, K.

**Traces to:** 2.1.18
**Verified by:** Test: `tests/test_card_states.py::test_impact_ranking_and_ties`

#### Scenario: Ranking with a tie
- **WHEN** a quarterback and a receiver both added +13%
- **THEN** the quarterback is listed first

### Requirement: 2.1.18.2 Full lineup in the model view
The Model view of states O1, O2, O3 and PW SHALL show each team's full lineup.

**Rationale:** Win probability added exists only for the Managers' real starters.
**Traces to:** 2.1.18; 2.10
**Verified by:** Test: `tests/layout/test_game_states.py::test_finished_states_show_the_full_lineup_in_the_model_view`

#### Scenario: Model view of a final game
- **WHEN** the visitor switches a PW card to Model
- **THEN** both teams' full lineups show

### Requirement: 2.1.19 Card chips
Each card header SHALL show these chips by state, and none in PW:
- a grey "Bench playing" chip with a dot in L2 and O2;
- a "Bench to play" chip in O1;
- an "Unofficial" chip in O1, O2 and O3.

**Traces to:** 2.1; 2.10
**Verified by:** Test: `tests/layout/test_game_states.py::test_every_state_looks_as_decided`

#### Scenario: Starters done, bench playing
- **WHEN** a card is in O2
- **THEN** its header shows the Unofficial and Bench playing chips, and no LIVE badge

### Requirement: 2.1.19.1 Unofficial explained
Hovering over the Unofficial chip SHALL explain that Sleeper has not yet scored the week.

**Traces to:** 2.1.19
**Verified by:** Inspection: the live site, the Unofficial chip's tooltip

#### Scenario: Hover the chip
- **WHEN** a visitor hovers over an Unofficial chip
- **THEN** the tooltip says the week is not yet scored by Sleeper

### Requirement: 2.2 Games data exported
Each league's site data SHALL include, for every week of the current season, each card's data: teams, Managers, mean points, win probabilities, histograms, lineups, key players, not-playing lists and the Forecast's run time, plus the record, actual scores and winner for finished weeks.

**Traces to:** 2; 2.1
**Verified by:** Test: `tests/test_games_export.py::test_export_writes_games_index_and_weeks`; Test: `tests/test_games_export.py::test_export_lineup_views`

#### Scenario: Week files
- **WHEN** the export runs
- **THEN** each week of the season has its own file with every card's data

### Requirement: 2.2.1 One week at a time
The Games sub-tab SHALL load only the week file it shows.

**Rationale:** A season of cards is too large to load at once on a phone.
**Traces to:** 2.2; 9
**Verified by:** Inspection: the browser's network log on the live site, one week file per week shown

#### Scenario: Step a week
- **WHEN** the visitor steps from week 11 to week 10
- **THEN** only week 10's file is fetched

### Requirement: 2.2.2 Export without games
The export SHALL succeed without game data, leaving the Games sub-tab to say that games are not yet available.

**Traces to:** 2.2
**Verified by:** Test: `tests/test_games_export.py::test_export_without_game_files_has_no_games_entry`

#### Scenario: No games yet
- **WHEN** the export runs on a store without game data
- **THEN** the site builds and the Games sub-tab says games are not yet available
