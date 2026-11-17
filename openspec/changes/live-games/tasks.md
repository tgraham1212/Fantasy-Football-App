# Tasks

## 1. Schedule clock and scoring model

- [x] 1.1 Add `quarter`, `clock`, `home_score`, `away_score` to `parse_scoreboard` and a `share_left(game)` helper (scheduled 1.0, quarters 1-4 from the clock, final, overtime or missing clock 0), and verify `tests/test_schedule.py` covers a 3rd-quarter game, half time (0.5), overtime, final and a file stored before these fields existed
- [x] 1.2 Add `fixed` and `share` to `Starter` with defaults 0.0 and 1.0, add `bias` and `sd` to the noise models, and score starters as `fixed + share * (projected + bias) + sqrt(share) * (residual - bias)` in `simulate()`, and verify tests show defaults reproduce today's results exactly (same seed, same arrays), a final starter is constant, and a half-time starter's mean and spread match the spec example

## 2. Live week inputs and files

- [x] 2.1 Create `src/ffapp/live.py`: detect the live week from the stored schedule, build locked starters from the week's matchup rows (`starters` in slot order, `players_points`, share left) and fill open slots with `best_lineup` over unlocked, non-starting rostered players plus the replacement floor, and verify tests cover a locked FLEX starter, a benched Thursday player not counted, an open slot re-picked after a ruling-out, and no live week before the first kickoff
- [x] 2.2 Thread a `live` option through `build_inputs`, `simulate_as_of` and `run_as_of`; when live write `live.json` (with `live.week`, `games_final`, `games_total`, `generated_at`) and leave `asof_NN.json` alone; when not live write the as-of file and delete a stale `live.json`; verify `tests/test_odds.py` covers the frozen as-of file, the live file contents, its removal after the week is final, and that backfill and calibration never write it
- [x] 2.3 Add per-starter live state to game forecasts (`status`, `points`, `clock` on locked rows; `points_so_far`, `to_play` per team) and make `games.update_games` read `live.json` when present, and verify tests show live rows in the forecast and log entries that keep locked players' pre-kickoff projections
- [x] 2.4 Run `python -m ffapp simulate` on the real store with a schedule file edited to put week 11 in progress, and verify `live.json` appears, `asof_10.json` is byte-identical before and after, and the edit is reverted afterwards

## 3. Win probability added

- [x] 3.1 Store `margin_mean` and `margin_sd` on every prediction-of-record game and compute a provisional `baseline` per game for the live week each run, and verify tests check both against the simulated arrays
- [x] 3.2 Implement win probability added per starter (final and in-progress formulas from the design, sign by side, pre-week fallback using the forecast's margin) stored as `wpa`, and verify tests reproduce the spec's +22 example within 2 points, a dud's negative value, no value before kickoff, and independence from teammates' scores
- [x] 3.3 Document live scoring, the frozen as-of rule and win probability added in the README's Games section and verify the formulas there match the code

## 4. Export and Predictions page

- [x] 4.1 Export the live result into the league file when present (`teams`, `live`, previous as-of week, history from as-of files only) and live state, `to_play`, `points_so_far`, per-starter status and `wpa` into the games week files, and verify `tests/test_export.py` and `tests/test_games_export.py` cover a live league file, a non-live one, and WPA present only for scored starters
- [x] 4.2 Show "Live: N of M games final · updated …" on the Predictions page while live and keep the history chart on as-of points, and verify in the browser against an exported live file

## 5. Live cards

- [x] 5.1 Add the `--live` token per theme and the LIVE badge (inline SVG, animated gradient on the arcs, red dot, still under reduced motion), and verify by screenshots in both themes and with reduced motion emulated
- [x] 5.2 Show points so far beside the projected final and the to-play count on live cards, and verify on a live week in the browser
- [x] 5.3 Show player status (green dot and clock in progress, bold "F" final, grey kickoff time scheduled) and win probability added (green positive, red negative, hidden before kickoff) in key players and full lineups on live and finished weeks, with the note that values show size and do not add up, and verify on a live week and on finished week 9

## 6. Manual refresh

- [x] 6.1 Write `relay/worker.js` (`GET /status`, `POST /refresh`, CORS to the site origin, cooldown from the workflow's runs and jobs, dispatch with `ref: main`) and `relay/worker.test.mjs`, and verify `node --test relay/worker.test.mjs` covers available, held (minutes left), a queued manual run, a skipped hourly run not counting, two quick requests starting one run, and a foreign origin refused
- [x] 6.2 Add the optional `site.refresh_url` config block with validation, export it and the last successful refresh time into `site/data/index.json`, and verify `tests/test_config.py` and `tests/test_export.py` cover present, absent and invalid values
- [x] 6.3 Add the Refresh button beside "How good are these odds?" on both pages (hidden without a URL; status polled on load and every minute; "Updated N min ago" / "Available in N min" / started confirmation / relay-down message), and verify in the browser against a local stub relay for each state and with no URL configured
- [x] 6.4 Write `relay/README.md` (token scope, Worker creation, secrets, `npx wrangler deploy`, config entry) and verify every command and setting named there matches the code

## 7. Integration

- [x] 7.1 Run `pytest`, `node --test relay/worker.test.mjs`, `openspec validate live-games --strict` and `python -m ffapp refresh`, and verify all pass with no live file written when no game has kicked off
- [x] 7.2 Update the roadmap memory note with the live-games decisions and remaining backlog

## Workflow follow-up

- Commit and push after the user's review, then archive the change with spec sync.
- The user deploys the relay by following `relay/README.md`; until then the button stays hidden.
