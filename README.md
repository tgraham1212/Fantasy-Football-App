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
| `games` | Update this season's game files in `data/games/`: a log entry per game for the current and later weeks, and the prediction of record for weeks that have finished (see Games). `--force-records` recomputes every record. |
| `war` | Compute every player's Wins Above Replacement for every stored league-season (see Player WAR) and write `data/war/<league>/<season>.json`. |
| `refresh` | `sync`, `projections`, `stats`, `schedule`, `snapshot`, `ratings`, `replacement`, `war`, `simulate`, `games`, `export` in order, stopping at the first failure with a non-zero exit, except that a failed `schedule` or `snapshot` is skipped with a warning so the odds never depend on ESPN. This is what the scheduled job runs. |
| `calibrate` | Replay every completed season through the simulation and score the odds against what happened (see Calibration). Not part of `refresh`. `--runs N`, `--seed N`, `--residual-scale X` evaluate a candidate scale without touching the config. |

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
  ratings/<league>.json                        every manager's rating history by week (see Manager ratings)
  espn/<season>/season.json                    ESPN start/roster percentages, one frozen snapshot per season (see Player WAR)
  espn/<season>/week_NN.json                   the same, captured weekly from the 2026 season on
  espn/crosswalk.json                          Sleeper's player list trimmed to id, ESPN id, name and position
  war/<league>/<season>.json                   every player's WAR for that league-season, with the weekly detail
  nfl/<season>/week_NN.json                    NFL games for the week: teams, kickoff (UTC), state, byes (ESPN scoreboard)
  injuries/<season>/week_NN.json               {player_id: Sleeper injury status} as last seen during that week
  games/<league>/<season>/week_NN.json         per game: the projection log, the latest forecast and the prediction of record
  odds/<league>/<season>/asof_NN.json          one simulation result per as-of week (the odds history)
site/data/<league>.json, index.json            what the website reads
site/data/<league>/positions/<season>.json     positional rankings per season, plus positions/index.json (see Positional Rankings)
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

## Manager ratings

`ffapp ratings` rates every manager across the whole life of a league, for the
rating chart and the ELO columns on the site. Each scored regular-season week is one
free-for-all: all teams ranked by points scored, rated with Openskill's Plackett-Luce
model (`openskill` on PyPI) on a 1000 scale (start 1000, uncertainty 333; the
library's default parameters times 40). A blowout and a one-point win count the
same; only the rank matters. Playoff weeks, unplayed weeks and weeks with no points
are not rated.

Ratings follow the roster owner's Sleeper user ID, so a manager keeps one rating
through roster changes and former members keep their last one. Sleeper only stores
end-of-season owners, so a manager who quits before the league year officially ends
leaves a roster with no owner even though they played the season. Such a roster is
read as owned by the most recent earlier owner of that roster slot (else the first later
one), everywhere the app reads rosters: ratings, Player WAR owners, Positions and the odds
labels. Dynasty 2023 roster 11 is the case in our data: it reads as DeekBurg's, his 2022
owner. The stored Sleeper files are not changed. Only a roster with no owner in any
stored season is rated as a `vacant:<season>:<roster>` entry, so the week's ranking stays
complete; it is flagged and never charted.

Two rules keep the numbers meaningful across seasons:

- **Preseason reversion.** Entering every season after their first, each manager's
  rating mean moves `ratings.revert` of the way (default a third) toward a fixed
  1000. The anchor is 1000, not the league mean, so ratings cannot inflate or deflate
  as members leave and join. The uncertainty is left alone: resetting it sped up every
  week of the season and widened the spread when tried.
- **Early-season multiplier.** The rating change in the first rated weeks of a season
  is multiplied by `ratings.early_k` (default 2, 1.75, 1.5, 1.25, then 1), so managers
  settle at their level quickly after the offseason without a cliff at week 5. This is
  the one step outside the Openskill update; the uncertainty takes the model's value.

Alongside the rating, every team gets a weekly **z-score** (points minus that week's
league mean, divided by the sample standard deviation) and a **career mean z**: the
mean over every rated week they have played, never reset. The file also stores
background variants that the site does not show, kept for a later calibration
experiment: the season-to-date mean z, an exponentially weighted z carried across
seasons, and a fresh-start rating that resets to 1000 every preseason.

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

`ffapp war` values every player's season in Wins Above Replacement for each league,
following the Stathole Sports method (consensus lineups and a replacement cut drawn
by how widely a player is started), with the league's own scoring and roster slots.

1. **Start percentages.** `ffapp snapshot` pulls ESPN's public fantasy player list,
   which carries the share of ESPN leagues starting and rostering each player, and
   stores a slim copy under `data/espn/`. A season pulled after it ended has one
   frozen season-long value per player, so 2021 to 2025 have a single season snapshot
   each. The season in progress is pulled again on every run, but while it is in
   progress ESPN reports the current week's figure, not a season-long one (see
   "Current-season start percentages" below). The daily refresh also stores the
   current week's values, overwriting that week until it rolls over. ESPN players map to Sleeper ids through Sleeper's stored ESPN id, a short alias
   table in `src/ffapp/espn.py`, then a normalised name and position match with the
   NFL team as tiebreak; the command prints anyone started in at least 2% of leagues
   it could not match, so the alias table can be extended.
