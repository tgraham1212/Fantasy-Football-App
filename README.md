# Fantasy Football App

Playoff forecasts and league history for two Sleeper leagues. A Python job pulls each
league's history and Sleeper's player projections, simulates the rest of the
season 10,000 times, keeps a week-by-week forecast history, and publishes a static
website at https://fantasyfoosball.net. GitHub Actions runs it daily.

## Setup

Requires Python 3.12+.

```bash
pip install -e ".[dev]"
pytest
```

The browser layout check in `tests/layout/` skips unless Playwright is installed
(`pip install -e ".[dev,browser]"`, see Layout check). Tests never touch the network; they run against recorded Sleeper responses in
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
| `export` | Write `site/data/<league>.json`, `site/data/index.json` and the per-league Games, Positions and Player WAR files for the website. |
| `replacement` | Write replacement-level values (free agents, weekly projected and realised levels, season values) for every stored season to `data/replacement/`. |
| `ratings` | Rate every manager across all stored seasons from weekly points (see Manager ratings) and write `data/ratings/<league>.json`. |
| `snapshot` | Capture ESPN start-percentage snapshots (one per stored season that has none, the in-progress season again on every run until it is complete, plus the current regular-season week) and the ESPN-to-Sleeper player crosswalk into `data/espn/`, then report any widely started player the crosswalk could not match. |
| `schedule` | Store the NFL schedule (kickoff times, game states, byes) from ESPN's public scoreboard for the current and next week into `data/nfl/`; `--all` stores every week of the season. |
| `games` | Update this season's game files: a log entry per game of the current week and the forecast of record for weeks that have finished in `data/games/`, and the latest forecasts and lineup views in `data/games-derived/` (see Games). `--force-records` recomputes every record. |
| `war` | Compute every player's Wins Above Replacement for every stored league-season (see Player WAR) and write `data/war/<league>/<season>.json`. |
| `refresh` | The cold run: `sync`, `projections`, `stats`, `schedule`, `snapshot`, `trending`, `ratings`, `replacement`, `war`, `simulate`, `slates`, `games`, `export` in order, stopping at the first failure with a non-zero exit, except that a failed `schedule`, `snapshot` or `trending` is skipped with a warning so the odds never depend on ESPN. `--mode live` skips the simulation and the slate forecasts (the hot runs own the live forecast); the relay passes the mode (see Refresh modes). |
| `build` | Rebuild every derived file (ratings, replacement levels, WAR, odds, game views and `site/data/`) offline from the committed records. Run it after cloning or pulling, before opening the site locally. |
| `hot` | The hot run: this week's live scores, forecast and game cards as one bundle file (`--out PATH`, plus `PATH.meta` for the relay), built on a scratch copy so `data/` never changes (see Refresh modes). |
| `site-hash` | Print a hash of `site/` that ignores refresh times; the cold run deploys only when it changes. |
| `hold-tallies` | After `git add data`, unstage trending and ESPN percentage files already committed today (UTC), so git keeps one copy a day. |
| `calibrate` | Replay every completed season through the simulation and score the forecasts against what happened (see Calibration). Not part of `refresh`. `--runs N`, `--seed N`, `--residual-scale X` evaluate a candidate scale without touching the config. |

First-time setup of a fresh clone, in order:

```bash
python -m ffapp sync
python -m ffapp projections --backfill
python -m ffapp stats --backfill
python -m ffapp schedule --all
python -m ffapp snapshot
python -m ffapp ratings
python -m ffapp replacement
python -m ffapp war
python -m ffapp simulate --backfill-season
python -m ffapp games
python -m ffapp verify-brackets
python -m ffapp simulate --backfill-season
python -m ffapp export
python -m http.server 8000 -d site   # then open http://localhost:8000 (and /calibration.html)
```

After cloning or pulling an existing checkout, `python -X utf8 -m ffapp build` is enough:
`site/data/` and the other derived files are not in git (see Data layout), and the build
rebuilds them offline from the committed records.

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
- `ratings` (optional block, see Manager ratings): `revert` (default 1/3) is how far each
  rating mean moves back toward 1000 every preseason; `early_k` (default
  `[2, 1.75, 1.5, 1.25]`) multiplies the rating change in the first rated weeks of a
  season; `start_mu` / `start_sigma` (1000 / 333.3) are every manager's starting rating
  and uncertainty; `ewma_weight` (0.2) is the newest week's weight in the background
  exponentially weighted z-score. The same values apply to every league.

