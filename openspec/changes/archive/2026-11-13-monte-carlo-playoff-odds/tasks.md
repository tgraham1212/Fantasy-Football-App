# Tasks

## 1. Project setup

- [x] 1.1 Create `pyproject.toml` (Python 3.12+, requests, numpy, pyyaml; dev: pytest), the `src/ffapp/` package with `__main__.py`, and `tests/`. Verify `pip install -e .[dev]` succeeds and `pytest` runs with zero tests collected and no errors.
- [x] 1.2 Add `config/leagues.yaml` with league keys `dynasty` (`1339662153812025344`) and `redraft` (`1389347876550770688`) and an empty `overrides` list. Add a config loader that rejects unknown keys and malformed overrides. Verify with unit tests for valid, missing-ID and bad-override cases.
- [x] 1.3 Add the CLI skeleton (`python -m ffapp {sync,projections,simulate,verify-brackets,export,refresh}`) with placeholder commands. Verify `python -m ffapp --help` lists every command.
- [x] 1.4 Record Sleeper fixture responses (league, users, rosters, matchups, brackets, state, one projections week trimmed to about 30 rows) into `tests/fixtures/`. Verify a test confirms each fixture loads and has the fields the design depends on.

## 2. League sync (`sleeper-league-sync`)

- [x] 2.1 Implement the Sleeper HTTP client: base URL, timeout, retry with backoff, throttle about 5 per second, error raised on non-2xx. Verify with tests that stub HTTP responses.
- [x] 2.2 Implement the history-chain walk through `previous_league_id`, stopping on null, empty or `"0"`. Verify with fixture tests that a 3-season chain returns 3 league-seasons, newest last.
- [x] 2.3 Implement the per-season store under `data/leagues/<key>/<season>/` (league, users, rosters, matchups/week_NN, brackets). Writes go to temp files and are swapped in only after the whole season fetch succeeds. Verify a test where a failed fetch leaves existing files byte-identical.
- [x] 2.4 Skip seasons whose stored status is `complete` unless `--full` is passed. Verify with a test that counts stubbed HTTP calls for both modes.
- [x] 2.5 Implement owner mapping (roster_id → owner user_id, display name, team name) per season. Verify with a fixture where slot ownership changes between seasons.
- [x] 2.6 Implement `resolve_settings(league_key, season, week)` layering overrides with `from_week`. Verify unit tests for before/after the override week and for no override.
- [x] 2.7 Wire `sync` into the CLI. Run it live against both leagues and verify `data/leagues/dynasty/` holds 2022-2026, `data/leagues/redraft/` holds 2021-2026, and 2026 matchups for weeks 1-9 have scores.

## 3. Projections (`player-projections`)

- [x] 3.1 Implement the projections source function (one season-week, all six positions) with response-shape checks. Verify tests: valid fixture accepted; non-list, missing `stats` and HTTP error each raise without writing.
- [x] 3.2 Implement the upsert into `data/projections/<season>/week_NN.json`: drop rows with empty stats, replace only when `last_modified` is newer, keep the file when the source returns nothing. Verify unit tests for newer, older/equal, missing-player and empty-week cases.
- [x] 3.3 Implement `projected_points(stats, scoring)` as a dot product that ignores `pts_*` keys. Verify unit tests: the kicker case (120 FG yards, 3 XP, `fgm_yds` 0.1, `xpm` 1 → 15.0) and a missing projection counting as 0.
- [x] 3.4 Wire `projections` (current season weeks 1-17) and `projections --backfill` (2021 onward) into the CLI. Run the backfill live and verify every week file from 2021 through 2026 exists and is non-empty.
- [x] 3.5 Sanity-check the scoring: for 3 completed weeks, compare league-scored projections with the source's `pts_half_ppr` for non-kicker skill players. Verify the median absolute difference is under 0.5 points, and record the result in the test output.

## 4. Bracket logic and history check

