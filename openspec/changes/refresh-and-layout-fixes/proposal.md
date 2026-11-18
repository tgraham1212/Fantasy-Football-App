# Proposal

## Why

Rendering the site at several widths showed layout faults that break the page outside one desktop width: the refresh note overflows the screen or pushes the page tabs down, the Player WAR full list opens with a second scroll bar, and on phones a game card gives each player name about 22 px. Visitors also have to reload the page by hand to see a refresh they started, and nothing tells them when new site code is live. Nothing tests the layout, so faults like these ship unnoticed.

## What Changes

- **Refresh note.** The button text never wraps and the note has a fixed space, so starting a refresh moves nothing. Long messages show as a short line ("Started, back in ~5 min") with the full text in a tooltip; on phones the note sits beside the button.
- **Full list overlay.** The table is the overlay's only scroll area: hidden screen-reader labels are contained by the scrolling table, and the table fills the overlay's remaining height.
- **Phone lineups.** Below 560 px each game card stacks the two teams' lineups, so names get the card's width; "Free agent (replacement level)" shortens to "Free agent" there.
- **Live data updates.** While a page is visible it checks every minute whether newer data or newer code is deployed. Newer data with the same code is swapped in place, keeping the visitor's place (league, page, Games week, each card's Model/Actual view, open lineups, sort, highlighted team, an open full list). After a visitor starts a refresh, the note says when the new data arrived, or that the refresh did not finish after 20 minutes.
- **New version note.** When the deployed site code differs from the page's, a note pinned to the bottom of the screen says a new version is available, with a Refresh button; it stays until the page is reloaded, and no data is swapped under old code.
- **Code fingerprint (BREAKING for the deploy step).** Script and stylesheet URLs are stamped with a fingerprint of the site's code files instead of the commit id, and every deploy publishes that fingerprint in `version.json`. One stamping command is used by every deploy. Browsers stop re-downloading unchanged scripts after each hourly data refresh, and the stylesheet gains the stamp it lacked.
- **Deploy on code push.** A push to `main` that changes site code runs the tests and layout check and deploys the site, so the new version note reaches visitors without waiting for the next data refresh.
- **Layout check.** A browser test loads each page at phone, tablet and desktop widths, drives every button through its states (refresh responses mocked) and fails when an element moves that the control is not designed to move, or when the page scrolls sideways. It runs in the code-push workflow, never in the data refresh, and every new button must be added to it.

## Capabilities

### New Capabilities
- `site-updates`: the page's minute check for newer data and code, the in-place data swap that keeps the visitor's place, and the new version note.
- `layout-checks`: the browser layout test, its widths and control states, what counts as an unintended move, and the rule that every control is covered.

### Modified Capabilities
- `league-odds-site`: "Fresh scripts after deploy" becomes a code fingerprint covering scripts and the stylesheet, published in `version.json` by one stamping command; site code pushes deploy.
- `manual-refresh`: the refresh button's note keeps a fixed space, short messages with a tooltip, and reports when started data arrived or did not.
- `war-leaderboard-page`: the expanded list overlay has a single scroll area, the table.
- `games-page`: player rows stack per team on phones and the free-agent label shortens.

## Impact

- Site: `site/refresh.js` (note, polling hand-off), new `site/updates.js` (minute check, swap, version note), `site/app.js`, `site/games.js`, `site/war.js`, `site/calibration.js` (reload hooks that keep state; Games week in the URL hash), `site/index.html`, `site/calibration.html` (stylesheet stamp, note element), `site/styles.css`.
- Deploy: new stamping command (`python -m ffapp stamp-site`), `.github/workflows/refresh.yml` uses it, new `.github/workflows/site.yml` (tests, layout check, deploy on code push; shares the refresh concurrency group).
- Tests: `tests/test_site_files.py` (stylesheet stamp, fingerprint is stable and ignores `site/data`), new `tests/layout/` (Playwright for Python, skipped when Playwright is not installed). New optional dependency group `browser = ["playwright"]`; the layout check uses the installed Chrome (`channel="chrome"`), so no browser download.
- Docs: README deploy section and the project's OpenSpec config context get the fingerprint rule.
- Out of scope: pushing updates to the page from the server (the page polls), and a layout check inside the data refresh.