2. **Consensus lineup.** Each regular-season week, the most-started players with a
   game that week fill every position's starting slots (12 teams times the slots),
   then the most-started remaining RB/WR/TE fill the flex. The three most-started
   players past each position's cut are that week's replacement players.
3. **Season constants.** Over the regular season so far, each slot's mean and
   variance of actual points; the opponent is a normal distribution whose mean is the
   sum of the slot means and whose spread is the square root of the summed variances.
   The replacement level per position is the season mean of the replacement players'
   actual points.
4. **Wins.** A player's week is their actual points in a lineup whose other slots sit
   at the slot means, so the win probability is the share of the opponent distribution
   below the league mean plus (score minus the position's slot mean). A week with no
   game played takes the replacement level; a game played for zero points counts as
   zero. Expected wins is the sum over weeks 1 to 14, and WAR subtracts what the
   replacement level would earn every week, so a replacement-level season is exactly 0.

A season uses the **weekly cut** (each week's lineup from that week's snapshot) when
every scored week has a weekly snapshot, the **yearly cut** (every week from the
season snapshot) when none has, and the **merged cut** when some have. So 2021 to 2025
are yearly, 2026 is merged (weekly snapshots began in week 10), and 2027 should be the
first weekly season. The file records which. Every player at a lineup position with at
least one game played gets a WAR, rostered or not; the current season's values move
a little each week until week 14 is scored, because the constants are season-to-date.

`data/war/<league>/<season>.json` holds the cut mode, the week it runs through, the
constants and replacement levels, and per player: name, position, NFL team of their
last game, games, points, position stat totals, each week's score used and win
probability, expected wins, WAR, the manager holding them (end of season, or the
current roster in progress) and every manager who held them. Re-running on unchanged
data gives the same file apart from its timestamp. The free-agent replacement level
in `data/replacement/` is a different thing and still feeds the simulation.

### Current-season start percentages

The merged cut exists because of how ESPN's feed behaves during a season. This
subsection records the reasoning so it can be looked up later. The rules are in the
`player-war` spec ("Yearly and weekly cut") and in `merged_start_percentages` in
`src/ffapp/war.py`.

**The problem.** While a season is in progress, ESPN's season-level start percentage
is just the current week's figure. In November 2026, `data/espn/2026/season.json` was
identical to `week_11.json` for every player. Ranking every week of the season by
that one week's view treats anyone on a bye or hurt that week as a bench player for
the whole season. Josh Jacobs, for example, showed owned 91.5% and started 8.6%. The
consensus starter cut slid deeper, the "next three past the cut" became genuine
backups, and the 2026 RB replacement level came out at 5.0 points, against 8 to 11 in
every completed season. That inflated every 2026 RB and WR WAR.

**The rule.** A scored week with its own weekly snapshot uses it. Every other week
ranks each player by a merged figure:

- **Highest trusted start percentage.** A snapshot of a scored week counts for a
  player only if he played that week. A snapshot of the current, not yet scored week
  always counts. Byes and injuries only ever lower a start percentage, so the highest
  trusted figure is the closest to his role while active. A low figure from a
  current-week bye cannot win the maximum, and a player whose team had a bye in the
  only scored captured week gets his real figure from the current week.
- **Ownership, only for injured players.** A player not seen active in any scored
  captured week who carries an out status (the shared list below, in the latest saved
  injury file) takes the higher of that figure and his percent owned.
  Ownership barely moves during an injured-reserve stint, so it stands in for how
  often he was started while healthy. Healthy players never use it: a backup's
  ownership far exceeds his start rate (owned 50%, started 15%).

**Why it was revised.** The first version gave ownership to everyone not seen active
in a scored captured week. With only week 10 scored and captured, every player whose
team had a week-10 bye fell back to ownership, and backups flooded the replacement
zone. Measured 2026 redraft replacement levels:

| rule | QB | RB | WR | TE | K | DEF |
|---|---|---|---|---|---|---|
| single-week season snapshot (before) | 18.0 | 5.0 | 8.2 | 7.5 | 9.0 | 6.9 |
| scored weeks only, ownership for all not seen active | 17.4 | 6.4 | 6.5 | 6.7 | 8.3 | 6.9 |
| **highest trusted figure, ownership only if injured (used)** | **15.6** | **9.6** | **8.8** | **6.6** | **9.4** | **7.0** |
| 2021 to 2025 range | 15 to 18 | 8 to 12 | 8 to 11 | 6 to 7.5 | 7.4 to 9.4 | 6 to 8 |

Dynasty moves the same way (RB 5.0 to 9.8, WR 8.4 to 8.8). Each newly captured week
adds evidence, so the merged figure improves as the season goes on.

**What it does not touch.** Seasons pulled after they ended (2021 to 2025) have a
genuine season-long snapshot and keep the yearly cut. From 2027, every week has its
own snapshot, so seasons use the weekly cut and the merged rule no longer applies. To
see it on the current data, run `python -m ffapp war` and read `cut` and
`replacement` in `data/war/<league>/2026.json`.

### Out statuses

One list of Sleeper injury statuses means "not playing" everywhere on the site
(`OUT_STATUSES` in `src/ffapp/injuries.py`): Out, Doubtful, IR, PUP, Sus, NA and DNR,
shown as Out, Doubtful, IR, PUP, Suspended, Not active and Did not report. Doubtful
counts as out because such players almost never play; Questionable does not. It drives
the Games cards' not-playing list, the Player WAR ownership fallback, and the red cross
and popup on the Positions page.

## Positional Rankings

The **Positions** sub-tab compares every manager's roster position by position, in the
style of 538's quarterback Elo charts: one chart per position the league starts (QB,
RB, WR, TE, K, DEF in redraft; no K in dynasty), one row per manager, and one dot per
rostered player at his points per game.