- [x] 4.1 Implement final regular-season standings from stored matchups (wins + 0.5 × ties, then points scored) for a completed league-season. Verify against a hand-checked fixture.
- [x] 4.2 Implement winners-bracket logic (6 teams, 2 byes) with fixed and re-seed modes, plus losers-bracket logic for seeds 7-12. Verify unit tests for each mode with given seeds and game winners.
- [x] 4.3 Implement `verify-brackets`: for each completed league-season, compare produced week-15 pairings and replayed later-round pairings against stored brackets, and report mismatches. Run it live; adjust the `playoff_seed_type` → mode mapping and the losers-bracket rules until all 9 completed league-seasons pass. Verify a test runs the check over recorded fixtures for at least the 2025 dynasty and 2025 redraft seasons.

## 5. Simulation (`playoff-odds-simulation`)

- [x] 5.1 Implement as-of detection (`min(last_scored_leg, 14)`, playoff weeks 15-16 handled) and loading of fixed results for completed weeks. Verify unit tests, including a week Sleeper hasn't scored yet being treated as unplayed.
- [x] 5.2 Implement roster selection: the current roster minus reserve and taxi; the backfilled roster as of N taken from week-(N+1) matchup `players`. Verify fixture tests for both paths and for as-of 0.
- [x] 5.3 Implement greedy lineup selection (fixed slots, then FLEX from RB/WR/TE; 0-projection players last). Verify unit tests for the flex-choice and bye-week scenarios in the spec, and for both leagues' slot layouts.
- [x] 5.4 Implement residual pools (position × projection band, minimum 200 samples or fall back to the whole position) built from stored matchups and projections. Verify unit tests for band assignment and fallback, and log pool sizes when run live.
- [x] 5.5 Implement the vectorized engine: remaining regular weeks on the real schedule, standings and tiebreak, both brackets, and in-progress playoff rounds taken from stored brackets. Use a seeded generator and 10,000 runs. Verify tests: sums (600/200/200/100/600/100%), a clinched team at 100%, identical output for the same seed, and a run time under 60 seconds for one league.
- [x] 5.6 Implement the odds-history store `data/odds/<key>/<season>/asof_NN.json` (per-team results plus generated_at, run count, seed), replacing only the same as-of key. Verify a test where re-running week 10 leaves weeks 0-9 unchanged.
- [x] 5.7 Wire `simulate` and `simulate --backfill-season` into the CLI. Run the backfill live for 2026 and verify as-of 0-9 files exist for both leagues, and that week-9 playoff chances look reasonable against current standings (spot-check the top and bottom teams).

## 6. Website (`league-odds-site`)

- [x] 6.1 Implement `export`, writing `site/data/<league_key>.json` (teams, owners, record, points scored, projected record, all chances, change since the previous as-of week, history series, as-of week, generated_at). Verify a schema test on the exported file.
- [x] 6.2 Build `site/index.html` with CSS and a JS module: league switcher, odds table sorted by playoff chance with weekly change, freshness label. Verify by opening it locally (`python -m http.server -d site`) and checking both leagues render all 12 teams.
- [x] 6.3 Add the odds-over-time chart (pinned Chart.js copy in `site/vendor/`): playoff chance by default, switchable to bye/final/title, highlight-on-select. Verify locally that the lines cover as-of weeks 0-9 and that switching metrics works.
- [x] 6.4 Make the layout work on phones (no sideways page scroll at 375px; the table scrolls inside its container) with light and dark themes. Verify in a 375px-wide browser viewport.
- [x] 6.5 Write `README.md` covering setup, CLI commands, the config file (including the yearly redraft ID update and overrides) and the data layout. Verify each documented command runs as written.

## 7. Scheduled job and deployment

- [x] 7.1 Implement `refresh` (sync → projections → simulate → export, stopping at the first failure with a non-zero exit). Verify a test where a stubbed projections failure stops before simulate and leaves `data/` unchanged.
- [x] 7.2 Add `.github/workflows/refresh.yml`: daily cron at 11:00 UTC plus `workflow_dispatch`, concurrency group, Python setup, `pytest`, `refresh`, commit and push `data/` only if changed, deploy `site/` to GitHub Pages. Verify with a manual `workflow_dispatch` run that succeeds and publishes the site.
- [x] 7.3 Integration check: after the manual run, open the published Pages URL on desktop and phone and confirm both leagues show current as-of odds, the trend chart and the correct freshness label. Then confirm the next scheduled run commits only changed files under `data/`.
