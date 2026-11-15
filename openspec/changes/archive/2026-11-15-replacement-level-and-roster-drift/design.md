# Design

## Context

See proposal.md for motivation. Facts that shape the approach (measured on the stored seasons on 2026-11-14 unless noted):

- **Player projection errors do not persist.** Week-to-week autocorrelation of a player's actual-minus-projected error is 0.02; the season-level share of error variance is 0.00 at every position. Projections are refreshed weekly and absorb form. There is nothing to gain from a persistent player error term.
- **Team-level persistence is small.** Teams beat or miss their simulated mean persistently by about 3.8 points a week in dynasty and 5.7 in redraft (ICC 0.03 and 0.07). Not addressed here; it is the natural follow-up if over-confidence remains.
- **Frozen rosters are the problem.** A team's projected strength under the roster it holds now, evaluated with projections for a week k ahead, predicts its true strength that week with slope 0.90/0.83/0.82 (dynasty, k = 2/5/12) and 0.50/0.43/0.39 (redraft). Filling zero-projection slots with a replacement-level player raises redraft to 0.89/0.79/0.73 and dynasty to 0.99/0.97/0.96 and roughly halves the residual drift (redraft 2.1/3.1/4.0 points). Sleeper's stored matchups give every week's rosters (`players`), so free agents for any past week are reconstructible.
- **Stats endpoint.** `https://api.sleeper.com/stats/nfl/{season}/{week}?season_type=regular&position[]=...` returns the same row shape as projections (`player_id`, `season`, `week`, `stats`, `player`, `team`, `opponent`, `last_modified`, `company: sportradar`), about 750 KB and 760 rows for 2025 week 1 of which 363 carry `pts_*`. Stat lines use the same keys as projections (`rec`, `rush_yd`, `bonus_rec_wr`, ...), so `scoring.projected_points` scores them. Rows without `pts_*` are players who did not play.
- **Code hooks.** `projections.py` has the validate/upsert/refresh pattern to copy. `odds.lineup_from_projections` builds lineups from a projections dict; `odds.build_inputs` computes `starters[rid][week]`; `simulate.simulated_scores(week)` sums `starter.projected + noise` per team; `rosters_as_of` already distinguishes current rosters (minus IR/taxi) from a stored week's `players`. `calibrate.replay_season` builds leave-season-out pools with `exclude_after=(season, 0)`. Config rejects unknown keys and already has a `simulation` section.

## Goals / Non-Goals

**Goals:**
- Make replacement level a stored, reusable concept with an unambiguous definition (free agents chosen by projection, scored two ways).
- Fix the simulation's frozen-roster bias with two measurable pieces that can be switched off independently for evaluation.
- Keep the weekly noise model untouched so the score-level calibration stays valid by construction.
- Estimate everything from roster facts, never from playoff outcomes.

**Non-Goals:**
- Changing the noise pools to use free-agent stats (separate change).
- Position-specific N, per-team manager effects, modelling trades.
- Changes to the league pages. The calibration page gains an explanatory section (decision 12); the drift diagnostic for N selection stays in the report files.

## Decisions

### 1. Stats store mirrors the projections store
`src/ffapp/stats.py` reuses `projections.validate_rows`, the record shape (`to_record`) and the newest-version upsert, keyed on `last_modified`. Rows are kept only when `stats` has a `pts_*` key (the player played). Storage `data/stats/<season>/week_NN.json`; `Store.read_stats/write_stats/stats_weeks`. `SleeperClient.stats(season, week)` uses a `stats_base` of `https://api.sleeper.com/stats/nfl` with the same position query. `ffapp stats [--backfill]` behaves like `projections`: current season every refresh, all seasons on backfill, all-or-nothing per season. `actual_points(record, scoring)` is `scoring.projected_points` on the stat line; a test over a stored season checks it reproduces `players_points` for 99% of rostered player-weeks within 0.05.

*Alternative:* only store `pts_half_ppr`. Rejected: both leagues score the raw line (bonuses, half PPR variants), and the realised replacement level must use each league's own scoring.