## Data layout

Everything is plain JSON so it diffs well in git. Only records are committed, and only when
they change; derived data is rebuilt by every run, carried between runs in a GitHub Actions
cache and never committed (it is in `.gitignore`). Which folder is which, what rebuilds each
derived one and what reads it: [`docs/refresh-modes.md`](docs/refresh-modes.md), "Where Data
Lives". `tests/test_storage_tiers.py` keeps the two in step.

```
data/
  leagues/<league>/<season>/league.json        raw Sleeper league object (settings, scoring, status)
                            users.json, rosters.json
                            brackets.json       {"winners": [...], "losers": [...]}
                            matchups/week_NN.json
  projections/<season>/week_NN.json            {player_id: {position, team, opponent, company, last_modified, stats}}
  stats/<season>/week_NN.json                  same shape, actual stat lines for every player who played (free agents included)
  projections-future/<season>/week_NN.json     weeks after the current one (rebuilt, not committed)
  replacement/<league>/<season>.json           weekly replacement levels by position and the season values (rebuilt; see Replacement level)
  model/<league>.json                          roster-drift factors by weeks ahead, estimated from the stored seasons (rebuilt)
  ratings/<league>.json                        every manager's rating history by week (rebuilt; see Manager ratings)
  espn/<season>/season.json                    ESPN start/roster percentages, one frozen snapshot per season (see Player WAR)
  espn/<season>/week_NN.json                   the same, captured weekly from the 2026 season on
  espn/crosswalk.json                          Sleeper's player list trimmed to id, ESPN id, name and position
  war/<league>/<season>.json                   every player's WAR for that league-season, with the weekly detail (rebuilt)
  nfl/<season>/week_NN.json                    NFL games for the week: teams, kickoff (UTC), state, final scores, byes (ESPN scoreboard)
  nfl-live/<season>/week_NN.json               the same with the fetch time and live clocks and scores (rebuilt)
  injuries/<season>/week_NN.json               {player_id: Sleeper injury status} as last seen during that week
  games/<league>/<season>/week_NN.json         per game: the projection log and the forecast of record
  games-derived/<league>/<season>/week_NN.json the latest forecast, lineup views and live baseline (rebuilt)
  odds/<league>/<season>/asof_NN.json          one simulation result per as-of week (the forecast history)
  odds/<league>/<season>/slates_NN.json        the live forecast as each slate of week NN went final
  odds/<league>/<season>/live.json             the latest live forecast (rebuilt)
  refresh/                                     last run time, schedule summary, site hash (rebuilt)
site/data/<league>.json, index.json            what the website reads (rebuilt)
site/data/<league>/positions/<season>.json     positional rankings per season, plus positions/index.json (see Positional Rankings)
```

Projections are stored as raw stat lines and scored with each league's own
settings, so one copy serves both leagues. Records for played weeks are kept
forever and only replaced when Sleeper publishes a newer version.

## Replacement level

`ffapp replacement` records, per league, season, week and position, what a waiver-wire
pickup is worth: the best free agents by projection that week (their projected and realised
levels) and a season value shrunk toward earlier seasons. The simulation uses the projected
level as the floor for every lineup slot. Files: `data/replacement/<league>/<season>.json`.
How it is calculated: `Calculations.txt`, section 14 (Replacement level).

## Manager ratings

`ffapp ratings` rates every manager across the whole life of a league, for the rating chart
and the ELO columns on the site: each scored regular-season week is a free-for-all ranked by
points, rated with Openskill on a 1000 scale, with a preseason pull back toward 1000 and a
faster start to each season, plus weekly and career z-scores. Ratings follow the manager's
Sleeper user ID; a vacant roster counts for its last earlier owner. How it is calculated:
`Calculations.txt`, section 15 (Manager ratings).

