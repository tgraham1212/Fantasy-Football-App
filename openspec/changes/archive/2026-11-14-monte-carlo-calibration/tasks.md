# Tasks

## 1. Residual scale knob

- [x] 1.1 Add `simulation.residual_scale` to `src/ffapp/config.py`: new top-level key, `SimulationConfig(residual_scale=1.0)` on `Config`, positive int/float only (bool and text rejected, unknown keys inside `simulation` rejected). Verify with tests in `tests/test_config.py`: absent section → 1.0; `0.9` → 0.9; `0`, `-1`, `"big"` and `true` raise `ConfigError` naming `residual_scale`; the repo config still loads.
- [x] 1.2 Add a `scale` field to `ResidualPools` applied in `sample()`, and have `build_pools` take `scale` defaulting to the configured value. Verify in `tests/test_noise.py` that a pool sampled at scale 1.2 returns exactly 1.2× the scale-1.0 draws for the same seed, and that scale 1.0 is bit-identical to the pre-change behaviour (same `GaussianNoise`-free pool, same seed, same array).
- [x] 1.3 Record `residual_scale` in every odds payload written by `run_as_of` and keep `simulate` output unchanged otherwise. Verify `tests/test_odds.py` asserts the key on a stored payload and the existing payload test still passes.
- [x] 1.4 Document the key (commented out) in `config/leagues.yaml` and in the README configuration section, with the note that it is for evaluated changes only. Verify `python -m ffapp export` still runs with the untouched config.

## 2. Replay driver

- [x] 2.1 Split `odds.run_as_of` into `simulate_as_of` (returns inputs, raw `SimResult` and payload) and `run_as_of` (stores and returns the payload). Verify the existing `tests/test_odds.py` run-as-of tests pass unchanged and a new test shows `simulate_as_of` returns `weekly_scores` for every simulated week.
- [x] 2.2 Create `src/ffapp/calibrate.py` with `replay_season(store, config, league_key, season, *, runs, seed, scale)` that builds leave-season-out pools via `exclude_after=(season, 0)`, replays as-of weeks 0–16, stores each payload in the odds history and yields the raw results. Verify with a test on the fixture store's completed dynasty 2025 season (2025 week-1 projections reused for each week, 300 runs): `store.odds_weeks("dynasty", "2025") == list(range(17))`, every payload has `season == "2025"` and the scale used, and the 2026 odds files are untouched.
- [x] 2.3 Add `completed_seasons(store, config)` listing only `status == "complete"` league-seasons. Verify a test shows the fixture's 2026 season is excluded and 2022–2025 are included.

## 3. Ground truth and metrics (pure functions)

- [x] 3.1 Implement `season_outcomes(data)` returning per-roster booleans for playoffs, bye, final, title, losers_bracket, last and avoid_losers_bye from final standings and the stored winners bracket's place-1 game. Verify with a test on the fixture's 2025 dynasty season that exactly 6 teams are `playoffs`, 2 `bye`, 1 `last`, 10 `avoid_losers_bye`, one `title`, two `final`, and the champion matches `brackets.json`.
- [x] 3.2 Implement `pit`, `interval_coverage` (50/80/95) and `mean_bias` over a `(runs,)` sample array and an actual value, with ties counted half. Verify tests: 10,000 draws from N(0,1) with actuals drawn from the same distribution give coverage within 3 points of nominal; a constant pool returns PIT 0.5; actual above every draw returns PIT 1.0.
- [x] 3.3 Implement `win_probability(a, b)` (ties half), `reliability_bins(probabilities, outcomes, width=0.10)` returning per-bin predicted mean, observed rate and count, and `brier`. Verify tests: perfectly separated predictions give Brier 0; probabilities of 0.5 with half the outcomes true give Brier 0.25; bins with no cases report count 0 and no rate.
- [x] 3.4 Implement `baseline_probability(outcome, records, remaining_weeks, total_weeks, n_teams)` per design decision 7. Verify tests: week 0 gives 0.5 for playoffs and 1/12 for title for every team; with all 14 weeks played, a top-6 team gets 1.0 for playoffs and a 12th-place team 1.0 for last; a mid-season value lies strictly between the base rate and the indicator.
- [x] 3.5 Implement `included_as_of_weeks(outcome, rules)` per design decision 4. Verify a test asserts 0–13 for the regular-season outcomes, 0–15 for final and 0–16 for title with the standard rules.
- [x] 3.6 Implement `lineup_gap(store, config, league_key, data, week)` returning projected and actual gaps between the best-projected lineup and the stored starters, skipping `"0"` placeholders. Verify with a test that a week where the stored starters already are the best lineup gives 0.0 for both gaps, and a hand-edited matchup that benches the top WR gives a positive projected gap equal to the projection difference.

