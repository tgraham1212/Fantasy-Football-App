# Design

## Context

See proposal.md for motivation. What exists and shapes the approach:

- `simulate()` in `src/ffapp/simulate.py` already produces `SimResult.weekly_scores`: per simulated week a `(runs, teams)` array of drifted scores, for regular-season and playoff weeks. Lineups are built in `build_inputs` (`src/ffapp/odds.py`) as `starters[rid][week]`, with replacement fills as `Starter(slot, "FA:<pos>", pos, level)`. Odds payloads keep only per-team season chances.
- Playoff brackets run through `run_six_team_bracket` in `src/ffapp/bracket.py`, which returns every game with per-run team arrays (`t1`, `t2`) and the advancer; toilet bowls advance the lower scorer.
- `simulate --backfill-season` writes an as-of file for every week of the current season; the daily refresh rewrites only the latest as-of file. The as-of number is completed weeks (`last_scored_leg`), so it does not move during a week.
- Projection records drop the raw row's `date`. Sleeper's player list (already fetched daily by `snapshot` for the crosswalk) carries `injury_status`.
- The workflow runs on a daily cron with a `refresh-odds` concurrency group; the site is three sub-pages driven by `site/app.js` (`#league` / `#league/war` hash), with `site/war.js` as a separately loaded page module and every script carrying `?v=__BUILD__`.

## Goals / Non-Goals

**Goals:**
- Game forecasts come from the same simulation run as the season odds, so a card and the Predictions table never disagree.
- The prediction of record is reproducible from stored data alone.
- A run that the gate skips costs one small HTTP request and no commit.

**Non-Goals:**
- Using actual or in-progress results mid-week (change B). In this change a card during the weekend still simulates the whole week from projections, with locked players held at their pre-kickoff projection only in the log and the record.
- Games for past seasons.

## Decisions

**1. Game detail is computed inside `simulate_as_of`, stored in the as-of payload under `games`.** For each simulated week: per game, mean score, a histogram (2-point bins from the 0.5th to 99.5th percentile across both teams, counts normalised to shares, rounded to 4 decimals), win probability `mean(sa > sb) + 0.5 * mean(sa == sb)`, and each team's lineup from `inputs.starters`. Regular weeks iterate `inputs.schedule`. This adds roughly 60 bins × 2 teams × 6 games × up to 8 weeks per file, about 40 KB. Alternative: a separate simulation for games (rejected: two runs could disagree).

**2. Projected bracket from the existing bracket outcome.** `simulate()` gains a record of each bracket game's per-run pairings (from the `Game` objects the bracket already returns) and the projected bracket is built after the run: seeds by mean of `seeds` per team (expected seed), pairings from `BracketRules` with the same reseed logic applied to that single seeding, the favourite in each projected game decided by the head-to-head win probability from the two teams' simulated scores for that week (for a toilet bowl, the team more likely to score lower advances, matching `advance_loser`). Each projected game's frequency is the share of runs in which that unordered pair met in that round of that bracket. Alternative: the single most frequent bracket path (rejected: the most common full path can be very rare and inconsistent round to round).

**3. NFL schedule from ESPN's site scoreboard.** `GET https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?seasontype=<2|3>&week=<n>&dates=<season>` through the existing client plumbing (`SleeperClient.get_json`), parsed to `{games: [{home, away, kickoff_utc, state}]}` with ESPN abbreviations mapped to Sleeper's (`WSH`→`WAS`, `JAX`/`JAC` normalised, others identical). Stored at `data/nfl/<season>/week_NN.json`. Regular-season weeks 1–18 are seasontype 2; the league's playoff weeks 15–17 are still NFL regular season, so seasontype 3 is never needed. New module `src/ffapp/schedule.py`.

**4. The gate is a CLI command, `ffapp should-run`, used as the workflow's first real step.** It refreshes the schedule for the current and next week (from Sleeper `state`), reads `data/refresh/last_run.json`, and prints `run=true|false` to `$GITHUB_OUTPUT`. Rules per the spec: daily (the 11:00 UTC cron fire, detected by the event's schedule string) or manual → run; else a kickoff in the next 60 minutes or a game final since `last_run` → run, if `last_run` is at least 3 hours old. Later steps are conditioned on `run == 'true'`. The refresh writes `last_run.json` with its start time; it is committed with the data. Two cron entries: `0 11 * * *` (daily) and `20 * * * *` (hourly check). Alternative: query previous workflow runs through the GitHub API for spacing (rejected: needs a token scope and is slower than reading a committed file).