`data/ratings/<league>.json` holds the parameters, the list of weeks and, per
manager, their display name, current/former/vacant flags, seasons played and a
history entry per rated week (`mu`, `sigma`, `z`, `career_z`, `season_z`, `ewma_z`,
`fresh_mu`, values after that week's update). Once a season's draft is done (Sleeper
status `in_season` or `complete`), every member also gets a week-0 entry holding the
rating they enter the season with: the reverted mean, or 1000 for a newcomer, with no
weekly z. Re-running on unchanged data gives the same file. The export puts the latest
`mu` in the table's ELO column (so the reverted rating shows from the draft until week
1 is scored, with an empty change cell), the change over the last rated week beside
it, and the `mu` and `career_z` series for every current and former manager under
`ratings` in the league's site file; the chart draws the preseason point as "Pre".

The defaults came from a replay of the stored seasons (2021/2022 to 2026). The
ratings are a display of career skill, not a forecaster: in the redraft league, where
rosters reset every year, last season's rating says little about week 1, which is why
the chart keeps a continuous career line rather than trying to predict.

## Player WAR

`ffapp war` values every Player's season in Wins Above Replacement for each league, following
the Stathole Sports method: consensus lineups and a replacement cut drawn from ESPN start
percentages (`ffapp snapshot` stores them under `data/espn/`, mapped to Sleeper ids through a
crosswalk and a short alias table in `src/ffapp/espn.py`), the league's own scoring and slots,
and a win probability against a typical opponent. A season uses the weekly, yearly or merged
start-percentage cut; 2021 to 2025 are yearly, 2026 is merged, and 2027 should be the first
weekly season. How it is calculated, including why the merged cut exists and the numbers
behind the decision: `Calculations.txt`, section 16 (Player WAR).

`data/war/<league>/<season>.json` holds the cut mode, the week it runs through, the
constants and replacement levels, and per player: name, position, NFL team of their
last game, games, points, position stat totals, each week's score used and win
probability, expected wins, WAR, the manager holding them (end of season, or the
current roster in progress) and every manager who held them. Re-running on unchanged
data gives the same file apart from its timestamp. The free-agent replacement level
in `data/replacement/` is a different thing and still feeds the simulation.



### Out statuses

One shared list of Sleeper statuses means "not playing" everywhere on the site (Out,
Doubtful, IR, PUP, Sus, NA, DNR, in `src/ffapp/injuries.py`): the Games cards' not-playing
list, the Player WAR ownership fallback, and the red cross on the Positions page. Details:
`Calculations.txt`, section 3 (Out statuses).

## Managers

The **Managers** sub-tab shows one manager at a time, after Football Manager's club page.
Pick a manager from the dropdown or step through them with the arrows (current managers
first, then "Retired"); any manager's name in a table on the other pages opens their page.

- **Team info bar:** the team logo (else the Sleeper avatar, else initials in the team
  colour), the team name, champion banners and toilet bowl banners (redraft), the form of
  the last five games as bars (win up, loss down, a draw or no game on the line), and
  Founded, All-Time record, Rating and Rival.
- **Season info bar:** Current League Position, Last Result, Next Matchup (with a Rivalry
  Week badge), Manager win rate, Top Scorer (projected before week 1), Best Player
  All-Time (most WAR in weeks on the team) and Playoff Forecast.
- **Roster:** the lineup with slot pills in Sleeper's position colours, status badges and
  points per game coloured against the position's replacement level.
- **Team History:** the finishes chart, honours and luck (all-play record, points against
  and points left on bench), head to head against every opponent, and records ranked
  against league history (#1 to #3 All Time).
- **Moves:** FAAB spent and the player history (most seasons on the team, the one that got
  away). The adds, drops and trades lists arrive with the transactions sync.
- **Team News:** short stories from the data (results, forecast moves, injuries, practice
  reports, depth-chart moves, trending adds, records, streaks, WAR milestones, rivalry
  week, Team of the Week), each written from a template in `site-copy.txt`.

Everything comes from `site/data/<league>/managers.json`, built by `src/ffapp/managers.py`
and `src/ffapp/news.py` (`Calculations.txt`, sections 19 and 20). Redraft rivals and each
season's rivalry week are set in `config/leagues.yaml` under the league's `rivals` block
(pairs of roster ids, so a rivalry follows the team); a league without one uses the
nemesis (the worst head-to-head record over at least four games). Each refresh also saves
Sleeper's player details (`data/players/<season>/week_NN.json`: injury body part, practice
participation, depth chart) and trending adds (`data/trending/<season>/<date>.json`) for
the news.

