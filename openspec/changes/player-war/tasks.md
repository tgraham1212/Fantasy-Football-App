# Tasks

## 1. ESPN snapshots and crosswalk

- [x] 1.1 Add an optional `headers` argument to `SleeperClient.get_json` merged over the defaults, and verify a test in `tests/test_sleeper.py` shows the extra header sent and the user agent kept
- [x] 1.2 Create `src/ffapp/espn.py` with `EspnClient` (ESPN base URL, filter header, ESPN team-id table) and `slim_snapshot(payload)` keeping only fantasy-position players with an ownership block as `{espn_id: {name, position, team, started, owned}}`, and verify tests on a small recorded ESPN fixture under `tests/fixtures/espn/` produce the expected rows, map team 28 to `WAS` and raise on an unexpected shape
- [x] 1.3 Add `Store` paths and readers for `data/espn/<season>/season.json`, `data/espn/<season>/week_NN.json` and `data/espn/crosswalk.json`, and verify tests round-trip each and list the weekly snapshots a season has
- [x] 1.4 Implement `capture_snapshots(client, sleeper, store, league_keys)`: a season snapshot for every stored season lacking one, a weekly snapshot for the current regular-season week from Sleeper `state` (overwriting that week only), no weekly write in the offseason, no file written on failure; verify tests cover backfill, stored-season skip, same-week overwrite, week rollover, offseason and a failing request leaving files intact
- [x] 1.5 Implement the crosswalk: fetch Sleeper's player list into `data/espn/crosswalk.json` (fantasy positions only, written only when changed), `normalise(name)`, the alias table, and `match(snapshot, crosswalk, season_teams)` returning `{espn_id: sleeper_id}` plus the unmatched list at or above 2 percent started; verify tests cover ESPN-id match, alias match, suffix and punctuation differences, team tiebreak, ambiguity left unmapped, and defense-by-team
- [x] 1.6 Add the `snapshot` CLI command that captures, builds the crosswalk and prints the unmatched report, and verify `python -m ffapp snapshot` against the live endpoints writes 2021 to 2026 season snapshots, the current week's snapshot and the crosswalk, and lists the known misses (Gainwell, Okonkwo, Knight, Hunter) until their aliases are added, after which it lists none at or above 2 percent

## 2. WAR model

- [x] 2.1 Create `src/ffapp/war.py` with `available(stats)`, `consensus_lineup(ranked, slots, flex_count, available)` and `replacement_players(...)`, and verify tests on hand-built rankings show bye players skipped, the flex taking the next most-started RB/WR/TE, and the replacement cut moving past the flex
- [x] 2.2 Implement the season constants (pooled slot means, slot-count-weighted opponent mean and spread) and the replacement level per position from per-week records, and verify tests reproduce hand-computed values for a two-week synthetic season
- [x] 2.3 Implement the weekly win probability, expected wins and WAR per player (missed week at replacement, zero while active as zero), and verify tests reproduce the spec's 0.86, 1.54 and zero-WAR examples
- [x] 2.4 Implement the cut-mode decision (weekly only when every scored regular-season week has a weekly snapshot) and the per-week snapshot selection, and verify tests cover yearly, fully weekly and partly captured seasons
- [x] 2.5 Implement owner attribution from the matchup rosters (end-of-season or current holder plus ordered holders) and the position stat totals including points allowed per game, and verify tests cover a traded player, an unrostered player and a defense's per-game figure
- [x] 2.6 Implement `build_war(store, config, league_key, season)` and `write_war` to `data/war/<league>/<season>.json` with the design's file shape, qualifying only players with a played game, skipping and reporting seasons without a snapshot, and verify tests show every stored season written, a retired-but-listed player absent, and two runs identical apart from `generated_at`
- [x] 2.7 Add the `war` CLI command, insert `snapshot` after `stats` (non-fatal in `cmd_refresh`) and `war` after `replacement` in `REFRESH_STEPS`, and verify `tests/test_refresh.py` checks the nine-step order and that a snapshot failure lets the remaining steps run while a `war` failure stops the refresh
- [x] 2.8 Make `cmd_refresh` end with a summary naming any skipped step and its reason, printed as a `::warning title=...::` workflow command when `GITHUB_ACTIONS` is set and as a plain warning line otherwise, and verify tests capture both forms and that a clean refresh prints no warning
- [x] 2.9 Run `python -m ffapp war` on the real store and verify the 2024 and 2025 redraft leaders match the exploration spike (Chase, Barkley, Jackson; McCaffrey, Taylor, Gibbs) and Bowers 2024 is within 0.05 of 1.54
- [x] 2.10 Document the `snapshot` and `war` commands, the data layout entries and a "Player WAR" section (model, yearly versus weekly cut, who qualifies, file shape) in `README.md`, and verify the documented commands run as written

## 3. Export

- [x] 3.1 Write `site/data/<league>/war/index.json` and one slim file per season (rows without weekly series, owner and holder display names, stats, cut and through-week), plus the Kittle and Bowers 2024 weekly series under `walkthrough` when both are present, and verify `tests/test_export.py` checks the index, a season file's rows and the walkthrough field
- [x] 3.2 Keep the export working for a league with no WAR files (no war directory, index absent) and verify a test on such a store passes and `python -m ffapp export` succeeds on the real store

## 4. Site: navigation and WAR page

- [x] 4.1 Add the Predictions / Player WAR sub-tab bar to `site/index.html` and the `#<league>/war` hash handling to `site/app.js`, keeping the sub-tab across league switches, and verify in the browser that a link to `#dynasty/war` opens the dynasty WAR page and the odds page is unchanged
- [x] 4.2 Create `site/war.js` with the season dropdown (current season default with through-week label, every season in the index, All-Time), the yearly-cut note, and the six-position compact tables in a two-column grid that omits missing positions and centres a lone last table; verify in the browser that redraft shows three rows of two, dynasty shows five tables with DEF centred, and the 375px harness stacks them with no horizontal scroll
- [x] 4.3 Implement owner cells with the hover list of other holders and a dash for unrostered players, and verify in the browser on a traded 2025 player
- [x] 4.4 Implement All-Time with the Seasons / Career toggle (year column in Seasons, summed WAR and seasons count in Career, owner from the latest season), loading all season files on demand, and verify in the browser that Kupp 2021 and McCaffrey 2025 appear in Seasons and each player once in Career
- [x] 4.5 Implement the expand control and `<dialog>` overlay with the full sortable list (GP, PS, position stat columns, WAR, year in Seasons mode) sharing the odds table's sort state rules through a common helper, and verify in the browser that one click on PS sorts descending with fill and arrow, a second ascending, and closing restores the page
- [x] 4.6 Add the explanation section: inline SVG flow chart with theme tokens and the Kittle versus Bowers 2024 walkthrough rendered from the walkthrough data (per-week score, played or replacement fill, win probability, totals and WARs), omitted when the data is absent; verify in both themes by screenshot
- [x] 4.7 Show "WAR is not yet available" when the league has no WAR index, and verify by loading the page against a site data directory without the war folder

## 5. Integration

- [x] 5.1 Run `python -m ffapp refresh` end to end locally, then `pytest` and `openspec validate player-war`, and verify snapshots, WAR files, site data and all tests pass with no validator warnings
- [x] 5.2 Take headless screenshots of the WAR page in light and dark themes at desktop and 375px widths for both leagues, and verify layout, centring, overlay and explainer render as specified
- [x] 5.3 Update the roadmap memory note with the WAR decisions and the ESPN capture caveats

## Workflow follow-up

- Commit and push after the user's review, then archive the change with spec sync.
