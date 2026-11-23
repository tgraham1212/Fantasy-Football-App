# Tasks

## 1. Storage Tiers

- [x] 1.1 Split game files: `Store.write_games` writes `log` and `record` to `data/games/` and the `forecast`, `views` and `baseline` parts to `data/games-derived/`; `read_games` merges them. Verify: `tests/test_games*.py` pass unchanged, and a round trip returns the same payload
- [x] 1.2 Projection log covers the current week only (`games.py`); future weeks get no entries. Verify: a test where week 12 projections change during week 11 adds no week-12 entries
- [x] 1.3 `ffapp build`: rebuild ratings, replacement levels, WAR, game views and baseline, and the export offline from committed records, with no network calls. Verify: a test runs it on a fixture store with networking blocked and gets `site/data`
- [x] 1.4 Projections: write future-week files to a git-ignored location in the build cache, and keep current and earlier weeks tracked. When they are missing, the simulation falls back to the latest stored week and logs it. Verify: unit test of the fallback
- [x] 1.5 Move `last_run.json` and `live.json` out of git (ignored paths); export still sets `index.last_refresh`. Verify: update `test_refresh.py` and `test_export.py`
- [x] 1.6 `.gitignore` the derived paths and untrack them with `git rm --cached` (history kept). Verify: `git ls-files` lists none of them
- [x] 1.7 `tests/test_storage_tiers.py`: fails when a rebuilt path is tracked, when a `data/` folder is in neither list of `docs/refresh-modes.md`, or when `ffapp build` fails on committed records. Verify: the test passes, and fails when a test-only extra folder is added
- [x] 1.8 Layout and accessibility tests: a session fixture runs `ffapp build` when `site/data` is missing. Verify: the layout check passes from a clean checkout

## 2. Cold Run

- [x] 2.1 Records: slate forecasts. When every game of a slate is final, `refresh` writes the league forecast to `data/odds/<league>/<season>/slates_NN.json`, keyed by kickoff time and never overwritten. Verify: unit test with three slates
- [x] 2.2 `refresh --mode live` skips the simulation and keeps the forecast of record steps. Verify: test that no simulation runs and records still update
- [x] 2.3 Schedule summary: the schedule step writes the summary JSON (kickoffs, slates, seasons over, NFL week) and its hash. Verify: unit test of the summary from a fixture schedule
- [x] 2.4 `ffapp site-hash`: a hash of `site/` ignoring `generated_at` and `last_refresh`. Verify: the same data with new timestamps gives the same hash
- [x] 2.5 `refresh.yml`:
  - remove the gate job and `pytest`;
  - add a `mode` input;
  - restore the previous build cache;
  - commit records only on change;
  - `PUT /schedule` when the summary hash changed;
  - save the build cache keyed `build-<sha>`;
  - deploy only on commit or a changed site hash;
  - keep the daily `0 11 * * *` cron.

  Verify: workflow checks in `tests/test_site_files.py` (or a new `tests/test_workflows.py`) cover the steps, and `stamp-site` still runs before every upload
- [x] 2.6 Remove `should-run`, `should_run` and its spacing logic, and `tests/test_should_run.py`. Verify: the CLI help no longer lists it, and the suite passes

## 3. Hot Run

- [x] 3.1 `ffapp hot`: current-week matchups, scoreboard, simulation, current-week game cards, into a scratch folder. It writes one bundle file (forecast and current-week games per league, game status, base commit, time) and never touches `data/`. Verify: `tests/test_hot.py` on fixtures checks the bundle's shape and that `data/` is unchanged
- [x] 3.2 The bundle's content hash; skip the upload when it equals the previous bundle's. Verify: unit test
- [x] 3.3 `.github/workflows/hot.yml`:
  - `workflow_dispatch` only;
  - concurrency group `hot`;
  - read-only permissions;
  - restore the build cache, falling back to `ffapp build`;
  - run `ffapp hot`;
  - `PUT /live` with `HOT_TOKEN`.

  Verify: a workflow test checks there is no commit, push or Pages step
- [x] 3.4 `site.yml`: restore the build cache or run `ffapp build` before tests and deploy. Verify: workflow test, then a code-push deploy on the live site

## 4. Relay

