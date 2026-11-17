# Design

## Context

See proposal.md for motivation. What exists today and shapes the approach:

- `data/stats/<season>/week_NN.json` holds a stat line for every player who played, with first and last name, position and NFL team per week. `data/leagues/<league>/<season>/matchups/` holds every roster's `players`, `starters` and per-player points per week. Both go back to 2021 (dynasty 2022).
- `src/ffapp/replacement.py` computes the free-agent replacement level the simulation uses. It stays as it is; WAR gets its own replacement definition.
- `src/ffapp/sleeper.py` has the only HTTP plumbing (throttle, retries, timeouts) and already exposes `state()` for the current NFL week. Its `get_json` sends fixed headers.
- ESPN's public endpoint `lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/<season>/players?view=kona_player_info&scoringPeriodId=<n>` with header `X-Fantasy-Filter: {"players":{"limit":5000}}` returns every player with an `ownership` block (`percentStarted`, `percentOwned`). For a finished season the block is one frozen value regardless of `scoringPeriodId`; for the current season it is live. Verified during exploration for 2021 through 2026.
- The site is one page (`site/index.html` + `site/app.js`, a module) with the league in the URL hash, a sortable odds table, two Chart.js charts, and a separate `calibration.html`.
- The spike script that produced the exploration numbers lives in the session scratchpad (`war_spike.py`); it is the reference implementation for the model and must be reproduced in `src/ffapp/war.py` with tests, not copied.

## Goals / Non-Goals

**Goals:**
- Reproduce the spike's results from the repository alone, deterministically, for every stored season.
- Keep the daily refresh robust: an ESPN outage must not stop the odds.
- Keep the site static and the per-page payload small: load one season at a time, all seasons only for All-Time.

**Non-Goals:**
- Super-flex or IDP lineups (neither league has them; flex eligibility comes from `league.FLEX_ELIGIBLE` so a later league could add slots).
- Manager-level WAR (started WAR per manager), career-wide ESPN history beyond what the API returns, and any change to the simulation's replacement floor.

## Decisions

**1. ESPN client reuses the Sleeper plumbing.** `get_json` gains an optional `headers` argument merged over the defaults; `src/ffapp/espn.py` holds an `EspnClient` that wraps a `SleeperClient` instance for the request and adds the filter header and ESPN base URL. Alternative: a copy of the retry loop. Rejected because two retry loops drift.

**2. Snapshots stored slim.** A raw ESPN response is about 25 MB; the stored snapshot keeps only players with an `ownership` block at fantasy position ids 1, 2, 3, 4, 5 and 16, as `{espn_id: {name, position, team, started, owned}}` with the team abbreviation resolved from ESPN's `proTeamId` by a table in `espn.py` (28 is `WAS`). About 300 KB per snapshot. Paths: `data/espn/<season>/season.json` and `data/espn/<season>/week_NN.json`, both via new `Store` methods.

**3. Which week a weekly snapshot belongs to.** The Sleeper `state` endpoint's `week` and `season_type`; a weekly snapshot is written only when `season_type` is `regular`. Each run overwrites the current week's file, so the Monday or Tuesday run is the one kept. ESPN's value barely moves once lineups lock, so that is close enough to a pre-kickoff capture; a run on Sunday morning (the schedule is 11:00 UTC daily) is the practical capture, and later runs in the same week only refresh it.

**4. Crosswalk inputs.** The snapshot step also fetches Sleeper's `/v1/players/nfl` once per run and writes `data/espn/crosswalk.json` holding only fantasy-position players: `{sleeper_id: {espn_id, name, position}}`, written only when the content changed so the daily commit does not churn. Matching order per the spec: ESPN id, alias table, normalised name and position, team tiebreak. The team used for the tiebreak is the Sleeper player's team in the season being mapped, taken from that season's stat lines (last game), not the current team. The alias table is a dict in `espn.py` from ESPN name to Sleeper player id. Normalisation lowercases, strips suffixes (Jr, Sr, II, III, IV, V) and every non-letter.

**5. Model lives in `src/ffapp/war.py` with the spike's structure.** Inputs per league-season: roster slots and `num_teams` from the stored league, scoring via `resolve_settings` (so overrides apply), stat lines per week, the matchups for owner attribution, and the snapshot(s). Per week: available = players with a stat line that passes `stats.played`; consensus lineup and replacement cut per the spec; slot scores and replacement scores recorded. Season constants, win probabilities and WAR per the spec, using `math.erf` for the normal CDF. Weeks are `regular_season_range` up to `last_scored_leg`. The cut mode is decided once per season: weekly when every such week has a weekly snapshot, else yearly.

