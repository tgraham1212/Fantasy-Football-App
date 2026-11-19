# Tasks

## 1. Games tab

- [x] 1.1 Stack `.game-body` below 600 px (replacing the 420 px rule) and shrink `.win` below 600 px. Verify: a screenshot at 440 px shows team rows across the card with the chart beneath.
- [x] 1.2 Rebuild the score block in `teamRow`:
  - finished and live games show the actual or current score as `.num`, then "{mean} forecasted", then "N to play" when live, then the lineup choices moved from `.who`
  - upcoming games show `.num` with "forecast"
  - "forecast" and "forecasted" become copy-marked literals (GAME-13, GAME-14)

  Verify: screenshots of a finished, a live (or mocked live) and an upcoming card at 440 and 1280 px.
- [x] 1.3 Lineup rows as an aligned grid: `ul` grid with `li { display: contents }`, the name column at max-content, points then WPA directly after, kickoff time at the right edge (split `asideTag`); not-playing reasons just after the name. Verify: screenshots at 440 and 1280 px; the existing phone-lineup layout tests pass.

## 2. Forecast table

- [x] 2.1 Rename "Owner" to "Manager". Left-align ELO and 1-week change, centre the Manager column (header, name and team lines), right-align the rest, headers included. Compact styling: padding 6 px 8 px, a slightly larger font, ELO 50 px, change 56 px, bold non-wrapping manager names, and desktop sticky offsets updated. Verify: screenshots at 375 and 1280 px in light and dark.
- [x] 2.2 Below 600 px, pin the Manager column (`sticky; left: 0`) with solid backgrounds for the header, normal, hover and selected rows, while ELO and change scroll away. Verify: a layout test scrolls the table container right at 375 px and asserts the Manager cells' left edge stays at the container's left edge.

## 3. Player WAR

- [x] 3.1 Rename "Owner" to "Manager" in the compact tables and the full list. Below 600 px, pin the full list's name column with surface backgrounds, the header over it set above the sticky header row. Verify: a layout test scrolls the full list right at 375 px and asserts the name column stays at the left edge; screenshots.

## 4. Predictions charts and header

- [x] 4.1 Chart right padding on narrow screens: 10 px with no team selected, else the measured width of the selected label plus 22 px, for both charts. Verify: at 375 px the plot area spans at least 85% of the card's inner width with nothing selected.
- [x] 4.2 Turn the odds chart's metric buttons into a swipe strip below 600 px (shared fade helper with the sub-tabs). Move the rating range buttons below the chart in a smaller size. Verify: the layout check passes for the moved controls; at 375 px the metric buttons sit on one line.
- [x] 4.3 Remove the header "How good are these odds?" link from `index.html` and its registry entry. Verify: the coverage test passes, and the footer link still opens the calibration page.

## 5. Layout check, copy and docs

- [x] 5.1 Add 440 to `WIDTHS`. Update the registry (moved controls, removed link, metric strip). Add tests:
  - Games cards stacked at 440 px, with no overlap within team rows
  - finished cards' score order
  - the pinned Manager and WAR name columns

  Verify: `LAYOUT_REQUIRED=1 pytest tests/layout` passes at all five widths.
- [x] 5.2 Regenerate `site-copy.txt` (`python -m ffapp site-copy`) for the new score labels, and update the README where it describes the table column, the Games score block or the layout-check widths. Verify: `python -m ffapp site-copy --check` passes, and the README matches.
- [x] 5.3 Run `pytest`, `node --test relay/worker.test.mjs`, the layout check and `openspec validate ui-cleanup --strict`. Take screenshots at 440 px (the owner's phone width) of the Predictions table scrolled, a finished Games card, the WAR full list scrolled and both charts, light and dark. Verify: all pass, and the screenshots are listed for the owner.

## Workflow follow-up

- Commit, push and archive with spec sync when the user asks.
