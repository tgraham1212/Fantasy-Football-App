# Tasks

## 1. Upcoming Pairings in the Forecast

- [x] 1.1 In `src/ffapp/simulate.py`, compute for each unscored regular-season week every team's mean simulated score and the n x n win share (ties as half) from `weekly_scores`, and carry it into the Forecast payload as `upcoming` via `src/ffapp/odds.py` (live and as-of results alike), rounded to 3 decimals; verify with `tests/test_simulate.py::test_upcoming_pairings` (pairs that do not meet are present, each pair's shares sum to 1 within 0.001, means match the per-game means) (1.1.9.3)
- [x] 1.2 Update `docs/simulation.md` (outputs, and Keeping This Document Current if needed) and redraw `python -X utf8 tools/simulation_diagram.py`; verify with `pytest tests/test_feature_docs.py`

## 2. Strength of Schedule Figures and Export

- [x] 2.1 Create `src/ffapp/schedule_strength.py`: regular-season weeks only, played weeks from stored matchups, upcoming weeks from the latest live or as-of Forecast's `upcoming` block, and a current season with no Forecast left out; verify with `test_regular_season_only` and `test_upcoming_weeks_use_the_forecast` in `tests/test_schedule_strength.py` (4.10.1, 4.10.3)
- [x] 2.2 Weekly Ranks: weekly rank = 1 + number of teams that scored more, opponent-rank means over played, upcoming and season to 0.01, order by season mean (lowest first, equal means share a rank); verify with `test_weekly_rank_ties_share_the_better_rank`, `test_opponent_rank_averages` and `test_weekly_ranks_order` (4.10.2, 4.10.2.1, 4.10.2.2)
- [x] 2.3 Schedule Swap: the N x N wins with substitution when the schedule's Manager meets this Manager, played games 1 / 0.5 / 0, upcoming games at the pair's win share, Index = mean over all N schedules minus own wins to 0.01, order by Index (highest first), lowest and highest wins; verify with `test_swap_substitutes_the_schedule_manager`, `test_played_week_wins`, `test_upcoming_week_wins_use_pair_probabilities`, `test_difficulty_index` and `test_swap_order_and_range` (4.10.4 to 4.10.4.4)
- [x] 2.4 Wire `site/data/<league>/schedule.json` into `src/ffapp/export.py` beside `records.json` (index entry `schedule`, managers with pictures keyed by user ID); verify with `test_export_writes_schedule_file` and by running `python -m ffapp build` and finding the file for both leagues with every stored season (4.10)
- [x] 2.5 Add Calculations.txt section 24 "Strength of Schedule" (weekly rank, opponent-rank means, swap with substitution, win shares for upcoming weeks, Index, range) and the glossary terms Strength of Schedule, Weekly Ranks, Schedule Swap and Schedule Difficulty Index to `openspec/glossary.md`; verify with `pytest tests/test_requirements.py tests/test_calculations_doc.py` (glossary terms in use are defined)
- [x] 2.6 Write `docs/strength-of-schedule.md` (Code, Runs, Tests; Diagram; sources, storage, calculations, where it shows; Keeping This Document Current) and `tools/strength_of_schedule_diagram.py`, and register both in `tests/test_feature_docs.py` for `src/ffapp/schedule_strength.py` and `site/schedule.js`; verify with `pytest tests/test_feature_docs.py`

## 3. Strength of Schedule Tab

- [x] 3.1 Add the second `#lg-tabs` button "Strength of Schedule" in `site/index.html`, routing in `site/league.js` (`#<league>/league/schedule[/swap][/<season>]`, Records view switch hidden on this tab) and `site/app.js` loading of `schedule.json`; register the tab state in `tests/layout/controls.py`; verify with `test_schedule_tab_opens` and `test_url_names_view_and_season` in `tests/layout/test_schedule_page.py` (4.9.6, 4.9.6.3)
- [x] 3.2 Create `site/schedule.js` (loaded with `?v=__BUILD__`): the `#sos-views` Weekly Ranks | Schedule Swap switch and the `#sos-season` selector (current season first), both in the controls registry; verify with `test_view_switch` and `test_season_selector` (4.9.6.1, 4.9.6.2)
- [x] 3.3 Render the Weekly Ranks table: Manager (picture, name, record), "1st Hardest" rank, Season, Played and Upcoming, then one cell per week with the opponent's points, weekly rank and picture, a full-name tooltip, a "Played" / "Projected" header and a line before the first upcoming week; finished seasons have no Upcoming column; verify with `test_weekly_ranks_table`, `test_week_cell` and `test_projected_weeks_marked` (4.9.6.4, 4.9.6.4.1, 4.9.6.4.3)
- [x] 3.4 Render the Schedule Swap table: rows and schedule columns in Swap order, own-schedule cell outlined, wins to one decimal, then Own, Avg, Index (signed) and Range ("1.6 – 5.1"); verify with `test_schedule_swap_table` (4.9.6.5)
- [x] 3.5 Add the `--sos-*` OKLCH colour tokens (Weekly Ranks quarters with faded and solid shades; Swap ±2 buckets with a neutral grey within 0.05; text tints) for light and dark modes, adjusting lightness only, and add the pairs to `tests/test_colour_contrast.py`; verify with `test_schedule_cells`, `test_weekly_ranks_colours` and `test_schedule_swap_colours` (4.9.6.4.2, 4.9.6.5.1, 4.9.6.6)
- [x] 3.6 Make the Rank, Season, Played and Upcoming headers (Weekly Ranks) and the Rank, Own, Avg and Index headers (Swap) sortable with `site/sorting.js`, registered in `tests/layout/controls.py`; verify with `test_sortable_columns` (4.9.6.7)
- [x] 3.7 Add the note under each table with copy IDs (`data-copy` or `/*copy:ID*/`), plus the tab, view, heading and unavailable-message copy, and run `python -X utf8 -m ffapp site-copy`; verify with `test_notes_shown` and `pytest tests/test_site_copy.py` (4.9.6.8)
- [x] 3.8 Phones: the table scrolls inside its card with a sticky, one-line Manager column (the Forecast table's `.col-owner` offset and shadow), and below 600 px the Swap puts Index right after Rank; verify with `test_manager_column_pinned_on_phones` and `test_summary_columns_first_on_phones` at 360, 390, 414 and 440 px, and with the layout check passing in Chromium, WebKit and Firefox with axe-core clean in light and dark modes (4.9.6.9, 4.9.6.9.1)
- [x] 3.9 Update `docs/league-records.md` for the `site/league.js` routing change and redraw `tools/league_records_diagram.py` if its boxes change; verify with `pytest tests/test_feature_docs.py`

## 4. Requirements and Final Checks

- [x] 4.1 Redraw the requirements diagrams (`python -X utf8 tools/requirements_diagram.py`) and confirm `pytest tests/test_requirements.py` reports no findings for the new requirements (no missing tests, IDs under their primary parents)
- [x] 4.2 Run the full suite (`python -X utf8 -m pytest`) and a local build (`python -m ffapp build`), then check both leagues' Strength of Schedule tab in the browser at 1280 and 360 px against the canvas mockups

## Workflow follow-up

- At archive: sync the specs, add standard reviews for the new specs `strength-of-schedule` and `strength-of-schedule-page`, and redo the review of `playoff-odds-simulation` in `openspec/inspection-checklist.md` (owner's approval).
- Commit, push and archive only when the owner asks.
