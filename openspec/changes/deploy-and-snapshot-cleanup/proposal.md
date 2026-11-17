# Proposal

## Why

Three small things left over from the last two changes. A deploy today paired the new page with a browser-cached old script, so the Player WAR button did nothing until a hard refresh; GitHub Pages caches every file for ten minutes and browsers keep their own copies, so this will recur on every deploy. The 2026 start-percentage snapshot was frozen the first time it was pulled (17 November), so the season's yearly replacement cut will be judged against a mid-season ranking for weeks that have not happened yet. And two requirements in the site spec have outgrown the validator's length limit, so every validation run warns.

## What Changes

- Script URLs on both site pages, and the module imports between the site's scripts, carry a build placeholder that the deploy workflow replaces with the commit SHA before uploading the site, so a new deploy always fetches fresh code. Locally the placeholder is left as is. A test keeps every script reference stamped.
- The season start-percentage snapshot is re-fetched on every snapshot run while the season is still in progress for any configured league, and frozen once every league has that season stored as complete. Already-complete seasons are never re-fetched, as before.
- The "ELO placeholder columns" and "Calibration page" requirements in `league-odds-site` are split: each keeps one behaviour and its scenarios, and the behaviours cut from their descriptions become requirements of their own. No site behaviour changes.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `league-odds-site`: a new requirement that deployed script URLs are stamped per build; "ELO placeholder columns" and "Calibration page" trimmed to one behaviour each, with the cut behaviours added as "ELO columns before week one", "ELO change fill" and "Odds model explained".
- `start-percentage-snapshots`: "Season snapshot" re-fetches the in-progress season and freezes it on completion.

## Impact

- Code: `site/index.html`, `site/calibration.html`, `site/app.js`, `site/war.js` (placeholder on script URLs and imports); `.github/workflows/refresh.yml` (replace step before the Pages upload); `src/ffapp/espn.py` (season refresh rule); a new test on the site files and new tests in `tests/test_espn.py`; README deploy and snapshot notes.
- Data: `data/espn/2026/season.json` changes on each daily run until the season completes; nothing else.
- Specs: `league-odds-site` and `start-percentage-snapshots` modified.
- Out of scope: moving the rating chart out of `app.js`, renaming the site, compacting the WAR files, and skipping weekly snapshots in playoff weeks, all noted for later.
