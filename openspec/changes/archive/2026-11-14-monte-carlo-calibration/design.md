# Design

## Context

See proposal.md for motivation. What the code and data already give us (checked 2026-11-14):

- **Replay is already possible.** `odds.run_as_of(store, config, league_key, data, as_of, current=False, noise=...)` builds inputs for any stored season: fixed records from stored matchups, the real schedule, rosters from the next week's matchup `players`, projected lineups from stored projections, real playoff points for scored playoff weeks. This is how the current-season backfill works.
- **Leave-season-out is one call.** `noise.collect_residuals(exclude_after=(season, 0))` drops every week of that season in both leagues, because the filter is `season == exclude_after[0] and week > 0`.
- **Per-week simulated scores exist in memory.** `SimResult.weekly_scores[week]` is a `(runs, 12)` array for every unscored week, but `run_as_of` returns only the summarized payload.
- **Ground truth is stored.** Nine completed league-seasons (dynasty 2022–2025, redraft 2021–2025) each have 17 matchup weeks with `players`, `starters`, `players_points`, `points`, plus `brackets.json` whose `p == 1` winners game names champion (`w`) and runner-up (`l`). `verify-brackets` proves `standings.seed_order` plus the bracket logic reproduce every stored bracket. Projections are stored for weeks 1–17 of 2021–2026 (about 450 projected players per week even in 2021).
- **Playoff weeks are partial.** In a playoff week, teams on a bye have `matchup_id: null` and the matchup rows are bracket games, so head-to-head comparisons only make sense in regular-season weeks.
- **Cost.** Building pools takes about 1.2 s per season, inputs 0.3 s per as-of week, and a 10,000-run simulation under 0.1 s. Nine seasons × 17 as-of weeks is roughly two minutes end to end, so replays can keep the production run count.
- **Config** rejects unknown top-level keys (`leagues`, `overrides` only). The site is `index.html` + `app.js` + `styles.css` + vendored Chart.js, with theme tokens and a validated 12-colour team palette.

## Goals / Non-Goals

**Goals:**
- Replay with the production code path, so the calibration measures the model the site actually publishes.
- Separate the three questions the user asked: is the noise the right width (score level), are game odds right (game level), are the published chances right and useful (season level, with a baseline).
- A knob that defaults to off and leaves results bit-identical when unset.
- Outputs that are plain data in the repo, re-aggregatable without re-simulating, and publishable by the existing export.

**Non-Goals:**
- Automatic tuning. The report informs a human decision; nothing changes `config/leagues.yaml`.
- Recovering pregame projection versions (Sleeper serves only the final version).
- Calibrating the in-progress season at season level (its outcomes are unknown). Weekly score and game checks for 2026 are left out too, so every row in the report comes from the same leave-season-out procedure.
- A fully general calibration framework. Metrics are the few named in the spec.

## Decisions

### 1. Replay through `run_as_of`, exposing the raw result
Split `odds.run_as_of` into `simulate_as_of(...) -> (SimInputs, SimResult, payload)` and the existing `run_as_of` (calls it, stores the payload, returns it). The calibration driver calls `simulate_as_of`, stores the payload itself with `store.write_odds`, and reads `weekly_scores` from the result for the score and game levels.

*Alternative:* a separate replay path that reimplements input building. Rejected: it would calibrate something other than the shipped model.

### 2. Residual scale lives in the pools
`ResidualPools` gets a `scale: float = 1.0` field applied in `sample()` (`pool[idx] * self.scale`). `build_pools(store, config, *, exclude_after=None, scale=None)` defaults the scale to `config.simulation.residual_scale`. Multiplying by exactly 1.0 is a no-op in IEEE floating point, so existing seeds reproduce existing results. The odds payload records `residual_scale`. `ffapp calibrate --residual-scale X` overrides the configured value for the replay only.

*Alternative:* scale the projections or add a Gaussian term. Rejected: a multiplicative scale on the empirical residuals keeps the pools' shape (skew, fat tails) and is the one parameter the score-level test directly informs.

