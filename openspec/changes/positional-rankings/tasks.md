# Tasks

## 1. WAR merged cut

- [x] 1.1 In `src/ffapp/war.py`, make `cut_mode()` return `merged` when some but not all scored weeks have a weekly snapshot, and build the merged start percentage:
  - the highest `started` across weekly snapshots of scored weeks the player played
  - otherwise `owned` from the most recent weekly snapshot
  - otherwise `owned` from `season.json`
  - ties broken by ESPN id

  Weeks with their own snapshot rank by it. Add a comment block above the merged-ranking code giving the reason, and point it to the README subsection. Verify: unit tests for the spec scenarios (partly captured season, bye in the snapshot week, injured before weekly capture, snapshot of an unfinished week) pass, and existing yearly and weekly cut tests still pass.
- [x] 1.2 Re-run `python -m ffapp war` on the real store and report the 2026 replacement levels per position for both leagues next to the 2021 to 2025 range. Verify: `data/war/{redraft,dynasty}/2026.json` say `"cut": "merged"`, 2021 to 2025 files are unchanged apart from timestamps, and the before/after table is recorded for the README.
- [x] 1.3 Update the Player WAR page note in `site/war.js` and the export index (`first_weekly` logic in `src/ffapp/export.py`), so a `merged` season shows the merged-cut note and never the yearly note. Verify: export test for the index and a browser check of the 2026 and 2023 notes.
- [x] 1.4 Add a "Current-season start percentages" subsection to the README's Player WAR section. It covers:
  - why the in-season season snapshot is one week's view (the week 11 match, Josh Jacobs owned 91.5% / started 8.6%)
  - the merged rule and the ownership fallback, with the reason for each
  - why past and fully captured seasons are untouched
  - the before/after 2026 levels from 1.2

  Verify: the subsection exists and the commands it names run as written.

## 2. Positional rankings data

- [x] 2.1 Add `src/ffapp/positions.py`. It builds one league-season:
  - roster players (`players` ∪ `taxi` ∪ `reserve`), limited to the league's lineup positions, with taxi and reserve flags
  - points per game: actual over final weeks played, plus projections above 0 for the remaining regular-season weeks, over the count of those weeks; the live week counts as projected
  - games played and games projected; players with zero points left out
  - an injured flag (IR or Out, from the latest injury file) for the season in progress only
  - per-position replacement levels from the WAR file, or none if it is missing

  Verify: unit tests for the spec scenarios (mid-season blend 14.45, not yet played 6.0, nothing scored or projected, completed season, no kicker slot, out this week, past season no flags, WAR missing).
- [x] 2.2 Compute the fixed axis per league and position across all seasons (low = min(0, floor5 of the 1st percentile), high = ceil5 of the max of the 99th percentile and the highest replacement level), and write it into every season. Verify: a unit test shows the same QB range in every season and an outlier left outside it.
- [x] 2.3 Extend `export_site` to write `site/data/<league>/positions/<season>.json` for every stored season plus `positions/index.json` (seasons, current), and a `positions` entry per league in `site/data/index.json`. Verify: export tests for files per season, the index, determinism apart from timestamps, and that a missing WAR file still exports. Run `python -m ffapp export` on the real store and inspect redraft 2025 RB and dynasty 2026 QB.

## 3. Positions page

- [x] 3.1 Add the "Positions" sub-tab between Games and Player WAR in `site/index.html`, with a `#page-positions` section: title "Positional Rankings", a season select, a note line and a chart grid. Wire `showPage`, the hash (`#<league>/positions`) and league switching in `site/app.js`, and import the new module with `?v=__BUILD__`. Verify: `tests/test_site_files.py` passes, and a link to `#redraft/positions` opens the page.
- [x] 3.2 Build `site/positions.js` with `initPositions`, `loadPositions` and `reloadPositions`:
  - season control defaulting to the current season, labelled "actual through week N plus projections"
  - one SVG chart per position in the QB/RB, WR/TE, K/DEF order, with a lone last chart centred
  - rows sorted by best, then second-best player, then team name, with empty rows at the bottom
  - the "Replacement Level" dotted line, axis ticks and grid lines

  Verify: a browser check of the redraft (6 charts) and dynasty (5 charts, DEF centred) layouts.