**5. Projection log and lock.** New module `src/ffapp/games.py`, run as a `games` step after `simulate`. For the current week and later weeks it takes the latest as-of payload's game forecasts, the stored projections, the rosters and the schedule, and appends to `data/games/<league>/<season>/week_NN.json` an entry per game: run time, both teams' model lineups and win probability, and every rostered player's projected points and `locked` flag (kickoff time at or before the run time). Entries are appended only when they differ from the previous entry for that game, ignoring the run time. A locked player's projection is copied from his last unlocked entry, never from newer projections.

**6. Prediction of record when a week is final.** When `last_scored_leg` reaches the week, `games` builds each team's record lineup from the week's matchup row: `starters` gives the players in slot order, each player's projection is his last logged unlocked value (else the stored projection for that week), and empty starter slots score 0. It then simulates those fixed lineups with the same noise model and the as-of-(week-1) drift for one week ahead, with a deterministic seed per league, season and week, and stores mean, histogram and win probability with the actual scores and winner from the matchup row. Weeks with no log entries use the as-of-(week-1) payload's game forecast, flagged `source: "pre-week"`; the backfill re-run of `simulate --backfill-season` populates those `games` blocks for 2026 weeks 1–10. A week's record is computed once and not recomputed unless forced, so later projection changes cannot move it.

**7. Injury statuses.** `snapshot` already fetches Sleeper's player list; it additionally writes `data/injuries/<season>/week_NN.json` (`{player_id: status}` for fantasy positions with a non-empty `injury_status`) for Sleeper's current week, overwriting that week only, during `regular` and `post` season types. Not-playing lists are computed at export: bye from the schedule (no game for the player's team), then the saved status if `Out`, `Doubtful` or `IR` (Sleeper's values `Out`, `Doubtful`, `IR`, `PUP`, `Sus` are mapped: `PUP` and `Sus` count as Out), then the inferred rule for weeks without a saved file.

**8. Key players and lineups.** At export, per team: the lineup's QB slot, then the highest-projected RB, the highest-projected WR, then the highest-projected remaining RB/WR/TE, all taken from the lineup actually used (model lineup for forecasts, real starters for records). Replacement fills render as "Free agent (replacement level)".

**9. Site.** A new `site/games.js` module, loaded like `war.js`, owns the page; `app.js` gains the third sub-tab and the `#<league>/games` hash. Export writes `site/data/<league>/games/index.json` (weeks with labels, the current week, and per week its kind: final, current, upcoming, projected-bracket) and `site/data/<league>/games/week_NN.json`. Distribution charts are small Chart.js line charts with filled areas at low alpha in owner colours and, for finished weeks, vertical annotation lines drawn with a tiny inline plugin (no new library). Playoff ordering: 1 seed's side first, then the 2 seed's side, then toilet bowl games. The win probability ramp comes from a new `--diverging` mode in `tools/team_palette.py`: neutral grey at 50% to green and red at the ends, generated per theme and checked with the dataviz validator, stored as CSS tokens and interpolated in OKLab like the chance cells.

**10. Refresh order.** `sync, projections, stats, schedule, snapshot, ratings, replacement, war, simulate, games, export`. `schedule` and `snapshot` are non-fatal (warning annotation) as `snapshot` is today; `games` is fatal.

## Risks / Trade-offs

- [GitHub's scheduler delays or drops cron fires, sometimes by 10–30 minutes on busy hours] → the trigger window is 60 minutes and the check runs at :20, so a delayed fire still lands before a 1 pm kickoff in most cases; the daily run backs everything up.
- [ESPN scoreboard changes shape] → strict parsing, non-fatal step, stored schedule kept; locks fall back to the projection's game date at 00:00 Eastern if no schedule is stored for the week.
- [The record simulates real starters, so it measures projection skill, not the model's lineup choice] → deliberate (agreed during exploration); the log keeps the model's own lineups.
- [More commits: up to ~6 extra runs a week] → acceptable; each commits only changed files.
- [Odds files grow ~40 KB] → acceptable; site data loads per week.
- [Pre-week fallback for 2026 weeks 1–10 uses projections stored today, which may include post-kickoff updates] → labelled as a pre-week forecast on the page.

## Migration Plan

1. Ship; run `ffapp simulate --backfill-season` once to add `games` blocks to the 2026 as-of files, then `ffapp games` and `ffapp export`.
2. The workflow's hourly check starts with the next push; the first injury save and log entries come from the next run.
3. Rollback: drop the hourly cron and the `games` step; stored files can stay.