- **Points per game.** Regular season only, weeks 1 to 14. A player's actual points in
  the final weeks he played, plus his projected points for the regular-season weeks not
  yet final, over the number of those weeks. A week counts as projected when its
  projection is above zero, and a week in progress counts as projected until it is
  final. A player with nothing scored and nothing projected is left out; a rookie who
  has not played yet still gets a figure from his projections. Games he played for
  another manager or as a free agent count, because the figure rates the player.
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
- **Axis.** Each position keeps one range in every season of a league, chosen so about
  99% of player-seasons fit, rounded to multiples of 5 and always including zero and
  the replacement level. A value beyond the range sits at the edge with an arrow, and
  its popup still shows the real number.

The data is built at export time from stored files (rosters, users, stats, projections,
injury statuses and WAR), so nothing extra is stored under `data/`:
`site/data/<league>/positions/<season>.json` holds the weeks covered, the last final
week, per-position replacement levels and axis ranges, and per manager the owner and
players (id, name, position, NFL team, points per game, games played and projected,
taxi, reserve and injured flags); `positions/index.json` lists the seasons.

## Games

Every simulation run also stores, for each week it plays, a forecast per game: each
team's mean score, a shared 2-point histogram of both teams' simulated scores (per-mille
shares), each team's win probability (ties split) and the lineup the model used, with a
replacement-level fill marked by an empty player id. Playoff weeks that Sleeper has not
paired yet get a projected bracket: teams seeded by expected seed, the league's own
bracket rules, and the team with the higher win probability advancing from each game (in
a toilet bowl, the team more likely to score lower). Each projected game says how often
that pairing happened across the simulations. Sleeper fills its bracket from the live
standings all season, so a pairing only counts as real once the week before it is final.
Consolation brackets are not shown; toilet bowls are.