## Positional Rankings

The **Positions** sub-tab compares every manager's roster position by position, in the
style of 538's quarterback Elo charts: one chart per position the league starts (QB,
RB, WR, TE, K, DEF in redraft; no K in dynasty), one row per manager, and one dot per
rostered player at his points per game.

- **Points per game.** Regular season only: actual points in the weeks played plus
  projected points for the weeks left, per game (`Calculations.txt`, section 17).
- **Rosters.** Completed seasons use each team's final, end-of-season roster; the
  season in progress uses the current roster. Taxi and reserve players are included.
- **Rows.** Each chart orders managers by their best player's points per game, then
  the second best and so on, so the labelled top player always sits top right. A
  manager with nobody at a position keeps an empty row at the bottom.
- **The dotted line** is the position's WAR replacement level for that league-season
  ("Replacement Level"), from `data/war/` (see Player WAR).
- **Rows** are labelled with the manager's display name and, beneath it in small grey
  text, the team name, as on the Predictions and Games tabs. On desktop the two charts
  in a grid row share one row height, so both fill their cards.
- **Dots.** A light fill and a dark outline in the manager's colour (matched by owner,
  so a past season colours by manager rather than roster slot; former members are
  grey). A dotted outline marks a taxi player, and a red cross marks a player with an
  out status (current season only). Dots too close together step above and below the
  row line, and a chart's rows grow taller when a row needs more room. The top player's
  last name is centred over his dot, overhanging the plot if needed but never leaving
  the card. Hovering, focusing or tapping a dot shows the player's name and points per
  game, then his out status in red and "Taxi" in gold when they apply.
- **Axis.** One range per position for every season of a league; a value beyond it sits
  at the edge with an arrow (`Calculations.txt`, section 17).

The data is built at export time from stored files (rosters, users, stats, projections,
injury statuses and WAR), so nothing extra is stored under `data/`:
`site/data/<league>/positions/<season>.json` holds the weeks covered, the last final
week, per-position replacement levels and axis ranges, and per manager the owner and
players (id, name, position, NFL team, points per game, games played and projected,
taxi, reserve and injured flags); `positions/index.json` lists the seasons.

## Games

Every simulation run also stores a Forecast per game (mean scores, win probability, a shared
score histogram, the lineup used) and a projected playoff bracket for weeks Sleeper has not
paired. `ffapp games` keeps a per-game log of projections frozen at kickoff, and once a week is
final each game gets a fixed forecast of record from the lineups the managers started. How
they are calculated: `Calculations.txt`, section 10 (Game forecasts). Files:
`data/games/<league>/<season>/week_NN.json`.

Each team row shows its score block beside the win probability: before kickoff, the
forecast (mean simulated points, labelled "forecast"); once a game is live or final, the
current or final score in large type with the forecast beneath it ("forecasted") and the
team's lineup choices under that. On screens narrower than 600 px the chart moves under the
team rows so names and scores get the card's width. In the lineups, points (then win
probability added) sit just after the longest name of each list and line up as a column,
kickoff times sit at the right edge, and "Not playing" reasons follow the name.

### Card states

Every card is in one of 11 states (future, current but not started, live, paused, games over
and past week, with their variations), worked out by the exporter from the managers' real
starters and bench and stored on the card as `state`; the page draws each state from one
table. Live and paused cards show both full lineups; finished cards rank their key players by
win probability added and show the winner check, with an "Unofficial" chip until Sleeper scores
the week. The states, every transition between them, the rules and a screenshot of each state:
[`docs/games-page-states.md`](docs/games-page-states.md) (`Calculations.txt`, section 22). Redraw
the screenshots after changing the cards with `python -X utf8 tools/games_states_gallery.py`.

### Model and actual lineups

Cards where play has started or finished have a **Model | Actual** toggle (future weeks and
current-week cards nobody has kicked off in show the model only). Both are pre-kickoff forecasts simulated with the same model and no results; only the
lineup differs:

