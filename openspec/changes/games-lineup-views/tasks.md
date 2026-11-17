# Tasks

## 1. Views and lineup choices

- [x] 1.1 Build the model lineup from frozen projections (log value else stored projection, the week's projected replacement floor) and simulate it with `simulate_fixed` and a `model:` seed, and verify tests show a 6.6 receiver chosen over a 6.4 starter, replacement fills where the roster is short, and determinism
- [x] 1.2 Store `views` per game in finished week files (log weeks: actual = record, new model; pre-log weeks: model = record, new rebuilt actual) and in the live week (actual = live forecast, model recomputed each run), filled once and recomputed with `--force-records`, and verify tests cover both kinds of week, the live week and no recomputation on re-run
- [x] 1.3 Compute lineup choices per team (realised replacement level for fills, projected fallback; live week counts kicked-off players only, fills once final) on both views, and verify tests reproduce +7.4 and -12.0 examples and the live-week rule
- [x] 1.4 Run `python -m ffapp games` on the real store and verify dynasty week 10's tg1212 actual view lists Adonai Mitchell, its model view Xavier Worthy, and every finished week has both views

## 2. Export

- [x] 2.1 Export `views` (model and actual rows, actual-only WPA, `benched` on model rows, `lineup_choices`, view source incl. `rebuilt`) and `default_view` per week, falling back to `record` when views are missing, and verify `tests/test_games_export.py` covers a log week, a rebuilt week, an upcoming week (model only) and the fallback

## 3. Site

- [x] 3.1 Add the Model | Actual toggle per card (default from the export, switches rows, key players, means, win probabilities and chart; actual-score lines in both; "rebuilt" label), and verify in the browser on week 10 and week 11
- [x] 3.2 Show lineup choices per team (green / red) and the "BN" tag in the model view, and verify on week 10 for tg1212
- [x] 3.3 Link the two "Full Lineup" expanders of a card and capitalise the label, and verify in the browser that opening one opens both
- [x] 3.4 Rework player rows (aside column for WPA or kickoff time, collapsed when empty; "F" only on the live week), and verify by screenshots of an upcoming, a finished and a live week that names are no longer truncated in the narrow column
- [x] 3.5 Rename the button to "Refresh Data" and hang its note below without moving the button, and verify by a screenshot that it lines up with the other header buttons at desktop and phone widths

## 4. Integration

- [x] 4.1 Update the README Games section (views, rebuilt, lineup choices), run `pytest`, `node --test relay/worker.test.mjs`, `openspec validate games-lineup-views --strict` and `python -m ffapp refresh`, and verify all pass
- [x] 4.2 Update the roadmap memory note with the lineup views and lineup choices

## Workflow follow-up

- Commit and push after the user's review, then archive the change with spec sync.
