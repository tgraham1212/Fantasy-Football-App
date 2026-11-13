# Design

## Context

The repo is brand new: OpenSpec scaffolding only, no application code. See proposal.md for the motivation. Facts that shape the approach, checked against the live APIs on 2026-11-13:

- **Leagues:** dynasty `1339662153812025344` has seasons 2022-2026. Redraft `1389347876550770688` has seasons 2021-2026; 2021-2023 were keeper (`type` 1), redraft since 2024. Both have 12 teams, a 14-week regular season, and 6-team playoffs in weeks 15-17 with 2 byes and a 3-round losers bracket. Neither has divisions or a median game. Trade deadline is week 11 in both.
- **Lineups:** dynasty is QB/2RB/2WR/TE/FLEX/DEF, with 10 bench, 1 taxi and 2 IR slots. Redraft is QB/2RB/2WR/TE/FLEX/K/DEF, with 5 bench and 1 IR slot. Both are half PPR.
- **Seeding setting:** `playoff_seed_type` is 1 in dynasty and 0 in redraft. Its meaning isn't documented. It probably decides whether seeds are re-ordered after round 1.
- **Settings archive:** stored scoring settings are identical across every season in both leagues. Sleeper keeps only the end-of-season snapshot. Actual kicker scores confirm incremental scoring was already in place from 2021 week 1.
- **Projections:** `GET https://api.sleeper.com/projections/nfl/{season}/{week}?season_type=regular&position[]=QB&...` returns about 3,300 rows per week, about 400 with real projections, about 2 MB. Rows hold a full stat line (`stats`), `player_id`, `team`, `opponent`, `company` (currently `rotowire`) and `last_modified`. Past weeks return data, but `last_modified` falls after the games (the latest version, not pregame). Future weeks are already populated.
- **Actual points:** `GET /v1/league/{id}/matchups/{week}` returns `players_points` for every rostered player, plus `starters`, `starters_points`, `points` and `matchup_id`.
- **Sleeper state:** `GET /v1/state/nfl` shows `week: 10` for 2026. The league's `settings.last_scored_leg` is 9.

## Goals / Non-Goals

**Goals:**
- One Python pipeline, run by one command, that syncs, refreshes projections, simulates and exports. It runs the same on a laptop as in GitHub Actions.
- A pure, well-tested simulation core: data in, odds out, no network calls.
- Stored data that is easy to inspect and that grows the repository slowly despite daily commits.
- The projections source sits behind a narrow interface so it can be swapped later.

**Non-Goals:**
- Modeling roster moves, players on the same NFL team scoring together, or game-day injury news within a week.
- Using live scores from a week in progress.
- Simulating past seasons. The odds history covers the current season only. The data model allows past seasons later.
- Accounts, server-side code, or a hosted database.

## Decisions

### 1. Stored data: per-partition JSON files in the repo, not one committed SQLite file
Stored data lives as plain JSON files under `data/`, split so that each refresh changes only a few small files:

```
data/
  leagues/<league_key>/<season>/league.json      settings, status
                               /users.json, rosters.json
                               /matchups/week_NN.json
                               /brackets.json      winners + losers
  projections/<season>/week_NN.json              { player_id: {stats, team, opponent, company, last_modified} }
  odds/<league_key>/<season>/asof_NN.json        per-team results + metadata
config/leagues.yaml                              league keys, current IDs, overrides
```

