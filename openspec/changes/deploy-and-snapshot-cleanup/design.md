# Design

## Context

See proposal.md for motivation. Relevant current state:

- `site/index.html` and `site/calibration.html` load `vendor/chart.umd.js` and one module script each (`app.js`, `calibration.js`). `app.js` statically imports `./sorting.js` and `./war.js`; `war.js` imports `./sorting.js`; `calibration.js` imports nothing. Data fetches already use `cache: "no-cache"`, so only scripts and the HTML are subject to the ten-minute Pages cache.
- The deploy is `.github/workflows/refresh.yml`: checkout, test, `ffapp refresh`, commit `data/` and `site/data/`, then `upload-pages-artifact` with `path: site`.
- `capture_snapshots` in `src/ffapp/espn.py` fetches a season snapshot only when `store.read_espn_season(season)` is `None`, and fetches everything before writing anything. League status per season is in the stored `league.json` (`status`: `complete`, `in_season`, and the pre-draft states).

## Goals / Non-Goals

**Goals:**
- A deploy can never pair a new page with an old cached script, with no change to how the site is developed locally.
- The in-progress season's yearly cut converges on end-of-season values without touching completed seasons.
- The validator runs clean in strict mode on the site spec.

**Non-Goals:**
- Changing Pages cache headers (not possible on GitHub Pages) or adding a service worker.
- Any change to what the snapshot files contain or to the WAR model.

## Decisions

**1. Build stamp as a placeholder replaced at deploy time, not at export time.** Source files reference `app.js?v=__BUILD__`, `calibration.js?v=__BUILD__`, `vendor/chart.umd.js?v=__BUILD__` and import `./war.js?v=__BUILD__` and `./sorting.js?v=__BUILD__`. A workflow step runs `sed` over `site/*.html` and `site/*.js` on the runner, replacing `__BUILD__` with the short commit SHA, after the data commit and before `upload-pages-artifact`. Nothing is committed with a real stamp, so the repository never churns and local serving keeps working with the literal placeholder (browsers treat it as an ordinary query string). Alternatives: having `ffapp export` rewrite the HTML (mixes generated content into source files and commits a new stamp every day); an inline bootstrap that reads a stamp from `data/index.json` and uses dynamic imports (works, but turns every static import into a dynamic one and hides the module graph).

**2. Module imports carry the stamp too.** A stamped `app.js` that imports a bare `./war.js` would still get the cached `war.js`. Static import specifiers with a query string are valid ES modules, so each import carries the same placeholder. The HTML page itself can be cached for up to ten minutes, which is fine: an old page references old stamps and gets a consistent old bundle; a new page gets a consistent new one.

**3. A test guards the placeholder.** `tests/test_site_files.py` reads the two HTML files and every `site/*.js`, finds `<script src=...>` and `import ... from "..."` references to local files, and asserts each carries `?v=__BUILD__`. The vendored Chart.js is pinned and never changes between deploys, so stamping it is harmless but not required; the test covers it anyway for uniformity.

**4. In-progress season detection from stored league status.** A season is in progress when any configured league has it stored with a status other than `complete`. `capture_snapshots` fetches a season snapshot when none is stored or the season is in progress; a failed fetch is reported and, because fetching happens before writing, leaves the stored file untouched. The weekly snapshot logic is unchanged. Sleeper marks a season `complete` after the championship, so the frozen value is the one ESPN shows at season end, the same moment past seasons' frozen values come from.

**5. Spec splits follow the sync contract.** Under MODIFIED, the two long requirements keep their headers and every existing scenario with a shorter description; the behaviours removed from the descriptions become ADDED requirements with their own scenarios. The archive merge replaces the two blocks and appends the new ones.

## Risks / Trade-offs

- [Someone adds a script or import without the placeholder] → the test fails and names the file.
- [The `sed` step misses a file type] → only `site/*.html` and `site/*.js` reference scripts; the test's file list and the workflow's glob are the same set, and the README names both.
- [The 2026 snapshot now changes daily until the season completes, so every day's WAR for 2026 shifts slightly] → already true of the season-to-date constants; the page's through-week label covers it.
- [A league left in a non-complete status after the season] → the snapshot would keep refreshing in the offseason, which is wasteful but harmless; the weekly capture already guards on `season_type`.

## Migration Plan

1. Ship; the next scheduled run re-fetches the 2026 season snapshot and stamps the deployed scripts.
2. Rollback: remove the workflow step and the placeholders (the site works with or without them); revert the fetch rule.