### 3. Configuration shape
```yaml
simulation:
  residual_scale: 1.0   # optional; multiplies every sampled score residual
```
`Config.simulation: SimulationConfig(residual_scale=1.0)`; the parser accepts the new top-level key, requires a positive int or float (bool rejected), and keeps rejecting unknown keys inside it. The repo's `config/leagues.yaml` gains the key commented out with a note that it exists for evaluated changes only.

### 4. Which as-of weeks count for which outcome
Replay as-of weeks 0–16 for every completed season (17 would simulate nothing). In the season-level comparison, a row is included only while the outcome is still undecided in general:

| outcome | as-of weeks compared | decided at |
|---|---|---|
| playoffs, bye, losers bracket, last, avoid bottom two | 0–13 | end of week 14 |
| final | 0–15 | week 16 |
| title | 0–16 | week 17 |

Rows from clinched or eliminated teams within those weeks stay in (they are genuine 0%/100% predictions). Rows after the decision would only add trivially correct 0/1 cases and flatter the Brier score.

### 5. Actual outcomes from the stored season
- Final seeds: `standings.seeds(regular_season_records(matchups, start..playoff_week_start-1))`, the same computation `verify-brackets` checks against Sleeper.
- `playoffs = seed <= 6`, `bye = seed <= 2`, `losers_bracket = seed > 6`, `last = seed == 12`, `avoid_losers_bye = seed <= 10`.
- `title` and `final` from the stored winners bracket's place-1 game (`w` champion, `l` runner-up). The bracket is Sleeper's record; our replay of it is already verified equal, so the stored one is the ground truth.