**6. Owner attribution computed in `war.py`, resolved to names at export.** For each player and scored week, the roster whose `players` list holds them gives the holder. `owner` is the holder in the last scored week (or the current roster when the season is in progress); `holders` is the ordered list of distinct managers over the season. Stored as Sleeper user ids; the export maps them to display names from the season's users, so a renamed manager still resolves.

**7. Position stat totals.** Summed over played weeks from the stat line keys: `pass_yd`, `pass_td`, `pass_int`, `rush_yd`, `rush_td`, `rec`, `rec_yd`, `rec_td`, `fgm`, `fga`, `xpm`, `sack`, `int`, `fum_rec`, `def_td`, `pts_allow`. Points allowed per game is `pts_allow` divided by games played, rounded to one decimal. A missing key counts as zero.

**8. File shapes.** `data/war/<league>/<season>.json`: `league_key`, `season`, `generated_at`, `cut` (`yearly` | `weekly`), `through_week`, `weeks`, `constants` (per position: slot mean, slot variance; plus opponent mean and spread), `replacement` (per position: level, baseline expected wins), `players` keyed by Sleeper id with name, position, team, games, points, stats, `weekly` (list of `{week, score, played, p}`), `exp_wins`, `war`, `owner`, `holders`, and `unmatched` (the crosswalk misses at or above 2 percent started). Site: `site/data/<league>/war/index.json` (`seasons` with cut and through-week, `current`, `first_weekly`) and `site/data/<league>/war/<season>.json` (slim rows without `weekly`, owner names, plus `walkthrough` holding the two reference players' full weekly series when present).

**9. Refresh order and failure policy.** `sync, projections, stats, snapshot, ratings, replacement, war, simulate, export`. `cmd_refresh` treats a `snapshot` failure as a logged warning and continues, because WAR only needs the snapshots already stored and the odds must not depend on ESPN. Run on its own, `ffapp snapshot` exits non-zero on failure. When the refresh finishes with a skipped step it prints a summary line naming the step and the reason; under GitHub Actions (`GITHUB_ACTIONS` set) that line uses the `::warning title=Refresh skipped a step::<reason>` workflow command, so the run stays green but shows a warning annotation on its summary page. `war` runs after `stats` so the current week's stat lines are in.

**10. Site structure.** `site/index.html` gains a sub-tab bar under the league switcher and a second top-level container for the WAR page; `site/app.js` keeps the Predictions page and delegates the WAR page to a new `site/war.js` module (season control, tables, overlay, explainer). The URL hash becomes `#<league>` or `#<league>/war`. The overlay is a `<dialog>`; its table header reuses the odds table's sort behaviour, generalised into a shared helper so both tables share the state rules. The flow chart is inline SVG in `index.html` styled with the existing theme tokens. The two-column grid centres a lone last table with `:last-child:nth-child(odd)`. Career mode is computed in the browser from the loaded season files.

**11. Walkthrough players.** The export looks up Kittle and Bowers in the 2024 file by Sleeper id (constants in `export.py`); if either is missing the `walkthrough` field is omitted and the page shows only the flow chart.

## Risks / Trade-offs

- [ESPN endpoint is undocumented and may change shape or disappear] → the snapshot step is non-fatal in the refresh, parsing is strict and reports the failure, stored snapshots keep WAR working for past seasons.
- [Season snapshots are late-season values, so players hurt late rank low and the cut can look odd for one position-year] → accepted by the user as a resolution loss; the available-this-week rule removes the worst of it, and seasons from 2027 use weekly cuts. The page states which seasons are yearly.
- [Name matching misses a player at the cut] → the unmatched report lists anyone at or above 2 percent started; the alias table is extended by hand. The spike found one to three such players per season.
- [Site data growth] → about 120 KB per league-season plus the two walkthrough series; the index lets the page load one season at a time. All-Time loads all seasons on demand.
- [`data/espn` grows by about 5 MB per season of weekly snapshots] → acceptable for the repository; slim storage keeps it bounded.
- [Current-season WAR shifts weekly as the constants settle] → stated on the page with the through-week label.

## Migration Plan

1. Ship the code with the refresh order change; run `ffapp snapshot` once locally to backfill the season snapshots for 2021 to 2026 and the crosswalk, then `ffapp war` and `ffapp export`, commit `data/espn`, `data/war` and `site/data`.
2. The daily workflow starts capturing weekly snapshots on its next run; nothing else to configure.
3. Rollback: remove the `snapshot` and `war` steps from the refresh order and the sub-tab from the site; the data directories can stay or be deleted.
