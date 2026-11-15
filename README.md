# Fantasy Football App

Playoff odds and league history for two Sleeper leagues. A Python job pulls each
league's history and Sleeper's player projections, simulates the rest of the
season 10,000 times, keeps a week-by-week odds history, and publishes a static
website. GitHub Actions runs it daily.

## Setup

Requires Python 3.12+.

```bash
pip install -e ".[dev]"
pytest
```

Tests never touch the network; they run against recorded Sleeper responses in
`tests/fixtures/`.

## Commands

All commands run as `python -m ffapp <command>`. (`pip install` also creates an `ffapp`
console script, usable as `ffapp <command>` when Python's Scripts directory is on your PATH.)
Global options: `--config PATH` (default `config/leagues.yaml`), `--data PATH`
(default `data/`), `--site-data PATH` (default `site/data/`), `-v` for debug logging.

| Command | What it does |
|---|---|
| `sync` | Pull every season of each configured league from Sleeper into `data/leagues/`. Seasons already stored as complete are skipped; `--full` re-fetches them. |
| `projections` | Refresh player projections for the current season (weeks 1-17), keeping only the newest version per player-week. `--backfill` fetches every season in scope. |
| `stats` | Refresh actual weekly stat lines for every projected player (free agents included) for the current season, keeping the newest version per player-week. `--backfill` fetches every season in scope. |
| `verify-brackets` | Check the bracket logic against every completed season's real playoff brackets. Exit 1 on any mismatch. |
| `simulate` | Run the Monte Carlo for the current as-of week of each league and store the results in `data/odds/`. `--backfill-season` also produces results for every earlier as-of week of the current season. `--runs N` and `--seed N` override the defaults. |
| `export` | Write `site/data/<league>.json` and `site/data/index.json` for the website. |
| `replacement` | Write replacement-level values (free agents, weekly projected and realised levels, season values) for every stored season to `data/replacement/`. |
| `refresh` | `sync`, `projections`, `stats`, `replacement`, `simulate`, `export` in order, stopping at the first failure with a non-zero exit. This is what the scheduled job runs. |
| `calibrate` | Replay every completed season through the simulation and score the odds against what happened (see Calibration). Not part of `refresh`. `--runs N`, `--seed N`, `--residual-scale X` evaluate a candidate scale without touching the config. |

First-time setup of a fresh clone, in order:

```bash
python -m ffapp sync
python -m ffapp projections --backfill
python -m ffapp stats --backfill
python -m ffapp replacement
python -m ffapp verify-brackets
python -m ffapp simulate --backfill-season
python -m ffapp export
python -m http.server 8000 -d site   # then open http://localhost:8000 (and /calibration.html)
```

## Configuration: `config/leagues.yaml`

```yaml
leagues:
  dynasty:
    league_id: "1339662153812025344"   # the CURRENT season's Sleeper league ID
    name: Taco Tuesdays
  redraft:
    league_id: "1389347876550770688"
    name: Chris Carter's Fall Guys
overrides: []
```

- Each key (`dynasty`, `redraft`) is a stable short name used in `data/` paths and
  on the website. Keep it the same across seasons.
- **Every new season, Sleeper creates a new league ID.** Replace `league_id` with the
  new one; earlier seasons are found automatically through Sleeper's
  `previous_league_id` chain, so history is never lost.
- `overrides` records scoring changes Sleeper did not keep (Sleeper stores only each
  season's final settings). Each entry replaces the listed scoring keys for one
  league-season from a given week onward:

  ```yaml
  overrides:
    - league: redraft
      season: "2023"
      from_week: 6
      scoring:
        fgm_yds: 0.1
  ```
- `simulation.residual_scale` (optional, default 1.0) multiplies every sampled score
  residual, widening (>1) or narrowing (<1) the simulated score noise. It exists so a
  calibration finding can be acted on; it is off unless set, and a value should only
  be adopted when the score-level coverage in the calibration report is off across all
  stored seasons. Try a candidate without editing the file:
  `python -m ffapp calibrate --residual-scale 1.1`.
- `simulation.replacement_top_n` (default 3): how many of the best-projected free agents
  are averaged to define the replacement-level player at each position, the floor every
  simulated lineup slot gets. `simulation.prior_weeks` (default 4): shrinkage weight, in
  weeks, toward earlier seasons for the season replacement value (see Replacement level).

## Data layout

Everything is plain JSON so it diffs well in git.

```
data/
  leagues/<league>/<season>/league.json        raw Sleeper league object (settings, scoring, status)
                            users.json, rosters.json
                            brackets.json       {"winners": [...], "losers": [...]}
                            matchups/week_NN.json
  projections/<season>/week_NN.json            {player_id: {position, team, opponent, company, last_modified, stats}}
  stats/<season>/week_NN.json                  same shape, actual stat lines for every player who played (free agents included)
  replacement/<league>/<season>.json           weekly replacement levels by position and the season values (see Replacement level)
  model/<league>.json                          roster-drift factors by weeks ahead, estimated from the stored seasons
  odds/<league>/<season>/asof_NN.json          one simulation result per as-of week (the odds history)
site/data/<league>.json, index.json            what the website reads
```

Projections are stored as raw stat lines and scored with each league's own
settings, so one copy serves both leagues. Records for played weeks are kept
forever and only replaced when Sleeper publishes a newer version.

## Replacement level

A replacement-level player is what a manager can pick up off the waiver wire. For
each league, season, week and position, `ffapp replacement` takes the N free agents
(default 3, `simulation.replacement_top_n`) with the highest projection for that
week, under the league's own scoring, and records two numbers:

- **projected level**: the mean of their projections (known before the games);
- **realised level**: the mean of the points those same players actually scored,
  from the stats store (absent until the week is played and its stats synced).

Free agents are the projected players on no roster in that league: for a stored
week, the rosters in that week's matchups; for the present and future, the current
rosters including IR and taxi. Choosing by projection and scoring afterwards keeps
the realised level honest; picking the top scorers after the fact would overstate
what a pickup is worth.

The **season value** per position is the mean of the realised weekly levels so far,
shrunk toward earlier seasons: `(n × mean + k × prior) / (n + k)` with `k =
simulation.prior_weeks` (default 4) and the prior a 50/30/20 weighted mean of the
last three seasons of that league with the same scoring and roster settings (the
first stored season uses its own mean projected level instead).

The simulation uses the projected level as a floor for every lineup slot (see
below). The files in `data/replacement/` are for inspection and for later features
such as value over replacement.

## How the simulation works

1. **As-of point**: the last week Sleeper has fully scored (`last_scored_leg`). A week
   with Thursday's game played but not yet scored counts as unplayed.
2. **Rosters**: current rosters minus IR and taxi squad (backfilled weeks use the
   roster each team carried into the following week).
3. **Lineups**: the best legal lineup by projected points, per week, using the
   league's roster slots (FLEX takes RB/WR/TE). Every slot is worth at least that
   week's replacement level for its position (`simulation.replacement_top_n` best
   free agents by projection, averaged), standing in for the pickup a manager would
   make for a bye, an injury or a thin bench.
4. **Noise**: each simulated player score is the projection plus a residual drawn
   from the history of actual-minus-projected points for that position and
   projection band, across both leagues' stored seasons.
5. **Roster drift**: real rosters change, so a team's edge today only partly
   survives. For each league the stored seasons give how much of a team's projected
   edge over the league mean remains k weeks ahead (a reversion factor) and how much
   random drift accumulates. Each simulated week shrinks every team by that factor and
   adds a per-run drift that persists from week to week. The factors live in
   `data/model/<league>.json` and in every odds result under `model`.
6. **Season**: remaining weeks on the real schedule, standings by wins (ties =
   half) then points, 6-team playoffs with two byes and a losers bracket, following
   each league's Sleeper settings (`playoff_seed_type` = re-seeding,
   `playoff_type` = consolation vs toilet bowl). `verify-brackets` proves these rules
   reproduce every completed season.