### 6. Score and game levels use the next regular-season week only
For as-of `w` with `w + 1 <= 14`, compare `weekly_scores[w + 1]` with week `w + 1`'s stored matchups:
- **Score:** per team, percentile rank of the actual `points` in the 10,000 simulated scores (ties counted half), 50/80/95% central-interval coverage, mean simulated minus actual. Also computed against the actual points of the *simulated* lineup (sum of `players_points` over the sim's starters) so the lineup effect can be separated from the noise width.
- **Game:** per pairing, `P(A > B)` from the same arrays (ties half) versus the real winner; 10-point bins on the favourite's chance, plus Brier.
This yields 9 × 14 × 12 = 1,512 team-weeks and 756 games. Playoff weeks are excluded (byes, bracket pairings).

### 7. Baseline
For outcome `o` with base rate `b` (6/12, 2/12, 2/12, 1/12, 6/12, 1/12, 10/12) and `f = remaining regular weeks / 14`:
- As of week 0: `p = b`.
- Afterwards: extrapolate each team's record (`wins + win% × remaining`), rank by that then points scored, mark the teams in qualifying positions (`top 6`, `top 2`, `bottom 6`, `12th`, `top 10`; for final and title the top 6 at `2/6` and `1/6` each), and shrink toward the base rate: `p = f·b + (1 − f)·indicator`. After week 14 the regular-season outcomes are decided and the baseline for title/final stays at the week-14 value.
Skill score = `1 − Brier_model / Brier_baseline`. This is "a person reading the standings"; it is deliberately simple and documented in the report so nobody mistakes it for a rival model.

### 8. Lineup gap
For every stored completed week in every stored season (2026's completed weeks included, since no simulation is involved): the sim's lineup via `odds.projected_lineup(...)` over the matchup `players`, versus the stored `starters`. Report per league the mean of `projected(best) − projected(started)` and `actual(best) − actual(started)` (actual from `players_points`; a starter without a projection or points counts 0; `"0"` placeholders in `starters` are skipped).

### 9. Metrics module is pure
`calibrate.py` separates a pure metrics layer (`pit`, `coverage`, `reliability_bins`, `brier`, `baseline_probability`, `season_outcomes`) from the driver that walks seasons. The pure functions take arrays and dicts, so tests hand-build inputs (e.g. a perfectly calibrated synthetic set gives coverage ≈ nominal; a wrong champion flips exactly one title outcome).

### 10. Outputs
```
data/odds/<league>/<season>/asof_NN.json          replay payloads (same schema as the live ones, plus residual_scale)
data/calibration/rows/<league>/<season>.json      per as-of rows: season predictions + actuals, game chances + results, score PITs + interval hits
data/calibration/report.json                      aggregates: meta (generated_at, runs, residual_scale, seasons, seed), per league + overall sections
data/calibration/report.md                        the same figures rendered as tables, with the caveats
```
The rows files let the report be re-binned or inspected without replaying. Two decimal-ish rounding (4 dp on rates) keeps the JSON stable in git. Rough size: 150 payloads × 10 KB + rows ≈ 2 MB once; later runs overwrite in place.

### 11. Export and site page
- `export_site` copies `data/calibration/report.json` to `site/data/calibration.json` when present and adds `"calibration": {"generated_at", "file"}` (or `null`) to `index.json`. Missing report → no file, `null` in the index, export succeeds.
- New `site/calibration.html` + `site/calibration.js`, sharing `styles.css`, Chart.js and the theme toggle. The header of both pages carries a small nav link ("How good are these odds?" / "← Playoff odds"). Content, top to bottom: headline sentence per outcome (e.g. "Teams shown at 30% made the playoffs 31% of the time"), a reliability chart (observed rate vs predicted bin, diagonal reference, point size by count, outcome switcher buttons styled like the metric switcher, one series per league using `--team-1` and `--team-2` which are already validated in both themes), a score-interval coverage table, a Brier/skill table, the lineup gap table, meta (seasons, runs, residual scale, generated date) and the caveats list. Everything reads `data/calibration.json`; when the index says `null` the page shows a single "Calibration has not been run yet" card.
- The dataviz skill's rules apply when the chart is built: one axis, legend plus direct labels, hover tooltips with the count per point, text in ink tokens, both themes validated.

### 12. CLI
`ffapp calibrate [--runs N] [--seed N] [--residual-scale X]`. Defaults: 10,000 runs (the production count, keeps the stored replays spec-compliant), seed derived per (league, season, as-of) as today, scale from config. Prints one line per league-season replayed and a short summary (coverage at 80%, playoff skill). Not added to `refresh`. README gains the command and a "Calibration" section; the workflow is unchanged because `git add data` already commits `data/calibration/`.

## Risks / Trade-offs

- [Projection vintage: stored past projections may include game-day updates, so historical replays look slightly sharper than live odds] → stated in the report's caveats and on the site page; not fixable with Sleeper's API.
- [Rows within a season are correlated, so "1,500 cases" overstates independence] → the report shows both the case count and the independent count (team-seasons, games) and the page labels them as cases, not samples.
- [Monte Carlo noise in the bins] → 10,000 runs keeps per-row error under 1 point; bins also show counts so thin bins are visibly thin.
- [Replays add about 150 files to `data/odds/`] → one-off ~1.5 MB; the export reads only the current season, so site payloads are unaffected. Future features (past-season odds pages) get the history for free.
- [Leave-season-out pools include seasons *after* the replayed one] → residuals are treated as stationary, which the current model already assumes; documented as a decision, and `exclude_after` remains available if a strictly chronological check is wanted later.
- [Sparse early-season projections (2021) could shrink pools or lineups] → pool sizes are logged per replay; the rows file records teams with fewer than the full starter count so they can be excluded from the score level if needed.
- [Knob invites overfitting] → the knob is off by default, the report records the scale used, and the README says a change should be justified by the score-level coverage across all seasons, not by season-level bins.

## Migration Plan

1. Merge the code; `pytest` and the daily refresh behave exactly as before (scale 1.0, no report → export writes no calibration file).
2. Run `python -m ffapp calibrate` locally once (minutes), inspect `data/calibration/report.md`, run `python -m ffapp export`, commit `data/odds`, `data/calibration`, `site/data`, push. The next deploy publishes the page.
3. Rollback: delete `data/calibration/` and re-export; the page reverts to "not run". Replay odds files are inert.