- [x] 4.1 `mode(now, summary, status)`: Off-season, Quiet or Live, with the 6-hours-after-kickoff rule and slate-final detection. Verify: `worker.test.mjs` cases for every mode, each of the 5 transitions and a stuck status
- [x] 4.2 Scheduled handler (every minute):
  - dispatch `hot.yml` when due and none is queued or running (remembering its own dispatch for 60 s);
  - dispatch `refresh.yml` every 15 minutes in Quiet and Live, and on slate final;
  - stop hot dispatches at 950 KV writes in a UTC day.

  Verify: worker tests with a fake clock and GitHub
- [x] 4.3 KV endpoints:
  - `GET /live` (site origin, cached 15 s);
  - `PUT /live` and `PUT /schedule` (with `HOT_TOKEN`, others refused);
  - bundle TTL of 7 days;
  - a daily write counter.

  Verify: worker tests
- [x] 4.4 Button rules:
  - `GET /status` returns `mode` and `reason`;
  - `POST /refresh` dispatches by mode (Quiet: both runs; Off-season: cold), and is refused in Live and while a hot run is going;
  - 5-minute button cooldown.

  Verify: worker tests for each case, including two clicks at once
- [x] 4.5 `relay/README.md`: KV namespace, `HOT_TOKEN` (Cloudflare and GitHub), the cron trigger and the setup order. Verify: the steps are followed in 6.2

## 5. Page

- [x] 5.1 `updates.js`: fetch `GET /live`, 30 s while a game is in progress and 60 s otherwise; newest wins against the static files; overlay the bundle's files in the data loader so week switches see them; ignore older bundles; keep the view when the relay is down. Verify: layout tests serve an older and a newer bundle with `page.route`, and the visitor's place is kept
- [x] 5.2 `refresh.js`: notes by `mode` and `reason`: "Live updates on" (disabled), "Available in N min", "Started, back in ~1 min", a 10-minute give-up, and "Updated" from the newer of the bundle and the static files. Verify: layout test per note, with nothing moving and the note within the screen at every width
- [x] 5.3 Copy IDs for the new notes and tooltips; run `python -m ffapp site-copy`. Verify: the copy tests pass, and I ask before any `--apply`
- [x] 5.4 Layout registry and accessibility: the button's new states in `tests/layout/controls.py`; axe in light and dark mode. Verify: the layout check passes

## 6. Docs and Rollout

- [x] 6.1 Finish `docs/refresh-modes.md` (remove the "planned" status line, and check the file names and commands match the code); regenerate the diagram with `python -X utf8 tools/refresh_modes_diagram.py`; link it from the README's refresh section, and add `ffapp build` to the README's local-run steps. Verify: the links resolve and the diagram matches the doc's wording
- [x] 6.2 Owner steps, then verify on the live site: create the KV namespace, set `HOT_TOKEN` in Cloudflare and GitHub, `wrangler deploy`, and run `hot.yml` once by hand. Verify: the page swaps in the bundle and the button shows the right note
- [x] 6.3 Enable the Worker's cron trigger, and remove `refresh.yml`'s hourly cron. Verify: across a Quiet hour, about 4 hot and 4 cold runs, with commits and deploys only on change
- [x] 6.4 Live check during the next game window: hot runs back to back, the page updates within about 2 minutes, slate-final cold runs store slate forecasts, and the KV write count stays within budget. Verify: Actions history and the Worker's write counter
- [x] 6.5 `Calculations.txt` section 10: the log covers the current week only, appended by cold runs every 15 minutes, plus slate forecasts. Verify: the section matches the code

## 7. Commit Only Real Changes (found in the 6.3 check)

- [x] 7.1 Projections and stats: replace a stored record only when a value other than `last_modified` changed. Verify: unit tests for a touched-but-same row and a real correction
- [x] 7.2 `ffapp hold-tallies`: after `git add data`, unstage and restore changed trending and ESPN snapshot files whose committed copy was saved on the same UTC day; `refresh.yml` runs it before committing. Verify: unit tests in a temporary git repository, workflow test
- [x] 7.3 `docs/refresh-modes.md`: the once-a-day rule for tallies under "Committed". Verify: doc tests

## Workflow follow-up

- Commit, push and archive with spec sync when the owner asks.
