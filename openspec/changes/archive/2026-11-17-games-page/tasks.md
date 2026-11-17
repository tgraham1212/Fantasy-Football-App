# Tasks

## 1. Data foundations

- [x] 1.1 Keep the raw row's `date` in projection records (`to_record` in `src/ffapp/projections.py`) and verify a test in `tests/test_projections.py` stores and reads back the date, and that records without one still load
- [x] 1.2 Create `src/ffapp/schedule.py`: scoreboard fetch through the client plumbing, parse to `{games: [{home, away, kickoff_utc, state}]}` with ESPN-to-Sleeper abbreviation mapping, store at `data/nfl/<season>/week_NN.json`, and a kickoff lookup (kickoff time, kicked-off at a moment, bye); verify tests on a recorded scoreboard fixture cover parsing, `WSH`→`WAS`, a bye team, the kicked-off check and an error leaving stored files unchanged
- [x] 1.3 Add the `schedule` CLI command refreshing the current and next week from Sleeper `state`, and verify `python -m ffapp schedule` against the live endpoint writes this week's file with plausible kickoffs and states
- [x] 1.4 Save weekly injury statuses in the `snapshot` step (`data/injuries/<season>/week_NN.json`, current week only, `regular` and `post` season types) and verify tests cover the save, the same-week overwrite, the week rollover and the offseason no-op
- [x] 1.5 Implement the not-playing rule (bye from the schedule; saved Out, Doubtful, IR, with PUP and Sus as Out; inferred out for weeks without a saved file) and verify tests cover each case, including bye taking precedence

## 2. Game forecasts in the simulation

- [x] 2.1 Record per-game detail in `simulate_as_of` (mean, 2-point histogram as shares, win probability with ties split, both lineups with free-agent fills marked) under the payload's `games`, and verify tests on the seeded store check a known week's games, histogram shares summing to 1 and win probabilities summing to 1 per game
- [x] 2.2 Record per-run bracket pairings in `simulate()` and build the projected bracket (expected-seed seeding, league bracket rules including reseed, favourite advancing, toilet bowl advancing the likelier lower scorer, pairing frequency; consolation leagues project winners only), and verify tests on hand-built results cover seeding order, a reseeded semifinal, the toilet bowl rule and frequencies
- [x] 2.3 Use real pairings for playoff weeks Sleeper has set, and verify a test with stored week-15 matchups yields those games and no projected ones
- [x] 2.4 Run `python -m ffapp simulate --backfill-season` on the real store and verify every 2026 as-of file gains a `games` block, file sizes stay under 100 KB, and the season odds are unchanged by the added recording (done: all 22 files have games; files are 107-332 KB pretty-printed, 52 KB of data per current file, over the 100 KB estimate because the store writes one number per line; old and new code give identical season odds on the same data)

## 3. Projection log and prediction of record

- [x] 3.1 Create `src/ffapp/games.py` with the log append (current and later weeks, every rostered player's projection and lock flag, dedupe against the previous entry ignoring run time, locked players frozen at their last unlocked projection) and verify tests cover a three-run weekend, an unchanged run adding nothing, and a locked player ignoring a later projection change
- [x] 3.2 Implement the prediction of record for final weeks (real starters in slot order, last unlocked logged projection else stored projection, empty slots 0, deterministic seed, same noise and one-week drift, actual scores and winner) computed once per week, and verify tests cover the Sunday ruled-out case, an unexpected starter, determinism and no recomputation on re-run
- [x] 3.3 Implement the pre-week fallback from the as-of-(week-1) payload, flagged `pre-week`, and verify a test on a week without log entries
- [x] 3.4 Add the `games` CLI command and verify `python -m ffapp games` on the real store writes week files for every 2026 week, records for weeks 1–10 marked pre-week, and log entries for the current and later weeks
- [x] 3.5 Document the log, the lock rule, the record and the fallback in a README "Games" section and the data layout, and verify the documented commands run as written

## 4. Refresh scheduling

- [x] 4.1 Add `ffapp should-run` (schedule refresh for current and next week, `data/refresh/last_run.json`, the trigger and spacing rules, daily and manual always run, scoreboard failure skips unless daily) writing `run=true|false` to `$GITHUB_OUTPUT` when set, and verify tests cover a quiet hour, the pre-kickoff trigger, a final-game trigger, the three-hour spacing, the daily run and a scoreboard failure
- [x] 4.2 Write `last_run.json` at the start of `refresh`, insert `schedule` (non-fatal) and `games` into `REFRESH_STEPS` in the design's order, and verify `tests/test_refresh.py` checks the order, a schedule failure continuing with a warning, and a games failure stopping the run
- [x] 4.3 Add the hourly cron (`20 * * * *`) and the gate step to `.github/workflows/refresh.yml`, conditioning the refresh, commit, stamp and deploy steps on its output, and verify by running `ffapp should-run` locally with `GITHUB_OUTPUT` set to a temp file for a quiet time and a pre-kickoff time
- [x] 4.4 Document the schedule and the gate in the README's scheduled-job section and verify the cron strings match the workflow

## 5. Export

- [x] 5.1 Export `site/data/<league>/games/index.json` (weeks, labels, current week, kind per week) and `week_NN.json` per week (teams with owner, team name and colour key, means, win probabilities, histograms, key players, full lineups, not-playing lists, run time; record, actual scores, winner and source for finished weeks; bracket order and frequencies for projected playoff weeks), and verify `tests/test_export.py` checks a finished week, a current week, a projected playoff week and the key-player rule
- [x] 5.2 Keep the export working without game data and verify a test on such a store passes and the real `python -m ffapp export` succeeds

## 6. Win probability colours

- [x] 6.1 Add a `--diverging` mode to `tools/team_palette.py` producing a grey-midpoint green-to-red ramp per theme, run the dataviz validator on both, add the tokens to all three theme blocks of `site/styles.css`, and verify the validator results and text contrast of at least 4.5:1 at every step are recorded in the tool's docstring

## 7. Games page

- [x] 7.1 Add the Games sub-tab between Predictions and Player WAR and the `#<league>/games` hash in `site/index.html` and `site/app.js`, with `site/games.js` loaded with the build placeholder, and verify a link to `#redraft/games` opens the page and the other two sub-tabs are unchanged
- [x] 7.2 Build the week control (dropdown of all weeks, arrows disabled at the ends, opening on the current week) and verify in the browser that the arrows step and the selection follows
- [x] 7.3 Build the matchup cards (colour dot, owner and team name, mean points, filled win probability, overlaid distributions in owner colours) in the two-column grid with the lone-card centring and one column on phones, and verify by screenshots of both themes and the 375px harness
- [x] 7.4 Add key players with the expand to the full lineup and the not-playing list under each card, and verify in the browser on a team with a replacement fill and an injured player
- [x] 7.5 Show finished weeks (record probabilities, check on the winner, actual-score lines in team colours, pre-week label) and verify on week 10 in the browser
- [x] 7.6 Show playoff weeks (1 seed's side first, bye cards, frequency labels, toilet bowl below) and verify on week 15 for both leagues
- [x] 7.7 Show "Games are not yet available" without game data and verify against a site copy without the games folder

## 8. Integration

- [x] 8.1 Run `python -m ffapp refresh` end to end, then `pytest` and `openspec validate games-page --strict`, and verify all pass and the Games page shows the current week from the refreshed data
- [x] 8.2 Update the roadmap memory note with the Games page decisions and change B's remaining scope

## Workflow follow-up

- Commit and push after the user's review, then archive the change with spec sync.
- Change B (live games) follows: actual and in-progress results inside the simulation mid-week.
