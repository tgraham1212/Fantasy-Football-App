# Design

## Context

See proposal.md for motivation. Current state:

- The workflow `refresh.yml` is the only deploy. After the data commit it runs `sed -i "s/__BUILD__/$(git rev-parse --short HEAD)/g" site/*.html site/*.js`, so every data commit gives every script a new URL. `styles.css` has no stamp. User pushes deploy only at the next refresh run.
- Data fetches use `cache: "no-cache"`; GitHub Pages answers with an ETag and `Cache-Control: max-age=600`, so revalidation returns 304 when nothing changed. `data/index.json` carries `last_refresh` (the start time of the last refresh run), rewritten on every run.
- League and page are in the URL hash (`#<league>/war`); the Games week and card states are module state only. `games.js` keys charts and per-card view state by card index; `war.js` caches seasons and keeps `dialogPos`.
- `.refresh-note` is absolutely positioned and centred under the button; long messages overflow the screen at 1000 px and below, and on phones the label wraps and shifts the tabs (measured: 22 px).
- The full-list dialog's table wrapper is not positioned, so the `.sr-only` spans (absolute) inside the table use the dialog as containing block and extend its scroll height (measured: 1997 px in a 654 px dialog).
- On a 375 px phone a lineup row is 143 px wide and a name gets 22 px.

## Goals / Non-Goals

**Goals:**
- One stamping command that every deploy uses; the stamp depends only on site code content.
- An update loop that never reloads the page for data and never pairs old code with new data.
- A layout check that runs headless on GitHub's runners without downloading a browser.

**Non-Goals:**
- Server push (SSE or WebSocket); Pages is static.
- Pixel-diff screenshots; the check compares element boxes, which is stable across fonts and data.

## Decisions

**1. Code fingerprint via `ffapp stamp-site`.** A new CLI command hashes (SHA-256, first 10 hex) the sorted relative paths and LF-normalised bytes of every file under `site/` except `site/data/`, before stamping. It then replaces `__BUILD__` in `site/*.html` and `site/*.js` and writes `site/version.json` = `{"code": "<fp>"}`. The page learns its own fingerprint from a new `site/version.js` exporting `CODE = "__BUILD__"`, stamped like any other reference. Stylesheet links gain `?v=__BUILD__`. Both deploy workflows call the command; `tests/test_site_files.py` checks that every workflow using `deploy-pages` runs `ffapp stamp-site` before `upload-pages-artifact`, that stylesheet links carry the placeholder, and that the fingerprint ignores `site/data/` and is stable across runs. Alternative: the last commit touching site code (`git log -1 -- site ':!site/data'`). Rejected: it needs full history in the checkout and can differ from what is actually uploaded.

**2. Where the rule lives.** The behaviour is the `league-odds-site` requirement "Fresh scripts after deploy"; enforcement is `tests/test_site_files.py`; the README deploy section documents the command; `openspec/config.yaml` gains a project `context` entry stating that every deploy goes through `ffapp stamp-site`, new site references carry `?v=__BUILD__`, and new controls are added to the layout check, so future changes plan for it.

**3. Update loop in `site/updates.js`.** Every 60 s while `document.visibilityState === "visible"`, and once on becoming visible, it fetches `version.json` and `data/index.json` with `cache: "no-cache"`. If `CODE` is stamped and differs from `version.json.code`, it shows the version note and stops swapping. Otherwise, if `index.last_refresh` is newer than the loaded one, it calls the registered reload hooks and tells `refresh.js` the data arrived. `refresh.js` keeps its relay `/status` poll for the held minutes only. Alternative: poll the relay for run status. Rejected: a finished run is not yet a visible deploy, and data is what the visitor waits for.

**4. Reload hooks keep state.** Each module exposes `reload()` that clears its data cache and redraws the open view from its existing state: `app.js` (league JSON, index, odds table sort, highlighted team, charts), `games.js` (week cache; per-card view and open lineups move from card index to game key so they survive a redraw), `war.js` (season cache; season, sort, and an open dialog with its sort), `calibration.js` (its JSON). If the selected Games week disappears, the default week is used. Charts are destroyed and recreated in the same fixed-height containers. The URL hash becomes `#<league>/<page>[/<week>]` so a reload keeps the week.

