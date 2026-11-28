# Tasks

## 1. Preseason Values

- [x] 1.1 Add `season_projections(season)` to `src/ffapp/espn.py` (`scoringPeriodId=0`, `kona_player_info`, the season line `statSourceId` 1 / `statSplitTypeId` 0) and, in a new `src/ffapp/preseason.py`, the ESPN stat-id mapping to the league's scoring keys, per-game value = scored line / 17 (kickers and defences: ESPN projected season points / 17); verify with `test_preseason_value_from_stat_line` in `tests/test_preseason.py` (1.5.1)
- [x] 1.2 Projection sources by season: ESPN; 2023 Sleeper season projections, else the week-1 Projection as the per-game value; record each Player's source; verify with `test_projection_sources` (1.5.1.1)
- [x] 1.3 ESPN to Sleeper matching by normalised name (suffixes dropped), position and NFL team, defences by team; unmatched drafted Players listed; verify with `test_espn_matching` (1.5.1.2)
- [x] 1.4 Bye weeks from the weekly stats (a team's played weeks), a Player's value 0 in his bye week; verify inside `test_preseason_value_from_stat_line`

## 2. Preseason Simulation

- [x] 2.1 Preseason rosters: redraft drafted rosters, dynasty week-1 rosters without taxi Players; a missing kicker or defence scores the season's replacement level; verify with `test_preseason_rosters` and `test_missing_kicker_scores_replacement_level` (1.5.2, 1.5.2.1)
- [x] 2.2 Add an optional `weekly_scores` hook to `simulate()` in `src/ffapp/simulate.py` (standings, seeds and brackets unchanged; existing callers unaffected, `pytest tests/test_simulate.py` still green), and update `docs/simulation.md` and redraw `tools/simulation_diagram.py`
- [x] 2.3 The absence hook: per team-week absence masks at QB 10.6%, RB 11.9%, WR 11.4%, TE 10.2%, K 4.4%, DEF 0%, lineup slots filled by the highest-valued healthy eligible Player, else replacement level, each chosen Player scoring his value plus a `NoiseModel` residual; verify with `test_absence_rates` and `test_bench_fills_absent_starter` (1.5.3, 1.5.3.1)
- [x] 2.4 Outcomes per team (title, playoff and last-place shares to 0.001, wins and losses to 0.1, points per week to 0.1) and Wins Saved from a second run on the same seed with replacement-level fill-ins; verify with `test_outcomes` and `test_wins_saved` (1.5.4, 1.5.4.1)

## 3. Grades, Record, Timing and Export

- [x] 3.1 Grades in the specified order with plus and minus; verify with `test_grade_letters` and `test_plus_and_minus` (1.5.5, 1.5.5.1)
- [x] 3.2 Write the record `data/preseason/<league>/<season>.json` once (values, sources, rosters, unmatched, replacement levels, teams, runs, seed) and never rewrite it; the `preseason` command and optional cold-run step after `replacement`, making a Forecast for each league-season with a complete draft, values available and no record; add `data/preseason/` to `docs/refresh-modes.md`; verify with `test_preseason_forecast_made_once`, `test_made_after_the_draft` and `pytest tests/test_storage_tiers.py tests/test_refresh.py` (1.5, 1.5.8, 6.1)
- [x] 3.3 Export `site/data/<league>/preseason.json` with each team's Manager and, for finished seasons, final place; verify with `test_actual_finish` and `test_export_writes_preseason_file`, and run `python -m ffapp build` (1.5.6, 1.5.7)
- [x] 3.4 Backfill locally (redraft 2021 to 2026, dynasty 2022 to 2026) and report to the owner, per league-season, the grade counts (A+ to F), the unmatched drafted Players and each A/F team's actual finish. Stop for the owner's confirmation of the bands before the page goes live (confirmed 2026-11-27: bands kept; redraft gets a Draft Strength column; calibration and drift trials not adopted, design decision 10)

## 4. Preseason Tab

- [x] 4.1 Add the fourth `#lg-tabs` button "Preseason", routing `#<league>/league/preseason/<season>` in `site/league.js`, loading `preseason.json` in `site/app.js`, and the Season picker; register controls in `tests/layout/controls.py`; verify with `test_preseason_tab_opens`, `test_season_picker` and `test_url_names_the_season` in `tests/layout/test_preseason_page.py` (4.9.8, 4.9.8.1, 4.9.8.2)
- [x] 4.2 Create `site/preseason.js` (`?v=__BUILD__`): the table with Grade, Manager, Title, Playoffs, Last (share bars), Forecast, Pts/Wk, Wins Saved and Finished, ordered by title share and sortable; verify with `test_table_columns_and_order`, `test_share_bars` and `test_table_sorting` (4.9.8.3, 4.9.8.3.1, 4.9.8.3.2)
- [x] 4.6 Draft strength: the redraft rank by preseason points per week in the export and a Draft Strength column (ordinal) after Pts/Wk on redraft seasons only; verify with `test_draft_strength_rank` and `test_draft_strength_column` (1.5.6.1, 4.9.8.3.4)
- [x] 4.3 Add the 13 `--grade-*` token pairs (hex with OKLCH notes; light from the PreseasonGrades artboard, dark by lightness only) in the light and both dark blocks and their pairs in `tests/test_colour_contrast.py`; verify with `test_preseason_grade_badges` (4.9.8.4)
- [x] 4.4 The grade key and method note with copy IDs, and `python -X utf8 -m ffapp site-copy`; verify with `test_key_and_note` and `pytest tests/test_site_copy.py` (4.9.8.5)
- [x] 4.5 Phone list rows; verify with `test_phone_rows` at 360, 390, 414 and 440 px and the layout check in Chromium, WebKit and Firefox with axe-core clean in both modes (4.9.8.3.3)

## 5. Docs

- [x] 5.1 Calculations.txt section 26 "Preseason Forecast" (values and sources, matching, absences and rates, bench fill-ins, Wins Saved, grade bands), register `preseason.py` in `tests/test_calculations_doc.py`, and the glossary terms Preseason Forecast, Preseason grade and Wins Saved; verify with `pytest tests/test_calculations_doc.py tests/test_requirements.py`
- [x] 5.2 Write `docs/preseason.md` and `tools/preseason_diagram.py`, register them in `tests/test_feature_docs.py` for `src/ffapp/preseason.py` and `site/preseason.js`, and update `docs/league-records.md` for the `site/league.js` routing; verify with `pytest tests/test_feature_docs.py`

## 6. Requirements and Final Checks

- [x] 6.1 Run `python -X utf8 tools/requirements_impact.py 6.1`, redraw the requirement diagrams, and confirm `pytest tests/test_requirements.py` reports no findings for the new requirements
- [ ] 6.2 Run the full suite and a local build, and check the Preseason tab in the browser at 1280 and 360 px against the canvas mockups

## Workflow follow-up

- At archive: sync the specs, add standard reviews for `preseason-forecast` and `preseason-page`, redo `data-storage-tiers` (owner's approval).
- Commit, push and archive only when the owner asks.
