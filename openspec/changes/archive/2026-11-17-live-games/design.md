# Design

## Context

See proposal.md for motivation. What change A left in place and this change builds on:

- `simulate()` scores every starter as `projected + noise.sample(position, projected)`; `Starter` is a frozen dataclass `(slot, player_id, position, projected)`. Lineups come from `lineup_from_projections` → `best_lineup(slots, candidates)` with the replacement floor applied per slot.
- The live week's real lineup and per-player points are already synced every run: Sleeper's matchup rows for the current week carry `starters` (slot order = `starter_slots(league)`) and `players_points` in league scoring.
- Drift for one week ahead is identity (slope 1.0, step sd 0), so the live week needs no drift change.
- `run_as_of` writes `data/odds/<league>/<season>/asof_NN.json` and is re-run every refresh for the current as-of week; `games.update_games` reads that payload's `games`; the export reads the latest as-of file.
- The schedule feed stores state only; ESPN's scoreboard also sends `period`, `displayClock` and per-competitor `score`.
- Residual pools are not centred: a pool's mean is the projection bias at that position and band.
- Node 22 is installed locally, so the Worker can be tested with `node --test`.

## Goals / Non-Goals

**Goals:**
- One code path: the live week flows through the same `simulate()` as every other week, so season odds and game cards agree.
- Look-backs never see live data: frozen as-of files, the log's pre-kickoff projections and the prediction of record are untouched by live runs.
- The site never depends on the relay.

**Non-Goals:**
- In-game injury or benching detection (backlog).
- Calibration of live odds (calibration replays stay pre-week).

## Decisions

**1. `Starter` gains `fixed: float = 0.0` and `share: float = 1.0`.** `simulated_scores` scores each starter as `fixed + share * (projected + bias) + sqrt(share) * (residual - bias)`, where `bias` is the mean of the residual pool for that position and band. With the defaults this is exactly today's `projected + residual`, so every existing caller and the calibration replays are unchanged. A final player is `fixed = actual, share = 0`; in progress `fixed = so far, share = minutes left / 60`. The noise models gain `bias(position, projected)` and `sd(position, projected)` (pool mean and standard deviation times `scale`; Gaussian: 0 and `sd`).

**2. `src/ffapp/live.py` builds the live week's lineups.** Inputs: the matchup rows for week `as_of + 1`, the stored schedule (now with quarter, clock and scores), projections and scoring. For each team: walk `starter_slots` with the row's `starters`; a starter whose NFL team has kicked off becomes a locked `Starter` with `fixed` from `players_points` and `share` from the clock; other slots are open. Open slots are filled by `best_lineup(open_slots, candidates)` over rostered players whose games have not kicked off and who are not locked starters, then the replacement floor as before. `build_inputs` takes an optional `live` argument and uses these lineups for the live week only. Share left: `((4 - quarter) * 15 + clock_minutes) / 60` for quarters 1-4, 1.0 when scheduled, 0 for final, overtime or a missing clock.

**3. The live decision and files.** `simulate_league` computes `live = schedule says week as_of + 1 has a kicked-off game at run time`. When live, `run_as_of` writes `live.json` beside the as-of files (same payload shape plus `live: {week, games_final, games_total, generated_at}`) and does not touch `asof_NN.json`. When not live, it writes `asof_NN.json` as today and deletes `live.json` if it belongs to an earlier as-of week. Backfill and calibration never use live mode.

**4. Game forecasts for the live week carry per-starter live state.** `forecast.game()` adds to each lineup row `[slot, pid, position, projected, status, points, clock]` when the inputs mark a starter locked (status `final` or `in_progress`), and to each team `points_so_far` and `to_play` (starters not yet kicked off). Unlocked rows stay four fields. `games.update_games` reads `live.json` when it exists, so the log keeps appending during the weekend; locked players' projections stay frozen at their pre-kickoff values as in change A.