7. **Outputs** per team: projected record and the chance of making the playoffs, a
   first-round bye, the final, the title, the losers bracket, and last place.

## Calibration

`python -m ffapp calibrate` replays every stored season with status complete (dynasty
2022-2025, redraft 2021-2025) as of every week from preseason to the last playoff
round, using the production simulation and score noise learned from the *other*
seasons only. The replay odds are stored in `data/odds/<league>/<season>/` like the
live ones, and the comparison with real results is written to
`data/calibration/report.json` and `data/calibration/report.md` (plus per-season rows
under `data/calibration/rows/`). The run takes about a minute.

The report answers three questions, from most to least data:

1. **Score level** (about 1,500 team-weeks): is the noise the right width? Each real
   team score is placed within its simulated distribution for that week. If the noise
   is right, the percentile histogram is flat and the 50/80/95% ranges contain the real
   score 50/80/95% of the time. Piles at the ends mean too narrow; a hump in the middle
   means too wide. This is the figure that justifies touching `residual_scale`.
2. **Game level** (about 750 games): are next-week win chances right? Favourites shown
   at 60-70% should win 60-70% of the time.
3. **Season level** (108 team-seasons): are the published playoff, bye, final, title,
   losers-bracket, last-place and bottom-two chances right, and are they better than a
   naive standings baseline? Reliability bins show "teams shown at X% got there Y% of
   the time"; the Brier score and the skill against the baseline summarise it. Rows
   after an outcome is decided are left out.