`ffapp games` keeps a log per game for the current and later weeks. Each entry holds the
run time, both teams' model lineups and win probability, and every rostered player's
projection with whether his NFL game has kicked off (from the stored schedule; without
one, midnight Eastern on the projection's game date). An entry is added only when
something other than the time changed, and a player who has kicked off keeps his last
projection from before kickoff in every later entry.

Once a week is final, each game gets a **prediction of record**: the lineup each manager
actually started, every player at his last logged projection before kickoff (else his
stored projection, empty slots 0), simulated 10,000 times with the same noise model and
one week of roster drift, with a seed fixed per league, season and week. It is computed
once and kept. Weeks that finished before the log existed use the forecast made as of
the week before instead, marked `pre-week`; for 2026 that is weeks 1 to 10.

Each team row shows its score block beside the win probability: before kickoff, the
forecast (mean simulated points, labelled "forecast"); once a game is live or final, the
current or final score in large type with the forecast beneath it ("forecasted") and the
team's lineup choices under that. On screens narrower than 600 px the chart moves under the
team rows so names and scores get the card's width. In the lineups, points (then win
probability added) sit just after the longest name of each list and line up as a column,
kickoff times sit at the right edge, and "Not playing" reasons follow the name.

### Model and actual lineups

Finished and live game cards have a **Model | Actual** toggle (upcoming weeks show the model
only). Both are pre-kickoff forecasts simulated with the same model and no results; only the
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
keeps each game's quarter, clock and score), runs score that week live. A starting slot
whose player has kicked off holds the player the manager started there, from Sleeper's
lineup for the week; a player on the bench when his game started is not used. Each locked
starter scores `fixed + share * (projected + bias) + sqrt(share) * (residual - bias)`:
`fixed` is his points so far (Sleeper's per-player points, league scoring), `share` is the
share of his 60-minute game still to play (1 before kickoff, 0 when final, in overtime or
without a clock), and `bias` is the mean miss of the residual pool he draws from. So a final
player scores exactly his points, and in progress the projection and its bias scale with
the time left while the scatter scales with its square root (about 71% of a full game's
spread at half time). With `fixed` 0 and `share` 1 this is the usual `projected + residual`.
Open slots keep the model's best pick from players who have not kicked off. Injuries and
benchings during a game are not visible until it is final.

A live run writes `data/odds/<league>/<season>/live.json` and leaves the as-of result for the
completed weeks frozen at its last pre-kickoff version, so the odds history and the
look-backs never see partial weeks. When the week is final, the next run writes the new
as-of result and removes the live file. The Predictions table shows the live chances while
the file exists.

### Win probability added

Every starter with a score gets his win probability added: his team's chance of beating the
opponent with his projection replaced by his score, minus the chance with his projection,
everyone else as projected. Both come from a normal distribution of the margin with the
mean and spread of the game's pre-kickoff simulation (the prediction of record, or during
the live week a provisional one built the same way each run); when his score is known his
own share of the spread (from the noise model) is removed. A player in progress uses his
projected final (`so far + share * projection`) and keeps `share` of his variance. Weeks
before the log existed use the pre-week forecast's margin and each starter's stored
projection. The values show how big a swing each performance was; they do not add up to the
team's change.

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