**5. Refresh note in a fixed space.** The button gets `white-space: nowrap`. `.refresh` reserves one note line with bottom padding, and the note sits absolutely in that line, centred, with messages of at most 22 characters ("Started, back in ~5 min", "Couldn't start, try later", "Refresh didn't finish", "Updated just now") and the full sentence in `title`. At 0.75rem, 22 characters stay inside the 16 px gutter even when the 110 px button sits at the screen edge. On phones the note is in flow beside the button with a fixed width and ellipsis. The 20-minute "didn't finish" timer starts on a 202 from the relay and is cleared by the update loop's data-arrived signal.

**6. Full-list overlay.** `dialog#war-dialog[open]` becomes a flex column with `max-height: calc(100vh - 48px)` and `overflow: hidden`; `.dialog-table` gets `position: relative` (containing the `.sr-only` spans), `flex: 1 1 auto` and `min-height: 0`, and loses its own `max-height`.

**7. Phone lineups.** Below 560 px `.game-players` becomes one column; each list already has its team name heading. Replacement fills render as `Free agent<span class="fa-more"> (replacement level)</span>`, and `.fa-more` is hidden below 560 px. With the full card width a name gets about 200 px, enough for every current name (longest measured: 171 px).

**8. Layout check with Playwright for Python.** `tests/layout/` holds a pytest module, a static server fixture (thread, free port, serving `site/`), and `controls.py`, the registry: per page, each control's selector, its states (click, select an option, a mocked relay answer) and its declared effect (`none`, `self`, `below`, or a selector region). For each width (375, 768, 1000, 1280) and each control state, the test records the boxes of landmark elements (header items, tabs, cards, tables, the control itself) before and after, and fails on a change over 0.5 px outside the declared effect, or when `scrollWidth > innerWidth`. A coverage test lists every visible `button`, `select`, `summary` and `.nav-link` on each page and sub-page and fails on any the registry does not match. The relay, `version.json` and `index.json` are served through `page.route`, so no refresh starts and the swap and version note can be driven. The browser is the installed Chrome (`channel="chrome"`, preinstalled on `ubuntu-latest` and present locally), so no browser download. The tests skip when Playwright or Chrome is missing unless `LAYOUT_REQUIRED=1`, which the code-push workflow sets. Alternative: Node with Puppeteer. Rejected: the suite is pytest and Python is already set up in CI.

**9. Code-push workflow `site.yml`.** On push to `main` with paths `site/**`, `!site/data/**`, `src/ffapp/**`, `tests/**` and `.github/workflows/site.yml`: job `test` installs `.[dev,browser]` and runs `pytest` with `LAYOUT_REQUIRED=1`; job `deploy` (needs `test`) checks out, runs `python -m ffapp stamp-site`, and uploads and deploys Pages. It shares the `refresh-odds` concurrency group without cancelling, so it never overlaps a refresh. Pushes made by the refresh workflow use the workflow token and do not trigger it; the path filter excludes data anyway.

**10. Found by the check: WAR leaderboard tables.** At 375 and 768 px the All-Time year column (and long names) made the top-10 tables wider than their cards and the page scrolled sideways. Each table now sits in a `.war-scroll` wrapper that scrolls inside its card, like the other wide tables.

## Risks / Trade-offs

- [Pages' CDN can serve a stale `index.json` briefly after a deploy] -> `no-cache` revalidation; the next minute's check catches up.
- [A failing layout check blocks a code deploy, but the next data refresh deploys whatever is on `main`] -> accepted: the data refresh must never be blocked, and the failure is visible on the push. Fix forward.
- [Box comparison flags sub-pixel shifts from async chart rendering] -> charts are measured after their animation ends, with a 0.5 px tolerance and fixed-height chart containers.
- [Registry upkeep] -> the coverage test makes a missing entry a failure, not a silent gap.
- [Every open tab makes two small requests a minute] -> visible tabs only; unchanged files answer 304.

## Migration Plan

1. Land the stamping command and switch `refresh.yml` to it in the same commit as `version.js` and the stylesheet stamp, so the first deploy publishes `version.json`.
2. Pages already open before that deploy run old code without the update loop; they pick it up on their next reload.
3. Rollback: revert the commit; `refresh.yml` returns to the `sed` stamp and pages ignore the missing `version.json`.