It also measures the **lineup gap**: how many points the best projected lineup would
have added to the lineup each manager actually started, and reports the **roster drift
diagnostic**: for each league and horizon, how well a team's projected strength
predicts its true strength that many weeks ahead (slope and residual noise), under
the frozen roster and under the replacement-floored roster. A floored slope near 1
means the floor removes most of the frozen-roster bias; it is also the evidence for
choosing `replacement_top_n` (the repo config uses 5 on that evidence). `--no-replacement-floor` and `--no-roster-drift` replay
without one piece so each can be measured alone; the report records the switches.

The optional knob `simulation.residual_scale` is deliberately off by default. Change it
only when the score-level coverage is off across all seasons and both leagues, never to
make one season's playoff bins look better: nine seasons give about five usable bins
with roughly ±5 points of noise each. Try a value first with
`python -m ffapp calibrate --residual-scale 1.1`, which leaves the config alone and
records the scale it used in the report.

Commit `data/odds`, `data/calibration` and `site/data` after a run; the next deploy
publishes the calibration page.

## Website

`site/` is static: `index.html`, `styles.css`, `app.js`, a pinned copy of Chart.js
in `site/vendor/`, and the exported data. It is deployed to GitHub Pages by the
workflow. URL options: `#dynasty` / `#redraft` picks the league, `?team=<roster_id>`
highlights a team, `?metric=playoffs|bye|title|avoid_losers_bye|last` picks the
chart, `?theme=dark|light` forces a theme.

The odds table follows the FiveThirtyEight layout: ELO and 1-week ELO change
(empty until the ELO feature ships), owner with team name and record, projected
record, then four chance columns filled on a white-to-blue ramp. The first chance
column depends on the league: a toilet-bowl league shows **Avoid Loser's Bye**
(finishing outside the bottom two), a dynasty league with a consolation bracket
shows **#1 Pick** (finishing last). The export decides this from Sleeper's
`playoff_type` and `type` settings (`bottom_column` in `site/data/<league>.json`).
Rows start in standings order; clicking a header sorts descending, clicking again
ascending. Hovering a chance shows its change since the previous week. Each team
has a fixed colour (the dot beside the owner name) that matches its line in the
chart; the palette comes from `tools/team_palette.py`.

`calibration.html` ("How good are these odds?", linked from the header) shows the
calibration report: predicted-vs-observed reliability per outcome, the score-noise
percentile histogram and interval coverage, head-to-head win-chance bins, the lineup
gap and the caveats. The export copies `data/calibration/report.json` to
`site/data/calibration.json`; without one the page says calibration has not been run.
It only changes when `calibrate` is re-run and its outputs committed.

After `git pull`, run `python -m ffapp export` before opening the site locally:
`site/data/` is whatever the last export wrote, and an older export may lack
fields the page expects.

## Scheduled job

`.github/workflows/refresh.yml` runs daily at 11:00 UTC (after Monday night's game
is scored) and on demand. It runs the tests, `python -m ffapp refresh`, commits
`data/` and `site/data/` if anything changed, and deploys `site/` to GitHub Pages.
A failure at any step ends the run before the commit and deploy, so the published
site keeps its last good state. GitHub Pages must be set to deploy from **GitHub
Actions** in the repository settings.
