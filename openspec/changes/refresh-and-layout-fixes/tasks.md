# Tasks

## 1. Code fingerprint and deploys

- [x] 1.1 Add `ffapp stamp-site`: fingerprint every file under `site/` except `site/data/` (sorted paths, LF-normalised bytes, SHA-256, first 10 hex), replace `__BUILD__` in `site/*.html` and `site/*.js`, write `site/version.json`; add `site/version.js` exporting `CODE = "__BUILD__"`
- [x] 1.2 Add `?v=__BUILD__` to the stylesheet links in `site/index.html` and `site/calibration.html`
- [x] 1.3 Switch `refresh.yml` from the `sed` stamp to `python -m ffapp stamp-site`
- [x] 1.4 Add `.github/workflows/site.yml`: on code pushes to `main`, a test job (`pip install -e ".[dev,browser]"`, `pytest` with `LAYOUT_REQUIRED=1`) and a deploy job that runs `stamp-site` and deploys Pages, in the `refresh-odds` concurrency group
- [x] 1.5 Extend `tests/test_site_files.py`: stylesheet links carry the placeholder; every workflow using `deploy-pages` runs `ffapp stamp-site` before the upload; the fingerprint ignores `site/data/`, is stable across runs, and changes when a script changes; add tests for the stamp command's output
- [x] 1.6 Record the rule: README deploy section, and a project `context` entry in `openspec/config.yaml` (every deploy goes through `ffapp stamp-site`, new site references carry `?v=__BUILD__`, every new control is added to the layout check)

## 2. Layout fixes

- [x] 2.1 Refresh note: non-wrapping button label, reserved note line, messages of at most 22 characters with the full sentence as tooltip, phone layout beside the button with ellipsis
- [x] 2.2 Full-list overlay: flex-column dialog with no own scroll, `position: relative` table wrapper that fills the remaining height
- [x] 2.3 Phone lineups: one-column `.game-players` below 560 px, "Free agent" with the "(replacement level)" part hidden below 560 px

## 3. Live updates

- [x] 3.1 URL hash carries the Games week (`#<league>/games/<week>`); restore it on load
- [x] 3.2 `games.js`: key per-card view state, open lineups and charts by game key instead of card index
- [x] 3.3 Reload hooks that clear caches and redraw the open view keeping state: `app.js`, `games.js` (fall back to the default week when the week is gone), `war.js` (season, sort, open dialog and its sort), `calibration.js`
- [x] 3.4 `site/updates.js`: minute check while visible (and once on becoming visible), version note pinned to the bottom with a Refresh button, data swap through the hooks when the code is unchanged, data-arrived signal to `refresh.js`; load it on both pages
- [x] 3.5 `refresh.js`: short started/failed messages, "Updated just now" on the data-arrived signal, "Refresh didn't finish" after 20 minutes without new data

## 4. Layout check

- [x] 4.1 Add the optional dependency group `browser = ["playwright"]` and the `tests/layout/` harness: static server fixture, Chrome via `channel="chrome"`, skip without Playwright or Chrome unless `LAYOUT_REQUIRED=1`, mocked relay, `version.json` and `index.json` through `page.route`
- [x] 4.2 Registry `tests/layout/controls.py` covering every control on the predictions, Games, Player WAR and calibration pages with states and declared effects (refresh idle, held, started, failed; league switcher; sub-tabs; theme; week arrows and select; Model/Actual; Full Lineup; table sorts and highlights; WAR season and mode controls, Full list open, sort and close; calibration controls; version note; data swap)
- [x] 4.3 Tests: no sideways scroll at 375, 768, 1000 and 1280 px; no unintended moves per control state and width; coverage test fails on any unlisted control
- [x] 4.4 Run the layout check locally against the fixed site and confirm it fails on the pre-fix refresh note and dialog, then passes after the fixes
- [x] 4.5 Fix what the check found beyond the planned items: the Player WAR leaderboard tables scrolled the whole page sideways at 375 and 768 px (All-Time year column, long names); each table now scrolls inside its card

## 5. Verify and document

- [x] 5.1 Run `pytest`, `node --test relay/worker.test.mjs` and the layout check; check the live swap and the version note by hand on a local server with a stamped copy
- [x] 5.2 README: live updates, the version note, the layout check and how to run it locally (`pip install -e ".[dev,browser]"`, `LAYOUT_REQUIRED=1 pytest tests/layout`)
- [x] 5.3 `openspec validate refresh-and-layout-fixes --strict`