- **Model**: each roster's best legal lineup that week, every player at his last projection
  before kickoff (the log's frozen value, else his stored projection), with the week's
  projected replacement-level floor.
- **Actual**: the starters each manager used, at the same projections (the prediction of
  record). For 2026 weeks 1 to 10, played before the log existed, the model view is the
  pre-week forecast and the actual view is rebuilt from the real starters at their stored
  projections, labelled "rebuilt" because stored projections can include updates made after
  kickoff. During the live week the actual view is the live forecast.

Cards open on Actual. Win probability added shows in the actual view only; in the model view,
model picks the manager benched carry a "BN" tag. Each team shows **lineup choices**: the
points its starters scored minus the points the model lineup's players scored, a replacement
fill counting that week's realised replacement level (during the live week only players who
have kicked off count, fills once the week is final). The views are stored per game under
`views` in the week files, computed once like the record (`ffapp games --force-records`
recomputes them).

### Live weeks

Once the first NFL game of the next week kicks off (from the stored schedule, which also
keeps each game's quarter, clock and score), runs score that week live. A starting slot whose player has kicked off holds the player the manager started there,
scoring his points so far plus his projection for the time left (`Calculations.txt`,
section 12). Injuries and benchings during a game are not visible until it is final.

A live run writes `data/odds/<league>/<season>/live.json` and leaves the as-of result for the
completed weeks frozen at its last pre-kickoff version, so the forecast history and the
look-backs never see partial weeks. When the week is final, the next run writes the new
as-of result and removes the live file. The Forecasts table shows the live forecasts while
the file exists.

### Win probability added

Every starter with a score shows how much it moved his team's chance of winning against his
projection, everyone else as projected. How it is calculated: `Calculations.txt`, section 13.

## How the simulation works

Each Forecast plays the rest of the season 10,000 times from the last fully scored week:
best projected lineups with a replacement-level floor, score noise learned from past
seasons, roster drift for weeks further out, the real schedule, and each league's own
playoff and losers-bracket rules. The calculation is documented step by step in
`Calculations.txt`, sections 4 to 9; `verify-brackets` proves the bracket rules reproduce
every completed season.

## Calibration

`python -m ffapp calibrate` replays every stored season with status complete (dynasty
2022-2025, redraft 2021-2025) as of every week from preseason to the last playoff
round, using the production simulation and score noise learned from the *other*
seasons only. The replayed forecasts are stored in `data/odds/<league>/<season>/` like the
live ones, and the comparison with real results is written to
`data/calibration/report.json` and `data/calibration/report.md` (plus per-season rows
under `data/calibration/rows/`). The run takes about a minute.

The report checks the noise width (score level), next-week win chances (game level) and the
published season chances against a standings baseline (season level), plus the lineup gap
and the roster-drift diagnostic. The measures are defined in `Calculations.txt`, section 18.
`--no-replacement-floor` and `--no-roster-drift` replay without one piece so each can be
measured alone; the report records the switches.

The optional knob `simulation.residual_scale` is deliberately off by default. Change it
only when the score-level coverage is off across all seasons and both leagues, never to
make one season's playoff bins look better: nine seasons give about five usable bins
with roughly ±5 points of noise each. Try a value first with
`python -m ffapp calibrate --residual-scale 1.1`, which leaves the config alone and
records the scale it used in the report.

Commit `data/odds` and `data/calibration` after a run; the next cold run that deploys
publishes the calibration page.

## Website

`site/` is static: `index.html`, `styles.css`, `app.js`, a pinned copy of Chart.js
in `site/vendor/`, and the exported data. It is deployed to GitHub Pages by the
workflow and served at https://fantasyfoosball.net. The custom domain is set in the
repository's Settings -> Pages (no CNAME file, since Actions deploys), with DNS at Cloudflare
(four GitHub `A` records for the bare domain and a `www` CNAME to `tgraham1212.github.io`,
all DNS-only) and a `_github-pages-challenge-tgraham1212` TXT record that verifies the
domain on the account; keep that record. The old `tgraham1212.github.io/Fantasy-Football-App`
address redirects to it. If the domain ever changes, update the relay's `SITE_ORIGIN` at
the same time (see `relay/README.md`) or Refresh Data stops working. URL options: `#dynasty` / `#redraft` picks the league, `?team=<roster_id>`
highlights a team, `?metric=playoffs|bye|title|avoid_losers_bye|last` picks the
chart, `?theme=dark|light` forces a theme.

The forecast table follows the FiveThirtyEight layout: ELO (the manager's current
rating, see Manager ratings) and its change over the last rated week, **Manager** (bold
name with team name and record), projected
record, then four chance columns filled on a white-to-blue ramp. Columns left of Manager are
left-aligned, Manager is centred and the columns right of it are right-aligned (headers and
cells alike). On a phone the table scrolls sideways inside its box with the Manager column
pinned to the left edge, so ELO and 1-week change scroll away while the names stay beside the
chances; wider screens pin the first three columns. The first chance
column depends on the league: a toilet-bowl league shows **Avoid Loser's Bye**
(finishing outside the bottom two), a dynasty league with a consolation bracket
shows **#1 Pick** (finishing last). The export decides this from Sleeper's
`playoff_type` and `type` settings (`bottom_column` in `site/data/<league>.json`).
Rows start in standings order; clicking a header sorts descending, clicking again
ascending. Hovering a chance shows its change since the previous week. Each team
has a fixed colour (the dot beside the manager name) that matches its line in the
chart; the palette comes from `tools/team_palette.py`.

Under the forecast chart, the rating chart plots every manager who has ever played in
the league: **Rating** (the Openskill mean) or **Z-score** (career mean z), over
**This season**, **Last 3 seasons** or **All time**, with each season start marked on
the axis. Current members keep their table colour; former members use three greys
(`tools/team_palette.py --greys`, checked with the dataviz validator for separation
and contrast), dashed and then dotted once the greys repeat. Clicking a line or a
table row highlights that manager in both charts. The card says ratings are not yet
available when the export carried none.

Each league has five sub-tabs, **Forecasts** (the table and charts above),
**Games**, **Positions**, **Managers** and **Player WAR**, kept in the URL (`#redraft/war`,
`#redraft/games/10`, `#redraft/positions`, `#redraft/managers/tg1212`). On a phone the sub-tab row scrolls
sideways under a finger (it snaps to a tab, fades on the side with more tabs, and
opens scrolled to the selected tab); the page itself never scrolls sideways. The Player WAR page shows the top
10 per position in two columns (QB and RB, WR and TE, DEF and K; a league without a
kicker slot centres its last table), for the current season by default, any past
season, or **All-Time** with a toggle between player-seasons and careers. Each table
expands into a full sortable list with games, points and the position's stats (on a phone
the player name stays pinned while the list scrolls sideways). The
Manager column is the manager holding the player at the end of that season (the current
roster for the season in progress); hovering it lists any other managers who held
them. The bottom of the page explains the calculation with a flow chart and walks
through Kittle and Bowers in 2024 week by week from the league's own data. Seasons
before the first weekly-cut season are noted as using a yearly replacement cut.