### 2. Free agents and weekly levels (`src/ffapp/replacement.py`)
```
free_agents(projections_for_week, rostered_ids) -> {position: [(player_id, projected), ...]}  # sorted desc, projected > 0
weekly_level(projections, scoring, rostered, stats=None, n=3) -> {position: {"projected": float, "realised": float|None, "available": int, "players": [ids]}}
```
Rostered ids for a stored week = union of `players` over that week's matchup rows; for the present = union over current rosters of `players` (which already include reserve and taxi). Positions are the six fantasy positions; a player's position is the projection record's `position`. Only players with projection > 0 that week are candidates, so a free agent on bye is not a replacement that week. Realised = mean of `actual_points` over the same N players, 0 for a player with no stat row, `None` when the week has no stats stored.

### 3. Season value with shrinkage
`season_value(weekly_realised: list[float], prior: float, k: float) -> float` = `(n·mean + k·prior)/(n + k)`; n = 0 returns the prior. The prior for a league-season is the 50/30/20 weighted mean of the final season values of up to three earlier seasons of the same league with identical `scoring_settings` and `roster_positions`; weights renormalise when fewer exist; with none, the prior is the mean of the current season's projected weekly levels. k comes from `simulation.prior_weeks` (default 4). The season file records the prior and which seasons fed it.

### 4. Replacement file and command
`ffapp replacement` writes `data/replacement/<league>/<season>.json` for every stored season:
```json
{"league_key", "season", "top_n", "prior_weeks", "weeks": {"1": {"QB": {"projected", "realised", "available", "players"}, ...}},
 "season": {"QB": {"value", "prior", "prior_seasons", "weeks_played"}, ...}, "generated_at"}
```
It runs in `refresh` after `stats` and before `simulate`. The simulation does not read this file; it recomputes levels for its own future weeks (decision 5) so a stale file can never leak into odds. The file is for inspection and later features.

### 5. Floor in the simulation
`build_inputs` computes, per future week t, `levels[t] = weekly_level(projections_t, scoring_t, rostered_now, n)` where `rostered_now` is the union of the rosters the sim is using (so in a replay, the week-(as_of+1) rosters). `lineup_from_projections(..., floor=levels[t])` post-processes the greedy lineup: for each slot, if the chosen starter's projection is below the floor for that slot (FLEX: max of RB/WR/TE; a missing starter counts as 0), replace it with `Starter(slot, "FA:<pos>", pos, level)`. The fill is a normal starter to `simulate`, so it draws noise from the (position, band) pool. `--no-replacement-floor` / `floor=False` skips the post-processing. Floors use projected levels only; stats are never needed to simulate.

*Alternative:* add the free agents themselves to each team's candidate pool. Rejected: twelve teams would all start the same three players, and lineups would silently change roster identity.

### 6. Drift estimation (`src/ffapp/drift.py`)
For a league, over the completed seasons allowed (all stored, or all except the replayed one): for every as-of week w and later regular-season week t = w + k, with floored strength S (projected best lineup total) of each team under (a) the roster held at week w+1 and (b) the roster actually held at week t, both relative to the league mean of (b) that week:

- `slope_k` = least-squares slope of (b) on (a) through the origin-free fit, forced non-increasing in k (cumulative minimum);
- `sd_k` = standard deviation of the residual, forced non-decreasing in k (cumulative maximum);
- k = 1 is fixed at slope 1, sd 0 (the sim already uses the next week's real roster in replays; live it is the closest thing);
- horizons beyond the regular season (playoff weeks) reuse the last estimated k.

Output `DriftModel(league_key, slopes: list, sds: list, seasons: list, top_n)` stored to `data/model/<league>.json` by `simulate` and embedded in each odds payload under `model`. With fewer than two seasons the model is the identity (slope 1, sd 0) and says so.

### 7. Drift in the simulation
In `simulate`, after computing a week's raw team scores (projection sums plus noise), apply per team i for week t at horizon k:
```
adjusted = raw + (slope_k − 1) · (S_t[i] − mean_t) + D_k[i]        # D: (runs,) per team
D_k = D_{k−1} + Normal(0, sqrt(max(0, sd_k² − sd_{k−1}²)))          # random walk, D_0 = 0
```
`S_t` and `mean_t` come from the floored lineups already in `SimInputs` (add `strength[t][rid]`). Gaussian steps are used because the drift is an aggregate of many roster moves and only its second moment is estimated. `roster_drift=False` skips both terms. The same adjustment applies to playoff weeks (seeding is already decided by then, but game outcomes still depend on strength).

### 8. Calibration
- `replay_season` estimates `DriftModel` from the league's other seasons (`exclude_season`), so no leakage.
- The report gains `drift_diagnostic` per league: for k in (2, 3, 5, 8, 12), slope and sd under frozen and floored rosters, plus `top_n`. This is the same computation as decision 6 with the floor on or off, so it is one function with a flag.
- `calibrate --no-replacement-floor --no-roster-drift` pass through to `build_inputs`/`simulate`; the report's meta records both switches. Replay payloads written to `data/odds` carry `model` like live ones.

### 9. Configuration
```yaml
simulation:
  residual_scale: 1.0
  replacement_top_n: 3   # free agents averaged per position
  prior_weeks: 4         # shrinkage weight for the season replacement value
```
`replacement_top_n` positive int (bool rejected), `prior_weeks` non-negative number.

### 10. CLI and pipeline
`stats` and `replacement` commands; `refresh` = `sync, projections, stats, replacement, simulate, export`. The workflow file is unchanged (it runs `refresh`); `git add data` already covers the new directories. First-time setup in the README gains `python -m ffapp stats --backfill` and `python -m ffapp replacement`.

### 11. Tests and fixtures
A stats fixture `tests/fixtures/sleeper/stats/2025/1.json` cut from the live response to the players in the projections fixture plus a handful of free agents at each position, served by `FixtureSession` under `/stats/nfl/`. Drift estimation is tested on a synthetic two-season store where rosters drift by a known amount so the expected slope is known, and on the fixture season for shape. The floor is tested through `lineup_from_projections` with and without a floor dict.

### 12. Explaining the model on the calibration page
The export adds to each league file `replacement: {as_of_week, week, levels: {pos: projected}, season: {pos: value}, top_n}` from `data/replacement/<league>/<season>.json` (the level for the first unplayed week) and `model` from the latest odds payload, both omitted when the files are missing. The calibration page loads the league files it already knows from `index.json` and adds a "How the odds are made" card between the summary and the reliability chart, written for league members rather than for us:

1. **Projections** (Sleeper's weekly projections, scored with the league's rules).
2. **Noise** (how far real scores have missed projections in past seasons; the 80% range figure from the report as the proof it is the right width).
3. **Lineups** (best projected lineup each week; every slot worth at least a replacement-level player, defined as the average of the best N free agents by projection) with a small per-league table of this week's levels by position and the season values.
4. **Roster drift** (teams change; a lead today only partly survives) with a per-league line "a team 20 points better than average is expected to keep about X points two weeks out and Y twelve weeks out", computed from the exported slopes, and a one-line note of the drift noise.

The report meta's switches (floor on/off, drift on/off, N) join the existing "What was checked" meta line so a member can see the published calibration matches the live model. When the league files lack `replacement`/`model`, the card shows the explanation with the numeric tables replaced by one sentence saying the live numbers are not published yet. Text stays short (one or two sentences per step) and uses no model jargon beyond "replacement level", which the card itself defines.

## Risks / Trade-offs

- [The floor lets all twelve teams "pick up" the same three free agents] → acceptable: slots below replacement are a minority of lineups each week and the drift term absorbs residual churn; the diagnostic shows whether N = 3 over-corrects (slope above 1 would mean the floor is too generous).
- [Drift estimated from few seasons (four dynasty, five redraft) is noisy per horizon] → monotone smoothing across horizons, and the slopes come from 600–800 team-week pairs per horizon; leave-season-out replays show how much the estimate moves season to season.
- [Realised replacement level depends on stats being synced] → the simulation never needs it; the replacement file marks it absent rather than failing.
- [35 MB of stats in the repo] → one-off, same order as projections; weekly refresh changes only the current season's files.
- [Published odds shift when this ships] → expected and the point; the calibration page documents the before/after once `calibrate` is re-run and committed.
- [`gp`/`gms_active` ambiguity for "did not play"] → a missing stat row or no `pts_*` both count as 0 for realised level, and the free-agent count is recorded so thin positions are visible.

## Migration Plan

1. Merge; run `python -m ffapp stats --backfill` (about 100 requests, a few minutes with throttling) and `python -m ffapp replacement`; commit `data/stats`, `data/replacement`.
2. Run `python -m ffapp calibrate` three times: `--no-replacement-floor --no-roster-drift` (baseline, should reproduce the current report), `--no-roster-drift` (floor only), and the default. Compare the redraft playoff bins and the drift diagnostic; commit the default run's outputs.
3. Run `python -m ffapp simulate --backfill-season` and `export`, commit, push. Rollback: the switches are config/CLI level and the old odds files are in git history.
