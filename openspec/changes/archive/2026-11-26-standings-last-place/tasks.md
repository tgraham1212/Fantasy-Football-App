# Tasks

## 1. Final Places (`src/ffapp/managers.py`)

- [x] 1.1 In `bracket_places`, for a league without a toilet bowl, stop reading the losers bracket. Place the rosters the winners bracket did not place in `regular_season_order` after the playoff teams. Keep returning `{}` until the winners bracket is placed. Verify: replace `tests/test_managers.py::test_consolation_winner_is_seventh` with `test_consolation_bracket_is_ignored` (a 2-12 consolation winner finishes 12th; two 5-9 teams ordered by points for; places 1 to 6 unchanged). `test_incomplete_brackets_give_no_places` and `test_toilet_bowl_winner_is_last_place` still pass.
- [x] 1.2 Check the stored seasons. Verify: a scratch check shows dynasty 2023 last place DeekBurg (2-12) and every dynasty season's 12th place is the team last in the standings, while redraft places are unchanged from today's `records.json`.

## 2. League Records (`src/ffapp/league_records.py`)

- [x] 2.1 Confirm Champions Last Place, the season result "Last" and the All-Time Standings last-place count follow the new places with no logic change. Verify: a `tests/test_league_records.py` case where a consolation league's 2-12 team that won its consolation games is the season's last place, with result "Last", and is counted in its Manager's last-place finishes.
- [x] 2.2 Rename "games that matter" to Meaningful Games in the module docstring and section comment, and rename the tests to `test_only_meaningful_games_count` and `test_streaks_count_meaningful_games` (docstrings too). Verify: `tests/test_league_records.py` passes.

## 3. Glossary, Calculations and Docs

- [x] 3.1 Rename the glossary entry "Games that matter" to "Meaningful Games" with the owner's wording (regular season; winners-bracket games on the path to the championship; the championship; the 3rd place game; in a toilet-bowl league the toilet bowl games on its path and its final; every other placement game ignored).
- [x] 3.2 `Calculations.txt`: in section 19, change the final place line (consolation bracket ignored; teams outside the playoffs in standings order) and add the assumption. In section 23, rename to Meaningful Games and say last place is last in the standings without a toilet bowl. Verify: `tests/test_calculations_doc.py` passes.
- [x] 3.3 `docs/league-records.md`: rename step 1 to Meaningful Games and update the final-places note; rename the "Games That Matter" box in `tools/league_records_diagram.py` and redraw. Verify: `tests/test_feature_docs.py` passes.

## 4. Player Games From This Season (`site/league.js`)

- [x] 4.1 Keep the phone top 25 "This season" chip already in the working tree, and `tests/layout/test_league_records_page.py::test_player_games_this_season`. Verify: the test passes at 1280 and 360 px in both leagues and fails without the fix (confirmed before this change).

## 5. Live Actual View (`src/ffapp/views.py`, `src/ffapp/live.py`)

- [x] 5.1 Build the live Actual view from the set starters: `live_lineup` with an `open_lineup` that returns the Manager's starters for the open slots at their latest Projections (empty slot 0, no floor). Simulate one week with the section 12 live scoring rule, the record's noise and one week of drift. Copy `wpa` and `points_so_far` from the live Forecast's team and count `to_play` on the Actual lineup. Verify: new `tests/test_views.py::test_live_actual_view_uses_set_starters`. A starter projected below the replacement level stays in his slot with no free agent. A benched higher-projected receiver is not in the Actual view, and the Model view marks him benched. Locked starters keep their results.
- [x] 5.2 Update `tests/test_live.py::test_live_forecast_rows_and_log_keep_pre_kickoff_projections`: the Actual view is still `live`, and its unlocked rows are the matchup's starters. Verify: the test passes.
- [x] 5.3 `Calculations.txt`: section 11 (the live Actual view: set starters, latest Projections, no fills) and sections 12 and 13 (the live Forecast keeps the model's picks; WPA measured on the Forecast). Also update the live Actual view mention in `docs/simulation.md`. Verify: `tests/test_calculations_doc.py` and `tests/test_feature_docs.py` pass.
- [x] 5.4 Check week 12 locally (`python -X utf8 -m ffapp build` with the current live data). Verify: tg1212's Actual view lists Cam Ward, Blake Corum, Kyren Williams, Josh Downs, Stefon Diggs, Chig Okonkwo, Derrick Henry and Houston Texans, with no free agent.

## 6. Verification and Review

- [x] 6.1 Rebuild (`python -X utf8 -m ffapp build`) and check the site. Verify: on the dynasty League tab, Worst Record shows DeekBurg 2023 with "Last", the 2023 Champions row lists DeekBurg as Last Place, and the Managers tab shows DeekBurg 12th in 2023.
- [x] 6.2 Run `tools/requirements_impact.py` for 2.7.3, 4.5.2, 4.5.2.1, 4.5.2.2, 4.8.1, 4.8.3, 4.8.4.1, 4.8.6.2, 4.8.6.5 and 4.9.2.2.2. Re-inspect the linked inspection-verified 4.5 and 4.5.3, recording only with the owner's approval. Redraw `tools/requirements_diagram.py`. Verify: `tests/test_requirements.py` passes apart from findings resolved at archive.
- [x] 6.3 Full suite. Verify: `python -X utf8 -m pytest` passes, including the layout check.

## Workflow follow-up

- Commit, push and archive with spec sync when the owner asks. Redo the standard reviews of `game-predictions`, `manager-history`, `league-records` and `league-records-page` at archive.