`calibration.html` ("How Good Are These Forecasts?", linked from the footer) shows the
calibration report: predicted-vs-observed reliability per outcome, the score-noise
percentile histogram and interval coverage, head-to-head win-chance bins, the lineup
gap and the caveats. The export copies `data/calibration/report.json` to
`site/data/calibration.json`; without one the page says calibration has not been run.
It only changes when `calibrate` is re-run and its outputs committed.

### Live updates and the new version note

An open page checks once a minute (every 30 seconds while a game is in progress), while
its tab is visible, whether newer data, a newer live bundle from the refresh relay or newer
site code is out (`site/updates.js`). Newer data with the same code is swapped in without a
reload, whether it was deployed or came in a live bundle (`site/data.js` lays the bundle's
files over the deployed ones, so switching weeks shows them too): the league, sub-tab, Games week (kept in the URL as
`#dynasty/games/10`), each card's Model or Actual view, open lineups, table sorts,
the highlighted team and an open full list all stay as they were, and the note under
**Refresh Data** reads "Updated just now". This covers a refresh a visitor started
and the scheduled refreshes alike. After a visitor starts a refresh the note reads
"Started, back in ~1 min" ("~5 min" in the off-season, when only a cold run starts; the
full sentence is its tooltip) and, if no new data has arrived 10 minutes later, "Refresh
didn't finish". While games are in progress the button is held with "Live updates on", and
while a refresh is already running with "Refresh running".