The odds table follows the FiveThirtyEight layout: ELO (the manager's current
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

Under the odds chart, the rating chart plots every manager who has ever played in
the league: **Rating** (the Openskill mean) or **Z-score** (career mean z), over
**This season**, **Last 3 seasons** or **All time**, with each season start marked on
the axis. Current members keep their table colour; former members use three greys
(`tools/team_palette.py --greys`, checked with the dataviz validator for separation
and contrast), dashed and then dotted once the greys repeat. Clicking a line or a
table row highlights that manager in both charts. The card says ratings are not yet
available when the export carried none.

Each league has four sub-tabs, **Predictions** (the table and charts above),
**Games**, **Positions** and **Player WAR**, kept in the URL (`#redraft/war`,
`#redraft/games/10`, `#redraft/positions`). On a phone the sub-tab row scrolls
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

`calibration.html` ("How good are these odds?", linked from the footer) shows the
calibration report: predicted-vs-observed reliability per outcome, the score-noise
percentile histogram and interval coverage, head-to-head win-chance bins, the lineup
gap and the caveats. The export copies `data/calibration/report.json` to
`site/data/calibration.json`; without one the page says calibration has not been run.
It only changes when `calibrate` is re-run and its outputs committed.

### Live updates and the new version note

An open page checks once a minute, while its tab is visible, whether newer data or
newer site code has been deployed (`site/updates.js`). Newer data with the same code
is swapped in without a reload: the league, sub-tab, Games week (kept in the URL as
`#dynasty/games/10`), each card's Model or Actual view, open lineups, table sorts,
the highlighted team and an open full list all stay as they were, and the note under
**Refresh Data** reads "Updated just now". This covers a refresh a visitor started
and the scheduled refreshes alike. After a visitor starts a refresh the note reads
"Started, back in ~5 min" (the full sentence is its tooltip) and, if no new data has
arrived 20 minutes later, "Refresh didn't finish".

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

`tests/layout/` loads every page in the installed Chrome at 375, 440 (current large phones), 768, 1000 and
1280 px, drives every control through its states (the refresh relay, `version.json`
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
LAYOUT_REQUIRED=1 pytest tests/layout
```

Without Playwright or Chrome the layout tests skip (the data refresh job runs that
way); `LAYOUT_REQUIRED=1`, set by the code-push workflow, turns a missing browser
into a failure.

After `git pull`, run `python -m ffapp export` before opening the site locally:
`site/data/` is whatever the last export wrote, and an older export may lack
fields the page expects.

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

## Scheduled job

`.github/workflows/refresh.yml` has two schedules. `0 11 * * *` is the daily run at
11:00 UTC (after Monday night's game is scored) and always refreshes. `20 * * * *` is an
hourly check: a small `gate` job runs `python -m ffapp should-run`, which stores the
current and next week of the NFL schedule and decides from it. It refreshes when a game
kicks off within the next 60 minutes or a game has gone final since the last refresh
(a final game counts when it kicked off after four hours before the last run), and never
within three hours of the last refresh's start, which a successful refresh records in
`data/refresh/last_run.json`. Replayed over week 11 of 2026 (Eastern time), that gives
7:20 pm Thursday before the night game and 12:20 am after it; on Sunday 12:20 pm before
the 1 pm games, 3:20 pm before the 4 pm games, 6:20 pm once the early games are final
(two hours before the night game), 9:20 pm once the late games are final and 12:20 am
after the night game; 7:20 pm Monday and 12:20 am Tuesday around Monday night; plus the
daily run at 6 am. Manual starts always refresh; if the scoreboard cannot be read,
the hourly check skips that hour and the daily run goes ahead anyway.

When the gate says so, the `refresh` job runs the tests, `python -m ffapp refresh`,
commits `data/` and `site/data/` if anything changed, and deploys `site/` to GitHub
Pages.
A failure at any step ends the run before the commit and deploy, so the published
site keeps its last good state. The one exception is the ESPN `snapshot` step: if
ESPN is unreachable the run continues with the snapshots already stored and ends
with a warning annotation on the job naming the skipped step. After the data commit
and before the upload, `python -m ffapp stamp-site` stamps the script and stylesheet
URLs with the code fingerprint and writes `version.json` (see above). It runs on the
runner only, so no stamp is ever committed. GitHub Pages must be set to deploy
from **GitHub Actions** in the repository settings.

`.github/workflows/site.yml` deploys code: a push to `main` that changes site code,
the Python package, the tests or `pyproject.toml` runs the full test suite with the
browser layout check required, then stamps and deploys the site with the data on
`main`. It shares the refresh's concurrency group, so the two never overlap. A
failing layout check stops that deploy; the next data refresh still deploys whatever
is on `main`, so fix forward.