## 4. Scoring the replays and writing the report

- [x] 4.1 Build the per-season rows from each replay result: season-level (as-of, roster, outcome, predicted, baseline, actual) using decisions 4–7, game-level (next regular-season week, favourite's chance, won) and score-level (PIT against started-lineup points and against the simulated lineup's actual points, interval hits, bias). Write them to `data/calibration/rows/<league>/<season>.json`. Verify with the fixture replay that row counts are 12 × 14 for score rows, 6 × 14 for game rows, and that season rows for `playoffs` stop at as-of 13 while `title` rows reach 16.
- [x] 4.2 Aggregate rows into `report.json` (meta, per league and overall: reliability bins, Brier, baseline Brier and skill per outcome; coverage and bias per interval; game bins and Brier; lineup gaps; case and independent counts) and render `report.md` from the same structure. Verify a test that builds the report from hand-made rows and checks that every number in the Markdown appears in the JSON, and that both files are overwritten on a second run with a different scale.
- [x] 4.3 Add `cmd_calibrate` and the `calibrate` subcommand (`--runs`, default 10000; `--seed`; `--residual-scale`) to `src/ffapp/cli.py`, not wired into `refresh`. Verify `tests/test_refresh.py` still shows refresh runs only its four steps, and a CLI test on the fixture store runs `calibrate --runs 200` and produces both report files.
- [x] 4.4 Add the "Calibration" section to the README (what the three levels mean, how to read the report, the knob policy, the command). Verify the documented command runs as written on the repo data.

## 5. Export and site page

- [x] 5.1 Make `export_site` copy `data/calibration/report.json` to `site/data/calibration.json` when present and add `calibration` (`generated_at`, `file`, or `null`) to `index.json`. Verify tests in `tests/test_export.py` cover both the present and absent cases and that the absent case still writes the league files.
- [x] 5.2 Create `site/calibration.html` and `site/calibration.js` sharing `styles.css`, the theme toggle and Chart.js: headline sentences, reliability chart with outcome switcher (one series per league using the validated `--team-1`/`--team-2` tokens, diagonal reference, point size by count, tooltips showing predicted, observed and count), coverage table, Brier/skill table, lineup-gap table, meta and caveats; a single "not run yet" card when `index.json` reports `null`. Add the cross-links to both page headers. Verify headless screenshots in both themes at desktop and 375px width show the chart and tables with no horizontal page scroll, and that renaming `calibration.json` away shows the not-run card without console errors.
- [x] 5.3 Document the page in the README website section (URL, what it shows, that it updates only when `calibrate` is re-run and committed). Verify the README's local-serving instructions show the page at `/calibration.html`.

## 6. Integration check

- [x] 6.1 Run the full sequence on the repo data: `pytest`, `python -m ffapp calibrate`, `python -m ffapp export`, serve `site/` locally. Verify: nine league-seasons replayed with 17 odds files each, `report.md` lists 1,512 score rows and 756 games, the 2026 odds files are byte-identical to before, the live pages render as before, and the calibration page shows the report.

## Workflow follow-up

- Commit `data/odds` replays, `data/calibration/` and `site/data/` after reviewing `report.md`; the next scheduled deploy publishes the page.
- Decide on any residual-scale change only from the score-level coverage across all seasons, and record the decision in the config comment if one is made.
- Archive the change with spec sync after the above.