Newer code is never paired with the old page: when `version.json` carries a
different fingerprint from the page's own (`site/version.js`, see the stamp below),
a note pinned to the bottom of the screen says a new version is available, with a
Refresh button, and stays until the page is reloaded. A local copy keeps the
placeholder fingerprint, so it checks for new data only.

### Site copy

`site-copy.txt` (project root) holds every piece of descriptive text on the site in one
place for copy editing: page and tab descriptions, headings, chart titles and notes,
explanations and on-screen messages. Each entry has a stable ID (`POS-02`), a label, its
location and its text; values the page fills in show as `${...}` placeholders and inline
markup (`<em>`, `<strong>`, links) is kept. The IDs live in the code: `data-copy="ID"` on
an HTML element, `/*copy:ID*/` before a script string.

To edit: change the text under `TEXT:` lines (keep the placeholders), add `NOTE:` lines for
questions, save. The tests then report the entries as pending copy edits, and they are
applied only after the owner confirms:

```bash
python -m ffapp site-copy            # regenerate the file from the code (keeps pending edits)
python -m ffapp site-copy --check    # report anything out of sync; non-zero exit if so
python -m ffapp site-copy --apply    # write confirmed edits into the HTML and scripts
```

`site-copy.lock.json` records a hash of each entry as last synced, which tells the two
directions apart: code changed but not the file means stale (regenerate); the file
changed but not the code means a pending edit (confirm, then `--apply`); both changed
means a conflict to resolve by hand. An edit that drops or changes a `${...}` placeholder
is refused. `tests/test_site_copy.py` fails on descriptive text without an ID, on a stale
file and on unapplied edits, so new text must be added in the same change (button labels,
tab names and table column headers are not part of the file).

### Layout check

`tests/layout/` loads every page in three browser engines: Chromium (the installed Chrome,
standing for Chrome and Edge) at 360, 390, 414, 440, 768, 1000 and 1280 px, and WebKit
(Safari's engine) and Firefox at 390, 440 and 1280 px for the engine-sensitive tests. The phone
widths follow StatCounter's US mobile screen statistics (reviewed yearly; see
`openspec/config.yaml`). It drives every control through its states (the refresh relay, `version.json`
and `data/index.json` are simulated, so no refresh starts) and fails when anything
the control is not designed to change moves or resizes, or when the page scrolls
sideways. `tests/layout/controls.py` is the registry of controls, their states and
their declared effects; a coverage test fails when a page shows a button, select,
expander or link the registry does not list, so add every new control there. The
check also asserts that the full list scrolls only its table, that phone lineups
show full names, that a data swap keeps the visitor's place, and that no page scrolls
sideways on a phone with a wide font (Linux draws wider text than Windows, so a
layout that only just fits on one machine can overflow on another). Run it locally with:

```bash
pip install -e ".[dev,browser]"
python -m playwright install webkit firefox
LAYOUT_REQUIRED=1 pytest tests/layout
```

Without Playwright or a browser engine the layout tests skip; `LAYOUT_REQUIRED=1`, set by the code-push workflow, turns a missing engine into a
failure.

The full layout check takes about 15 minutes, so any test run prints a progress line about
once a minute: tests done of the total, time so far, an estimate of the time left, failures
so far and the test running now (`tests/progress.py`). It appears in the terminal and in the
GitHub Actions log. `PROGRESS_SECONDS=30` changes the interval; `PROGRESS_SECONDS=0` turns
it off.

### Standards checks

The project standards (browsers, phone widths, WCAG 2.2 AA, Material Design 3 usability,
nomenclature and APA style, calculation docs) are written in `openspec/config.yaml` and
summarised in `CLAUDE.md`. Four checks enforce the checkable ones:

- `tests/layout/test_accessibility.py` runs axe-core (vendored in `tests/layout/vendor/`)
  with the WCAG 2.2 A and AA rules on every view at 390 and 1280 px, and checks that
  controls are at least 48 x 48 px at 360 and 440 px (inline links, chart canvases and the
  Positions dots are exempt);
- `tests/test_nomenclature.py` flags retired terms ("owner", "odds", "chances",
  "predictions", and "projected" meaning a forecast) in `site-copy.txt`;
