# Tasks

## 1. Calculation and Docs

- [x] 1.1 Rewrite `Calculations.txt` section 11 (Lineup Choices against the default lineup: rostered Players at their last pre-kickoff Sleeper Projection, no free-agent fills, empty slots 0, live rule, the QB example) and the lineup lines of section 23 (no realised replacement level; stored-Projections caveat kept). Verify: `tests/test_calculations_doc.py` passes.
- [x] 1.2 Update `docs/league-records.md` (data sources, storage and step 3) and the Lineup Choices mention in `docs/simulation.md`; redraw `tools/league_records_diagram.py` if its sources change. Verify: `tests/test_feature_docs.py` passes.

## 2. Default Lineup and Totals (`src/ffapp/views.py`)

- [x] 2.1 Add a `default_lineup` helper (`model_lineup` with no floor) and make `lineup_choices` count an empty row as 0 on both sides, dropping its `fills` argument. Verify: `tests/test_views.py::test_lineup_choices_examples_and_live_rule` updated (QB swap +5.0 and -5.0, empty slot, live rule) and `tests/test_views.py::test_default_lineup_is_roster_only` (a higher-projected free agent is never used; a slot nobody can fill counts 0 on both sides).
- [x] 2.2 Use the default lineup in `build_views` for live and finished weeks, leaving the Model view's lineup and floor unchanged, and store `"lineup_basis": "roster-default"` with the week's views. Verify: `tests/test_views.py::test_views_for_pre_log_and_logged_weeks` still passes and checks the basis marker.
- [x] 2.3 Rebuild past-season weeks in `season_lineup_choices` from the default lineup with no replacement levels, trusting stored values only when their basis matches. Verify: `tests/test_views.py::test_past_season_lineup_choices` (a stored old-basis value is recomputed; a matching one is kept).

## 3. One-Time Recompute (`src/ffapp/games.py`)

- [x] 3.1 In `update_games`, recompute only `lineup_choices` (no simulation, committed record untouched) for weeks whose stored views carry another basis. Verify: a `tests/test_views.py` case where an old-basis week gets new values and its `data/games/` record file is unchanged.

## 4. Site Text

- [x] 4.1 Change the GAME-09 hover to "Points vs starting the highest Sleeper projections on the roster: what the manager's starters scored minus what those players scored". Verify: `python -m ffapp site-copy` regenerates `site-copy.txt` with only GAME-09 changed.
- [x] 4.2 Add the League tab explanation for the two lineup-choices records (hover and focus tip on the rows, note atop their pop-ups, copy ID LG-48), register the tip in `tests/layout/controls.py`, and run `python -m ffapp site-copy`. Verify: `tests/layout/test_league_records_page.py::test_lineup_choices_explained` and the layout check for the new control pass.

## 5. Verification and Review

- [x] 5.1 Rebuild (`python -X utf8 -m ffapp build`) and compare: redraft and dynasty Lineup Choices no longer include free-agent fills, no empty slot earns points, and the League records' lineup entries change accordingly. Verify: a scratch check over every stored season reports zero free-agent rows in the default lineups.
- [x] 5.2 Run `tools/requirements_impact.py` for 2.8, 2.8.1, 2.8.2, 2.1.14 and 4.9.2.1.3.4, re-inspect any directly linked Inspection-verified requirement (with the maintainer's approval), and redraw `tools/requirements_diagram.py`. Verify: `tests/test_requirements.py` passes apart from findings resolved at archive.
- [x] 5.3 Full suite. Verify: `python -X utf8 -m pytest` passes, including the layout check.

## Workflow follow-up

- Commit, push and archive with spec sync when the maintainer asks; redo the standard reviews of `game-predictions`, `games-page` and `league-records-page` at archive.