**Why:** git stores a full new copy of a binary file every time it changes. A SQLite file of about 20 MB (6 seasons × 17 weeks × about 400 projected players, plus history), committed daily, would add gigabytes per season. With per-week JSON, a daily refresh touches about 8 future-week projection files plus a few current-season files. Git packs those as small text deltas. Completed seasons never change again.
**Alternatives:** a single SQLite file in the repo (simplest to query, but bloats history). A hosted Postgres or Turso database (removes bloat, but adds an outside service and secrets, which v1 doesn't need). SQLite can still be built from these files at runtime later, when the stats features need ad-hoc queries.

### 2. Projection upsert compares `last_modified`
Each refresh fetches weeks 1-17 of the current season. For each player row that has a non-empty stat line, the stored record is replaced only when the incoming `last_modified` is newer. Rows with no stats (about 2,900 per week) are dropped. A week the source returns empty for leaves its stored file untouched. A historical backfill runs the same code once for every season from 2021 on.
Responses are checked before anything is written: they must be a list, and each row must have `player_id`, `week`, `season` and a `stats` object. A failed check aborts the projections step without writing anything.
**Alternative:** append-only snapshots. Rejected by the user, who wants only the latest version.

### 3. Scoring: stat line × resolved settings
`resolve_settings(league_key, season, week)` returns Sleeper's stored `scoring_settings` for that league-season, with any `config/leagues.yaml` overrides layered on top where `from_week <= week`. Projected points are the sum of `stats[k] * scoring[k]` over keys present in both. Precomputed `pts_*` keys are ignored, so custom scoring works. DEF points-allowed brackets (`pts_allow_*`) and yardage brackets are already projected as fractional bucket probabilities, so the same dot product applies.
**Check:** for a sample of completed weeks, scoring the stat lines should land close to Sleeper's own precomputed points for a standard format. A unit test with a fixture covers kicker field-goal-yard math.

### 4. As-of point and completed weeks
`as_of = min(league.settings.last_scored_leg, 14)` for the regular season. A week counts as complete only when Sleeper has scored it, so partial weeks are never used (see spec). During the playoffs, as-of becomes 15 or 16, and finished bracket rounds are read from stored brackets.

### 5. Rosters for each as-of point
- **Current run:** `rosters.json` `players` minus `reserve` and `taxi`.
- **Backfilled run as of week N:** the `players` list from the week-(N+1) matchup for that roster. Matchups include each team's full roster at that week, so this is the roster the team actually carried into the next week. As of week 0, that means the week-1 roster, right after the draft.
- Backfilled rosters can't always separate IR and taxi players. Those players project 0 points or fall to the bench through lineup selection anyway, so the error is negligible.

### 6. Lineup: greedy by projection, deterministic per week
For each team and week: fill the fixed slots (QB, RB, WR, TE, K, DEF) with the highest-projected eligible players, then fill FLEX from the remaining RB/WR/TE players. Greedy is optimal for these slot types because FLEX is a superset of positions filled earlier. The lineup is chosen once per week from mean projections, not per simulation run. That matches how managers actually set lineups and keeps the sim vectorized.

### 7. Noise model: empirical residual pools
Residual pairs are built from every completed league-season week across both leagues: residual = `players_points[player]` − that player's projected points in the same league that week. They're bucketed by position × projected-points band (0-2, 2-5, 5-8, 8-11, 11-14, 14-18, 18-22, 22+). A band with fewer than 200 samples falls back to that position's whole pool. Each simulated score is the projection plus a residual sampled from the pool. Because the pools are empirical, they naturally include zeros from injuries, the floor and right-skew; nothing normal-shaped is forced.
Residuals use backfilled (post-game, latest-version) projections, so variance is slightly understated. That's an accepted trade-off; see Risks.
**Alternatives:** a normal distribution with σ per position (allows negative scores and misses skew), or team-level score history only (ignores roster strength, which the user rejected).

### 8. Simulation engine: NumPy, vectorized over runs
Per league and week, draw a residual matrix of shape (runs × starters) per team and sum it into team scores. Standings are tallied vectorized across 10,000 runs, sorted by (wins + 0.5 × ties, points scored), and the brackets are run on the resulting seed arrays. A `numpy.random.Generator` with an explicit seed (default: hash of league, season and as-of) makes results repeatable. A mid-season run for 5 regular weeks plus 3 playoff rounds is a few hundred thousand draws per league, well under a minute in CI.

### 9. Bracket logic is driven by the history check
Implement the 6-team bracket with two modes, fixed and re-seed. Add a `verify-brackets` command that, for every completed league-season, computes final regular-season seeds from stored matchups and compares produced pairings with stored `winners_bracket`/`losers_bracket`. Mapping `playoff_seed_type` (0 and 1) to a mode, and the losers-bracket pairing rules, are settled empirically by this check during implementation. The bracket code must pass it for all 9 completed league-seasons before the sim is trusted. The 2025 dynasty bracket shows seed 1 meeting the winner of the 3-vs-6 game in round 2; that's the first test case.

### 10. Pipeline commands
A single CLI (`python -m ffapp <command>`):
- `sync`: league history (complete seasons skipped unless `--full`)
- `projections`: refresh the current season (`--backfill` for all seasons)
- `simulate`: current as-of for each league (`--backfill-season` for as-of weeks 0..current)
- `verify-brackets`
- `export`: write `site/data/*.json`
- `refresh`: runs `sync → projections → simulate → export` in order and stops at the first failure

### 11. Website: plain static HTML/CSS/JS plus Chart.js, on GitHub Pages
`site/` holds `index.html` (league switcher, odds table, chart), a small vanilla JS module and a pinned copy of Chart.js. `export` writes `site/data/<league_key>.json` with the current table, history series and freshness metadata. No build step.
**Alternatives:** Astro or React with a bundler. More capable, but adds a toolchain v1 doesn't need. Easy to switch to later because the data contract (the exported JSON) stays the same.

### 12. Scheduled job: GitHub Actions
`.github/workflows/refresh.yml`:
- Triggers: `schedule` daily at 11:00 UTC, so the Tuesday run comes after Monday night's game, plus `workflow_dispatch`.
- Steps: run `refresh`; if it succeeds, commit changes under `data/` and push; then deploy `site/` to Pages with `actions/deploy-pages`.
- `concurrency` stops runs from overlapping. Any step failure ends the job before commit and deploy, so the published site and committed data stay as they were.

### 13. Project layout and tooling
`pyproject.toml` (Python 3.12+, dependencies `requests`, `numpy`, `pyyaml`; dev `pytest`), `src/ffapp/` (modules: `sleeper`, `store`, `projections`, `scoring`, `lineup`, `noise`, `simulate`, `bracket`, `odds`, `export`, `cli`), and `tests/` with recorded API responses in `tests/fixtures/`. Tests never call the network.

## Risks / Trade-offs

- [The undocumented projections endpoint changes or disappears] → Response checks abort without writing. Stored projections persist. The source sits behind one function, so a replacement can plug in later.
- [Backfilled projections are post-game versions, so residual variance is understated and the odds come out slightly overconfident] → Accepted for v1. Later, the gap can be measured with odds calibration once enough seasons are stored.
- [Backfilled odds for 2026 weeks 0-9 use post-game projections, so they look a little too accurate] → Accepted for a trend chart, as the user agreed. Odds from now on are saved as they're made.
- [Frozen rosters ignore waiver pickups and trades, so long-range odds are too sure for teams that will churn their rosters] → Documented non-goal. The odds update daily as rosters change.
- [`playoff_seed_type` or losers-bracket rules interpreted wrong] → The `verify-brackets` check against 9 completed seasons must pass before results go out.
- [Mid-season scoring changes Sleeper didn't keep] → The `config/leagues.yaml` overrides cover this. None are known today; the kicker change predates the stored history.
- [Repository growth from daily commits] → Per-week JSON partitions (Decision 1). Completed seasons never change again.
- [Hitting Sleeper's rate limit, documented as under 1,000 calls per minute] → A routine sync makes about 40 calls. The full backfill makes about 300, throttled to about 5 per second.
- [The redraft league ID changes every season] → History is followed through `previous_league_id`. The user updates one ID in `config/leagues.yaml` each year; data is stored under a stable `league_key`.

## Migration Plan

Greenfield, so nothing to migrate. Rollout:
1. Run `sync --full` and `projections --backfill` locally and commit the initial `data/`.
2. Run `verify-brackets` until it passes, then `simulate --backfill-season` for 2026.
3. Enable the workflow and GitHub Pages.

Rollback: disable the workflow. The last good site stays published.

## Open Questions

- Exact chart colors and whether to label lines directly. Settled while building the page; doesn't affect the data contract.
- Whether to add a calibration report (predicted vs. actual playoff rates) once more seasons of odds history exist. That's a future change.