- [x] 3.3 Draw the dots:
  - a light fill and dark outline in the manager's colour, by owner user id, with greys for former members
  - a dotted outline for taxi players and a red plus for injured players
  - the top player's last name kept inside the chart
  - edge arrows for out-of-range values
  - deterministic lane offsets (0, ±6, ±12 px; ±18 px if needed) for dots closer than 14 px

  Verify: a browser check of a dynasty RB row with close values, a taxi player, an injured player and an outlier.
- [x] 3.4 Add the popup: focusable dots with an `aria-label`, and one shared popup per chart showing the name and PPG to one decimal on hover, focus or tap, clamped inside the card. Verify: a browser check on desktop and at 375 px; the popup never widens the page.
- [x] 3.5 Styles in `site/styles.css`: the chart grid (two columns, one below 760 px), the label column truncating on phones, dark mode colours from tokens, and a `.pos-scroll`-style containment so nothing positioned escapes. Verify: the wide-font layout test passes for the new views.
- [x] 3.6 Register `reloadPositions` with the update loop in `app.js`, so a data swap redraws the page and keeps the season. Verify: the layout check's data-swap test extended to the Positions page keeps the season.

## 4. Swipeable sub-tabs

- [x] 4.1 Make `.subtabs` scroll sideways when it overflows: snap, hidden scroll bar, `overscroll-behavior-x: contain`, and `fade-left` / `fade-right` mask classes toggled by a scroll and resize handler. The selected tab is brought into view by setting `scrollLeft` on load and on a sub-tab change. Verify: at 375 px, swiping or scrolling the strip leaves `scrollY` unchanged, a link to `#dynasty/war` shows Player WAR inside the strip, and at 1280 px the menu has no overflow and no fade.

## 5. Layout check and tests

- [x] 5.1 Update `tests/layout/controls.py`:
  - views "positions" and "positions-past"
  - the sub-tab states including "positions"
  - controls "positions season" (other season; region = page content) and "position dot" (hover and focus; region = popup)
  - the new views added to the coverage and wide-font lists

  Verify: `test_every_control_is_listed` and every new control state pass at all four widths.
- [x] 5.2 Add layout tests:
  - the sub-tab strip at 375 px (it scrolls, the page doesn't, the linked tab is visible, the page doesn't move when the strip scrolls)
  - charts stay inside the screen at 375 px with the top player's name inside its chart
  - no two dots in any row overlap by more than 2 px after the lane offsets

  Verify: `LAYOUT_REQUIRED=1 pytest tests/layout` passes.

## 6. Verify and document

- [x] 6.1 README: a "Positional Rankings" section (what the page shows, points per game, replacement line from WAR, row order, rosters, flags, the fixed axis and its edge arrows), the new site data files in the data layout, and the four sub-tabs. Verify: the section exists and matches the built behaviour.
- [x] 6.2 Run `pytest`, `node --test relay/worker.test.mjs` and `LAYOUT_REQUIRED=1 pytest tests/layout`. Take screenshots of the Positions page at 1280 and 375 px in light and dark modes for the user. Verify: all pass and the screenshots are shown to the user.
- [x] 6.3 `openspec validate positional-rankings --strict`. Verify: it passes.

## Workflow follow-up

- Commit, push and archive with spec sync when the user asks. The new capabilities `positional-rankings` and `positional-rankings-page` create main specs; `player-war`, `war-leaderboard-page` and `league-odds-site` are modified.
- After deploy, the user judges the fixed axis on the live charts and may ask for a dynamic one.
