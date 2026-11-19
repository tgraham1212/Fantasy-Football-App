# Proposal

## Why

On the owner's phone, a 440 px-wide screen, the site is cluttered in ways the layout check never saw. It tests 375, 768, 1000 and 1280 px, and most current large phones are 390 to 440 px wide.

- **Games cards stay side by side at 440 px.** A card stacks only below 420 px, so names, scores, the win-% box and the chart squeeze into about 200 px. Names cut to "tg…", and "Lineup choices" wraps over the scores.
- **Wide tables lose context on phones.** On a phone, the forecast table and the Player WAR full list lose the manager or player name as soon as you scroll right.
- **Lineup rows are hard to read.** Points, statuses and kickoff times sit at the far edge, away from the names they describe.
- **Charts and their buttons waste space.** The Predictions charts keep an empty label strip on phones, and their buttons wrap untidily.
- **Finished scores read backwards.** Finished games show the forecast big and the real score small ("avg pts" over "actual").
- **The header repeats a link.** The "How good are these odds?" button duplicates the footer link.

## What Changes

- **Forecast table:**
  - The "Owner" column is renamed "Manager".
  - Columns left of Manager are left-aligned, Manager is centred, and columns right of it are right-aligned. Headers and data follow the same rule.
  - The table is tighter: narrower ELO and 1-week columns, less row padding, slightly larger text, and bold manager names.
  - On phones (below 600 px) the Manager column pins to the left edge while ELO and 1-week change scroll away. Wider screens keep today's pinned first three columns.
- **Player WAR:**
  - "Owner" becomes "Manager" in the top-10 tables and the full list.
  - On phones, the full list pins the player name column while the rest scrolls.
- **Games cards:**
  - Cards stack (teams above the chart) below 600 px, up from 420 px.
  - **Finished and live games:** the big number is the actual or current score, with the forecast smaller beneath it, labelled "forecasted", and "Lineup choices" beneath that.
  - **Upcoming games:** the big number is labelled "forecast".
  - The win-% box is smaller on phones.
- **Lineup rows:**
  - Points or projections sit just after the longest name in each team's list, as an aligned column. The win probability added follows the points.
  - Kickoff times stay at the right edge.
  - In "Not playing", the reason sits just after the name, with a little extra space.
- **Predictions charts:**
  - On phones, there is no empty label strip until a team is highlighted, and then only that label's width.
  - The odds chart's metric buttons become one sideways-swiping strip.
  - The rating chart's time-range buttons move below the chart, smaller, while Rating and Z-score stay above.
- **Header:** the "How good are these odds?" button is removed from the league pages. The footer link and the calibration page's way back remain.
- **Layout check:** 440 px is added to its widths. Moved controls are updated in its registry. The new score words ("forecast", "forecasted") get copy IDs in `site-copy.txt`, while column headers stay out of it as before.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `league-odds-site`:
  - "Current odds table": Manager column, alignment and compact styling.
  - "Usable on phones": the pinned Manager column.
  - "Chart metric buttons": the buttons lead the chart card and swipe on phones.
  - "Rating chart time range": the buttons sit below the chart.
- `games-page`:
  - "Matchup cards": stacking below 600 px; actual or current score big with "forecasted" beneath; "forecast" label for upcoming games; smaller win box on phones.
  - "Live cards": the same score layout as finished cards.
  - "Lineup choices shown": placed under the forecasted line.
  - "Player row layout": points column after the names, times at the right edge.
  - "Not playing": the reason next to the name.
- `war-leaderboard-page`:
  - "Position leaderboards": Manager column.
  - "Expanded list": Manager column and the pinned player name on phones.
- `layout-checks`: "Layout check" adds the 440 px width.

## Impact

- **Site:**
  - `site/index.html`: the header link and table header text.
  - `site/app.js`: chart padding on phones, metric and range button placement, table classes.
  - `site/games.js`: the score block, lineup rows and not-playing rows.
  - `site/war.js`: column headers.
  - `site/styles.css`: the bulk of the change.
- **Tests and copy:**
  - `tests/layout/conftest.py`: widths.
  - `tests/layout/controls.py`: moved controls, and checks for pinned columns, card stacking and score order.
  - `site-copy.txt` is regenerated for the new or changed labels.
- **No data or export changes.**