- `tests/test_calculations_doc.py` checks every calculation module has a section in
  `Calculations.txt` with all its headings.

The first three start from baselines in `tests/baselines/` listing today's gaps. A new
finding fails at once; a fixed one fails until its baseline entry is removed, so the
lists only shrink. `UPDATE_BASELINES=1` rewrites a baseline on purpose.

After `git pull`, run `python -X utf8 -m ffapp build` before opening the site locally:
`site/data/` is not in git, and an older build may lack fields the page expects. The
layout check builds it by itself when it is missing.

Every local script reference, stylesheet link and module import in `site/` ends in
`?v=__BUILD__`. Every deploy runs `python -m ffapp stamp-site`, which fingerprints the
site's code (every file under `site/` except `site/data/`, line endings ignored),
replaces the placeholder with that fingerprint and writes `site/version.json`. A
deploy that only brings new data keeps the same fingerprint, so browsers keep their
cached scripts; any code change gives every reference a new URL, and open pages see
the new fingerprint in `version.json` and show the "new version" note. Locally the
literal placeholder is just a query string and the site works unchanged (the page
then checks for new data only). `tests/test_site_files.py` fails if a reference lacks
the placeholder or a deploying workflow skips `stamp-site`, so add the placeholder to
any new script, stylesheet or import, and stamp any new deploy through the command.
Do not run `stamp-site` in your checkout: it rewrites the site files in place.

## Refresh modes

The data refreshes in two kinds of run, and how often each runs depends on one of three
modes. The modes, their transitions, both runs' steps, where each kind of data lives, the
limits and what happens when something fails are in
[`docs/refresh-modes.md`](docs/refresh-modes.md), with a diagram. Redraw the diagram after
changing a mode, trigger or step with `python -X utf8 tools/refresh_modes_diagram.py`.

| Mode | Hot runs (`hot.yml`) | Cold runs (`refresh.yml`) |
|---|---|---|
| Off-season | Off | Daily at 11:00 UTC |
| Quiet (in season, no game in progress) | Every 15 min | Every 15 min |
| Live (a game in progress) | Back to back, about every 1 to 1.5 min | Every 15 min without the simulation, plus one when a slate goes final |

- **The refresh relay is the clock.** A Cloudflare cron trigger runs `relay/worker.js` every
  minute; it works out the mode from the schedule summary the cold run uploads and the game
  states in the latest live bundle, and starts the runs that are due. GitHub's own
  `0 11 * * *` schedule on `refresh.yml` is the fallback if the relay stops.
- **A hot run** (`python -m ffapp hot`) fetches this week's matchups and the scoreboard,
  simulates the live week and builds this week's game cards, and uploads them to the relay's
  KV store as one bundle. It never commits or deploys.
- **A cold run** (`python -m ffapp refresh`) syncs everything, rebuilds the derived data,
  commits `data/` only when a record changed and deploys `site/` only when what visitors see
  changed (`ffapp site-hash`). Trending and ESPN percentages are committed once a day
  (`ffapp hold-tallies`). It no longer runs the test suite: tests run on code pushes.
  A failure at any step ends the run before the commit and deploy, so the published
  site keeps its last good state. The one exception is the ESPN `snapshot` step (and
  `schedule` and `trending`): if it fails the run continues with the data already stored
  and ends with a warning annotation on the job naming the skipped step. Before the upload,
  `python -m ffapp stamp-site` stamps the script and stylesheet URLs with the code
  fingerprint and writes `version.json` (see above). It runs on the runner only, so no
  stamp is ever committed. GitHub Pages must be set to deploy from **GitHub Actions** in the
  repository settings.
- **The build cache** carries the derived data from each cold run to the next run, the hot
  runs and the code deploy (`actions/cache`, key prefix `build-`).

`.github/workflows/site.yml` deploys code: a push to `main` that changes site code,
the Python package, the tests or `pyproject.toml` restores the latest build cache (or runs
`ffapp build`), runs the full test suite with the browser layout check required, then stamps
and deploys the site with that data. It shares the cold run's concurrency group, so the two never overlap. A
failing layout check stops that deploy; the next cold run that deploys still deploys
whatever is on `main`, so fix forward.
