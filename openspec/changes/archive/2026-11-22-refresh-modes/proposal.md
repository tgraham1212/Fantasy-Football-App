# Proposal

## Why

Today every refresh goes through the same slow path: a gate job, the full test suite, a 55-second rebuild, a commit and a GitHub Pages deploy. So a button press takes about 7 to 9 minutes to reach the screen, live games refresh at most every 3 hours, and every run commits regenerated files. About 90% of the repository's growth comes from data that is either recomputable or only matters in its latest version.

Splitting the refresh into a fast **hot** path for live data and a durable **cold** path for records fixes all three problems. The hot path writes to Cloudflare, so it never commits or deploys. The cold path commits only real records, and only when they change.

## What Changes

- **Three refresh modes:** Off-season, Quiet (in season, no game in progress) and Live (a game in progress). The refresh relay's Worker becomes the clock: every minute it works out the mode and starts whichever runs are due. The modes, transitions and both runs are documented in `docs/refresh-modes.md` with a generated diagram.
- **Hot run** (new workflow `hot.yml`, command `ffapp hot`):
  - fetches the current week's matchups and the scoreboard, simulates the live week and builds this week's game cards;
  - writes them to Cloudflare KV as **one bundle**;
  - runs back to back in Live (about every 1 to 1.5 minutes), every 15 minutes in Quiet, and is off in the off-season;
  - never commits or deploys.
- **Cold run** (the existing `refresh.yml`, reworked):
  - runs every 15 minutes in Quiet and Live, when a slate goes final, daily in the off-season, and from the button;
  - commits only when a record changed, and deploys only when the commit or the rebuilt site changed;
  - skips the simulation in Live, since the hot runs own the live forecast;
  - saves each slate's forecast to history when the slate goes final.
- **BREAKING (for local work):** derived data is no longer committed. That covers `site/data`, ratings, replacement levels, WAR, future-week projections, the live forecast, the game files' forecast, views and baseline parts, and the last-run time.
  - Cold runs rebuild these files and save them to a GitHub Actions build cache, which hot runs restore.
  - The code-push deploy builds them as well.
  - A new `ffapp build` command rebuilds them offline for local viewing.
  - Their earlier history stays in git.
- **The game log covers the current week only** and is appended by cold runs, so a player's kickoff-frozen projection is at most 15 minutes old (today it can be 3 hours old).
- **The page reads the live bundle** from the relay: every 30 seconds in Live and every 60 seconds in Quiet. It shows the bundle when it is newer than the static files.
- **The Refresh Data button:**
  - starts a hot run and a cold run in Quiet, so new data shows in about 1 to 1.5 minutes;
  - starts a cold run in the off-season;
  - is held in Live, with the note "Live updates on";
  - its 15-minute cooldown becomes 5 minutes, and it is also refused while a hot run is going.
- **Removed:**
  - the hourly check, the `should-run` gate job and its 3-hour spacing rule;
  - the full test suite inside the data refresh. Tests and the layout check still run on every code push.
- **A test keeps the storage tiers honest:** it fails when a derived path is tracked by git, or when the site cannot be built from the committed records alone.

## Capabilities

### New Capabilities
- `live-refresh`: the hot run, its inputs from the cold build cache, the single KV bundle, how the relay serves it, and the KV write budget.
- `data-storage-tiers`: which data is a record kept in git, which is derived and rebuilt, where each tier lives and how long, the offline build command, commit-only-on-change, and the test that enforces the tiers.

### Modified Capabilities
- `refresh-scheduling`:
  - the hourly check and run spacing are replaced by the three refresh modes, their transitions and per-mode cadences, run by the Worker clock;
  - adds the slate-final cold run, the daily fallback, and the refresh-modes document and diagram.
- `manual-refresh`:
  - the relay also runs the clock and serves the bundle;
  - the cooldown changes to 5 minutes plus "no hot run going";
  - the button's per-mode behaviour and notes change.
- `site-updates`: the update check also reads the live bundle, every 30 seconds in Live, and swaps it in place like deployed data.
- `league-odds-site`:
  - "Scheduled refresh" now describes the cold run, which commits records only and deploys only on change;
  - "Deploy on code push" builds the site data before testing and deploying.
- `game-predictions`:
  - the projection log covers the current week only and is appended by cold runs;
  - game files store the log and record, with forecast and views rebuilt;
  - adds slate forecasts.

## Impact

- **Relay:** `relay/worker.js` gains a scheduled handler (Cloudflare cron, every minute), a KV namespace binding, `GET /live`, `PUT /live` (for the hot job, with its own secret) and mode logic; `relay/README.md` and `relay/worker.test.mjs` are updated. New Cloudflare settings: a KV namespace and a `HOT_TOKEN` secret, also stored as a GitHub Actions secret.
- **Workflows:**
  - new `.github/workflows/hot.yml`, with its own concurrency group so it never waits behind a cold run;
  - `refresh.yml` loses the gate job and pytest, and gains the build cache, commit-on-change and deploy-on-change;
  - `site.yml` builds site data before testing and deploying.
- **Python:**
  - new `ffapp hot` and `ffapp build` commands;
  - `ffapp refresh` gains mode-aware steps and the schedule summary;
  - `games.py` changes the log scope and adds slate forecasts;
  - the game file is split into its record and derived parts;
  - `schedule.py` loses `should_run`, which moves to the Worker's mode logic.
- **Site:** `site/updates.js` and `site/refresh.js` change (new notes, with copy IDs, and `site-copy` is run).
- **Git:** `.gitignore` gains the derived paths, which are removed from the index (not from history).
- **Docs:**
  - `docs/refresh-modes.md`, `docs/images/refresh-modes/diagram.svg` and `tools/refresh_modes_diagram.py` (drafted during the explore);
  - the README's refresh section links them;
  - `Calculations.txt` section 10 notes the log's current-week scope and cadence.
- **Tests:**
  - `test_should_run.py` is removed;
  - `test_refresh.py` and `test_export.py` are updated for the last-run time leaving git;
  - new `test_hot.py` and `test_storage_tiers.py`.
- **Limits:** about 500 KV writes on a full Sunday, against Cloudflare's free 1,000 a day. GitHub Pages deploys drop to a few an hour at most.
