# Tasks

## 1. Terms, Calculations and Shared Helpers

- [x] 1.1 Add **league record** and **game that matters** to `openspec/glossary.md` (game that matters: regular-season games, winners-bracket games on the path to the final, the 3rd place game, and in a toilet-bowl league the losers-bracket games on the path to the toilet bowl final and that final; consolation and placement games excluded). Verify: `tests/test_requirements.py` reports no "used in no spec" finding for either term.
- [x] 1.2 Write a new `Calculations.txt` section, 23. League Records: games that matter, ranking and ties, champions and Best Player by WAR, all-time standings and order, weekly records with margins credited to the winner, season records (regular-season basis, streaks over games that matter, luck as actual minus all-play wins, current-season eligibility, season result), Player records, championship order, and past-season lineup choices with the stored-Projections caveat. Verify: `tests/test_calculations_doc.py` passes.
- [x] 1.3 Add the game classifier (regular season, Playoffs, Championship, 3rd Place, Toilet Bowl, Toilet Bowl Final, not counted) from stored brackets, round to week via `playoff_week_start`. Verify: `tests/test_league_records.py::test_only_games_that_matter_count` covers a 5th place game (not counted), a 3rd place game and a toilet bowl final (counted), and a consolation-bracket league.
- [x] 1.4 Move the Sleeper logo, avatar and headshot helpers from `site/managers.js` into a shared module imported by both pages (with `?v=__BUILD__`). Verify: the Managers layout tests still pass.

## 2. Past-Season Lineup Choices

- [x] 2.1 Compute lineup choices for every finished week of 2021 to 2025 from stored weekly Projections, matchup starters and realised replacement levels, reusing `views.model_lineup` and `views.lineup_choices`; keep 2026's game-log values. Verify: `tests/test_views.py::test_past_season_lineup_choices` on a fixture week (known Projections, starters and expected result).

## 3. League Records Data (`src/ffapp/league_records.py`)

- [x] 3.1 Ranking helper: top 25, competition ranks for equal values, oldest first, record-specific tie-breaks. Verify: `test_ties_share_a_rank_oldest_first`.
- [x] 3.2 Champions: finished seasons only; champion, runner-up, toilet bowl champion or last place; champion's regular-season record and points; that season's Team Name; Best Player by WAR over his weeks on the roster (windows), with NFL team. Verify: `test_champions_list_finished_seasons`.
- [x] 3.3 All-time standings: regular-season record, win %, point differential; playoff appearances and record over winners-bracket games that matter; 1st, 2nd, 3rd and toilet bowl or last counts; current then former, by win %, ties to point differential; vacant rosters credited to the previous Manager. Verify: `test_all_time_standings_example`, `test_standings_order`.
- [x] 3.4 Weekly records: the eight records over games that matter, margins once under the winner, each entry with score, opponent, game kind and current-season flag. Verify: `test_weekly_records_example`.
- [x] 3.5 Season records: the fourteen records with season result; regular-season basis; streaks over games that matter within a season; luck as actual minus all-play wins; bench points; lineup choices gained and lost; current-season eligibility. Verify: `test_season_records_example`, `test_streaks_count_games_that_matter`, `test_luck_example`, `test_current_season_eligibility`.
- [x] 3.6 Player records: best games and career scoring over every Player-week whatever the status; best bench games; championships from title-week rosters with reserve and taxi; ordered by WAR in title seasons; per position and all; NFL team from that week's stats. Verify: `test_player_records_example`, `test_championships_count_the_whole_roster`.
- [x] 3.7 Export `site/data/<league>/records.json` and add it to the site index. Verify: `test_export_writes_league_records`; `python -X utf8 -m ffapp build` writes the file for both leagues.

## 4. League Sub-Tab and Records Page

- [x] 4.1 Add the League sub-tab after Player WAR, with its tab strip (Records) and `#<league>/league/records[/players]` routing, kept across league switches. Verify: `tests/layout/test_league_records_page.py::test_league_tab_opens_on_records`, `test_url_names_the_tab_and_view`; `tests/layout/test_forecasts_page.py` sub-tab tests extended to the sixth sub-tab.
- [x] 4.2 Build `site/league.js` and styles: Managers / Players switch; Champions, All-Time Standings (former Managers group, .700 format), Weekly Records and Season Records tables with tags, season-result pills, the asterisk note and the luck explanation on hover and focus. Verify: `test_view_switch`, `test_managers_view_sections`, `test_champions_table`, `test_standings_table`, `test_record_rows`, `test_luck_explained`.
- [x] 4.3 Players view: four cards, top 5 each, position filter buttons (All, QB, RB, WR, TE, DEF, K) styled as roster badges, Player photos and badges. Verify: `test_players_view`, `test_pictures_with_names`.
- [x] 4.4 Record pop-up: `<dialog>` with the top 25, gold, silver and bronze ranks, and focus return; a bottom sheet with a 48 px close button below 600 px; the luck explanation at the top of the luck pop-ups. Verify: `test_record_popup`.
- [x] 4.5 Phone layout: tables become lists with no score lines and no sideways scroll at 360, 390, 414 and 440 px. Verify: `test_phone_lists` and the layout check.
- [x] 4.6 Colours: tag, medal and pill tokens from existing hues (new bronze and silver derived in OKLCH), in both modes. Verify: `tests/test_colour_contrast.py`.
- [x] 4.7 Register every new control in `tests/layout/controls.py` (League sub-tab, League tab, view switch, position filters, Top 25 buttons, pop-up close) and give all new text copy IDs, then run `python -m ffapp site-copy`. Verify: `tests/layout/test_layout.py` and the site-copy tests pass (ask the owner before any `--apply`).

## 5. Docs, Requirements and Checks

- [x] 5.1 Write `docs/league-records.md` (Code, Runs, Tests; Diagram; sources, storage, calculations, where it shows; Keeping This Document Current) and `tools/league_records_diagram.py`, and register them in `tests/test_feature_docs.py` for `src/ffapp/league_records.py` and `site/league.js`. Verify: `tests/test_feature_docs.py` passes.
- [x] 5.2 Update `docs/requirements.md` for the glossary and checklist changes, and redraw its diagrams with `python -X utf8 tools/requirements_diagram.py`. Verify: `tests/test_feature_docs.py` passes.
- [x] 5.3 Re-inspect 9.1.1 and its directly linked requirements with inspection rows (per the impact report: 9.1 and the sub-tab pages), and add inspection-checklist rows for any new Inspection-verified requirement. Verify: `tests/test_requirements.py` reports no stale or missing inspection.
- [ ] 5.4 Redo the standard reviews for `league-odds-site` and `game-predictions`, and add reviews for `league-records` and `league-records-page` once synced. Verify: `tests/test_requirements.py::test_findings_match_the_baseline` passes.
- [x] 5.5 Run the full suite with the layout check and both modes. Verify: `python -X utf8 -m pytest` passes.

## Workflow follow-up

- Commit the proposal with the first apply work, since the requirements check reports the new tests as missing until they exist.
- After this change: review the lineup-choices feature (owner request).
- Next League tabs: Strength of Schedule, then History with draft data, then Trades.
