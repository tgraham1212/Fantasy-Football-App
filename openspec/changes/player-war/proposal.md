# Proposal

## Why

The site rates managers but says nothing about the players who made their seasons, and the only replacement level in the system is the waiver wire, which is the right floor for a simulation but far too low to value a rostered player against (a free-agent RB in the dynasty league scores 4 points a week against a consensus 25th RB's 9). League members want a per-player, per-season Wins Above Replacement built the proven way, from consensus lineups and a replacement cut drawn by start percentage, and a leaderboard per league and year to argue over. A spike over 2021 to 2026 produced the seasons people remember (Kupp 2021, Chase and Barkley 2024, McCaffrey and Taylor 2025) on a scale of 2 to 3 wins for a top player.

## What Changes

- New external data source: ESPN's public fantasy player endpoint, for every player's start percentage. One frozen snapshot per past season, and from now on a weekly snapshot captured by the daily refresh, stored under `data/`. A second HTTP client with the Sleeper client's throttle and retry treatment.
- A crosswalk from ESPN players to Sleeper player IDs (Sleeper's stored ESPN id where present, otherwise name plus position with a team tiebreak, defenses by team table, plus a small alias table for known name mismatches), with a report of relevant players left unmatched.
- New `ffapp war` command and `data/war/<league>/<season>.json`: per league-season, the consensus lineup chosen by start percentage each week (players with a game that week only, flex-aware), the season slot means and opponent spread from those lineups, the replacement level as the season mean of the three players past each position's cut, and for every player who played at least one game that season their weekly win probabilities, expected wins and WAR over the regular season. A season is marked as using a yearly cut (one snapshot) or a weekly cut (a snapshot per week); 2021 to 2026 are yearly, later seasons weekly once every week has a snapshot.
- The refresh pipeline gains the snapshot capture and the `war` step; the export writes per-league WAR leaderboards for the site (one file per season plus an all-time index).
- Each league page gains a sub-tab, Predictions and Player WAR, kept in the URL. The Player WAR page shows the top 10 per position in two columns (QB and RB, WR and TE, DEF and K; a lone last table is centred), a season dropdown defaulting to the current season with an All-Time option that toggles between player-seasons and careers, an expand control per table opening a full sortable list with games, points and position stats, owner attribution per season with the other holders on hover, and a bottom-of-page explanation with a flow chart and a week-by-week Kittle versus Bowers 2024 walkthrough drawn from the league's own data.
- The existing free-agent replacement level and the simulation are untouched.

## Capabilities

### New Capabilities
- `start-percentage-snapshots`: capturing, storing and reading ESPN start-percentage snapshots (per season and per week), and the ESPN-to-Sleeper player crosswalk with its alias table and unmatched report.
- `player-war`: how a player-season's Wins Above Replacement is computed: consensus lineups, replacement cut, season constants, weekly win probability, missed-week handling, qualification, yearly versus weekly cut, and the stored file.
- `war-leaderboard-page`: the Player WAR page: season control and All-Time modes, the per-position tables and their layout, the expanded sortable list, owner attribution, the explanation section, and the exported leaderboard data it reads.

### Modified Capabilities
- `league-odds-site`: League pages gain the Predictions / Player WAR sub-tab; the scheduled refresh also captures the start-percentage snapshot and runs the `war` step.

## Impact

- Code: new `src/ffapp/espn.py` (client, snapshot capture, crosswalk), `src/ffapp/war.py` (model and files); `src/ffapp/cli.py` (`snapshot` and `war` commands, refresh order); `src/ffapp/export.py` (leaderboard files); `src/ffapp/store.py` (paths for snapshots and WAR files); `site/index.html`, `site/app.js`, `site/styles.css` (sub-tab, WAR page, modal, explainer); `config/leagues.yaml` only if an alias needs to be configured rather than coded.
- Data: `data/espn/` snapshots (about 25 MB raw per season if stored whole; the design decides what to keep), `data/war/<league>/<season>.json`, `site/data/<league>/war/*.json`, all committed by the daily refresh.
- External: requests to ESPN once per refresh, with a generic user agent and no league or user identifiers.
- Specs: new `openspec/specs/start-percentage-snapshots`, `player-war`, `war-leaderboard-page`; `league-odds-site` modified.
- Out of scope: manager-level WAR stats (WAR actually started by each manager), using WAR inside the odds model, and splitting the over-long "Calibration page" requirement, which this change does not touch.