**5. Win probability added is computed in `games.py`, from a pre-kickoff baseline.** For a final week the baseline is the prediction of record; the record gains the margin's mean and standard deviation for team A (`margin_mean`, `margin_sd`, from the same 10,000 runs). For the live week, each run simulates a provisional baseline the same way as the record: the manager's current starters, each at his last logged pre-kickoff projection (current projection for players not yet locked), stored as `baseline`. For each starter with a score: `p0 = Phi(m / s)`, `m' = m ± (score - projected)` (sign by side), `s' = sqrt(max(s^2 - sd_i^2 * (1 - share_i), 1e-9))` with `sd_i` from the noise model, `wpa = Phi(m' / s') - p0`, from that player's team's point of view. In-progress players use `score = so far + share * projected` and keep `share * sd_i^2` of their variance. Stored per starter on the week file as `wpa`, rounded to 3 decimals. Pre-week records (2026 weeks 1-10) use the pre-week forecast's margin and the starter's stored projection; the export notes the source.

**6. Schedule fields.** `parse_scoreboard` adds `quarter` (ESPN `status.period`), `clock` (`status.displayClock`), `home_score`, `away_score` (ints). Existing files without them read as missing, which the share-left rule treats as no time left only for in-progress games.

**7. Predictions page.** The export reads `live.json` when present: the league file's `teams` come from it, `live` is copied to the payload, `previous_as_of_week` is the frozen as-of week, and the history series are built from as-of files only. The page's freshness line becomes "Live: N of M games final · updated …" while live.

**8. Relay: a Cloudflare Worker in `relay/`.** `relay/worker.js` (ES module, no dependencies) with `GET /status` and `POST /refresh`, both CORS-limited to the configured site origin. Cooldown source of truth is GitHub itself: list the workflow's runs created in the last 15 minutes (`GET /repos/{repo}/actions/workflows/refresh.yml/runs?created>=…`), and for each fetch its jobs; a run counts when its `refresh` job is queued, in progress or completed without being skipped, or when the run is a `workflow_dispatch` (queued manual runs have no jobs yet). Start time = the `refresh` job's `started_at`, else the run's `created_at`. `POST /refresh` re-checks, then calls `POST /repos/{repo}/actions/workflows/refresh.yml/dispatches` with `ref: main`. Configuration via Worker secrets/vars: `GITHUB_TOKEN` (fine-grained, this repository only, "Actions: read and write"), `REPO`, `SITE_ORIGIN`. Tested with `node --test` against a fake `fetch`. Alternative considered: a KV store for the last click (rejected: GitHub already knows about every run, including scheduled ones).

**9. Button and config.** `config/leagues.yaml` gains an optional `site: {refresh_url: …}` block (validated like the others); the export copies it and the last successful refresh time (`data/refresh/last_run.json`) into `site/data/index.json`. `app.js` and `calibration.js` render the button only when `refresh_url` is set, poll `/status` on load and every minute, and fall back to "Updated N min ago" from the data when the relay is unreachable. A short `relay/README.md` covers: create the token, create the Worker, set the secrets, deploy with `npx wrangler deploy`, put the URL in the config.

**10. Live badge.** Inline SVG (dot + two arc pairs) with a `linearGradient` on the arcs animated by CSS (`@keyframes` on a gradient offset), neon green from a new `--live` token per theme, the dot `--bad`. `@media (prefers-reduced-motion: reduce)` stops the animation. Status colours: in progress `--good` with a dot, final `--ink` bold with "F", scheduled `--muted`.

## Risks / Trade-offs

- [Daily and hourly runs land between scoring plays, so "live" is minutes to hours old] → the freshness line says when; the manual refresh exists for that.
- [Sleeper's per-player points and ESPN's clock come from different feeds and can disagree briefly] → points come from Sleeper only; the clock only sets the share left.
- [A starter on bye or inactive with 0 points and a kicked-off team counts as final 0] → correct: that is his real score.
- [The relay's GitHub calls per page view] → `/status` makes at most a few API calls; well under the token's 5,000 an hour for a league-sized audience, and Cloudflare's free tier allows 100,000 requests a day.
- [Win probability added uses a normal approximation of the margin] → matches the WAR method; numbers show size, not exact shares, as the page says.
- [Live odds are less tested than the pre-week model] → they reduce to the pre-week model when nothing has kicked off, which tests pin down.

## Migration Plan

1. Ship code; the first run after a kickoff writes `live.json`; nothing to backfill.
2. Optional: follow `relay/README.md` to deploy the Worker and add its URL to the config; the button appears on the next deploy.
3. Rollback: delete `live.json` and redeploy; the site falls back to as-of files.
