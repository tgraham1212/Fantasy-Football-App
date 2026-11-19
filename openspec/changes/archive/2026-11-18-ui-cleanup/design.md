# Design

## Context

Current state, from the code and screenshots at 375, 402 and 440 px:

- **Games card stacking.** `.game-body` stacks only at `max-width: 420px`. At 440 px (the owner's phone, from a 1320 px screenshot at 3x) the team rows get about 200 px:
  - names are cut short ("tg…")
  - `.who` holds `choicesLine()`, so "Lineup choices: 0.0" wraps in the narrow column and overlaps the score column
  - the score block (`teamRow` in `site/games.js`) shows `mean` big with "avg pts", "proj final" when live, and the actual score small ("183.5 actual", or "so far" and "to play" when live)
  - `.win` has `min-width: 4.4em`
- **Lineup rows.** Each row is a three-column grid (`2.6em | 1fr | auto`) holding position, name, points and an aside, so points, win probability added (WPA) and kickoff time all sit at the right edge. Not-playing rows put the reason at the far right (`1fr | auto`).
- **Forecast table.**
  - Columns: ELO and change are `.num`, so right-aligned; owner is left-aligned; projected and chance columns are right-aligned.
  - Widths: ELO 62 px, change 64 px; cell padding is 9 px 10 px.
  - Pinning: at 600 px and wider, ELO, change and owner are sticky at left 0, 62 and 126 px. Below 600 px nothing is sticky, and the table scrolls inside `.table-wrap`.
- **Player WAR.** Headers say "Owner". The full list scrolls inside `.dialog-table`, with nothing pinned.
- **Predictions charts.**
  - On narrow screens both charts keep `layout.padding.right = 104`, although only the selected team's end label is drawn.
  - The metric buttons wrap onto two lines at 375 px.
  - The rating card puts the metric and range button groups together in `.switchers` above the chart.
- **Header.** `index.html` has the "How good are these odds?" `a.nav-link` in the header, and the footer links the same page.
- **Layout check.** `WIDTHS = (375, 768, 1000, 1280)` in `tests/layout/conftest.py`.

## Goals / Non-Goals

**Goals:**
- Every phone width from 375 to 599 px gets the stacked, full-width Games card, and 440 px is tested.
- Wide tables keep their identifying column on screen while scrolling on phones.
- Scores read actual first. Lineups put the numbers next to the names.

**Non-Goals:**
- No change to the data or the export.
- No change to desktop pinning of the forecast table, beyond alignment and compactness.
- Column headers and button labels stay out of `site-copy.txt`, as before. Only the new score words get copy IDs.

## Decisions

**1. Games card: stack below 600 px.**
- `@media (max-width: 599.98px) { .game-body { grid-template-columns: minmax(0, 1fr) } }` replaces the 420 px rule. The chart already follows the rows in source order.
- Below 600 px, `.win` gets `min-width: 3.4em; padding: 4px 6px; font-size: 0.92rem`.
- 600 px is the existing phone breakpoint used elsewhere (the header and table pinning), so the site keeps one phone threshold.

**2. Score block.** `teamRow` builds `.mean`:
- **Finished or live:** `<span class="num">{actual or points so far}</span><span class="unit">{mean} forecasted</span>`, plus `{to_play} to play` when live, then `choicesLine(t)`. `choicesLine` moves out of `.who`, so it sits under the forecasted line, right-aligned, and the name column never carries it.
- **Upcoming:** `<span class="num">{mean}</span><span class="unit">forecast</span>`.
- **Copy IDs:** the words "forecast" and "forecasted" become marked literals (`GAME-13`, `GAME-14`) built into the markup, so the owner can edit them in `site-copy.txt`.
- **Live projected final:** this is the mean of the live simulation, the same field the card shows today as "proj final". It now sits under "forecasted".

**3. Lineup rows as an aligned grid.**
- `.team-players ul` becomes `display: grid; grid-template-columns: 2.6em minmax(0, max-content) auto auto 1fr; column-gap: 6px`, with each `li` set to `display: contents`.
- Children are placed by class: `.pos` in column 1, `.pname` 2, `.pts` 3, the WPA aside 4, the kickoff-time aside 5 with `justify-self: end`.
- `asideTag` splits into a WPA span and a time span, so WPA stays beside the points.
- The name column is as wide as the list's longest name (max-content, never wider than the card allows, ellipsis beyond). The points column follows it, so values line up per list. The full lineup inside `details` is its own list and aligns within itself.
- Not-playing lists use `grid-template-columns: minmax(0, max-content) auto; column-gap: 0.9em`, which puts the reason just after the longest name with slightly more than a word space.
- Rows keep their `li` element for the layout check's selectors. `display: contents` keeps them in the accessibility tree.

**4. Forecast table.**
- **Header:** "Owner" becomes "Manager" (`index.html` header button text and sort label). The sort key stays the same.
- **Alignment:**
  - `.col-elo` and `.col-elo-change` lose `.num` alignment and are left-aligned.
  - `.col-owner` is `text-align: center`, and its name and team lines are centred.
  - Projected and chance columns stay right-aligned, and headers match their cells (`th .sort` alignment follows).
- **Compact:**
  - `#odds-table th, #odds-table td { padding: 6px 8px }`
  - table font size `1.02rem`, up from the body size
  - `.col-elo` 50 px and `.col-elo-change` 56 px
  - `.col-owner .owner-name { font-weight: 700; white-space: nowrap }`
- **Pinning below 600 px:** `.col-owner { position: sticky; left: 0; z-index: 1; background: var(--surface); box-shadow: 1px 0 0 var(--grid) }`. Its header gets z-index 2 and the same background. Selected and hover row backgrounds also apply to the sticky cell. At 600 px and wider, the existing three-column pinning stays, with offsets updated for the new widths.

**5. Player WAR.**
- "Owner" becomes "Manager" in `war.js` headers: the compact tables and the full list.
- Below 600 px, the full list's name column (`th`/`td` of the name) is `position: sticky; left: 0` with a surface background. The rank column scrolls away. The header cell over it gets a higher z-index, so the sticky header row and the pinned column cross cleanly.

**6. Chart width on phones.**
- `layout.padding.right` becomes `narrow ? (selected ? labelWidth + 22 : 10) : 160` for both charts.
- `labelWidth` is measured with the chart's own font (`ctx.measureText`) for the selected team's short label.
- The chart is already redrawn when a team is selected, so the padding updates with the selection.

**7. Chart buttons.**
- **Odds chart:** `#metric-switcher` stays the card head's first item. Below 600 px it gets the sub-tab strip treatment: `flex-wrap: nowrap; overflow-x: auto; scroll-snap-type: x mandatory`, hidden scrollbar, and an edge fade. The fade helper in `app.js` is generalised from the sub-tabs, so both strips share it.
- **Rating chart:** `#rating-range` moves in `index.html` from the card head to just after `#rating-wrap`, with a `small` modifier: smaller font and padding. Rating and Z-score stay in the head.

**8. Header link.** The header `a.nav-link[href='calibration.html']` is removed from `index.html`. The footer link stays. `calibration.html` keeps its "← Playoff odds" header link.

**9. Layout check.**
- `WIDTHS` becomes `(375, 440, 768, 1000, 1280)`.
- **Registry:** the "calibration link" control is removed. "chart metric" and the rating range controls use their new positions. A "metric strip" scroll check is added.
- **New tests:**
  - at 440 px, every Games card's `.game-body` is one column and no team row's elements overlap (the bounding boxes of name, score block, lineup choices and win box are disjoint);
  - the forecast table's Manager column stays at the container's left edge after scrolling it right at 375 px;
  - the WAR full list's name column does the same;
  - finished cards show the actual score as `.num` and the forecast in `.unit`.
- Run time grows by about a fifth.

**10. Copy.** "forecast" and "forecasted" get IDs. Regenerate `site-copy.txt`. The removed header link was a label, not copy, so it was never in the file.

## Risks / Trade-offs

- [Sticky cells in a horizontally scrolling table show content beneath them without a solid background] → explicit backgrounds, including the selected-row and hover states, checked by screenshot in light and dark.
- [`display: contents` on list items] → supported by current browsers. The layout check runs in Chrome; Safari is checked by the owner on their phone.
- [A long name widens the name column for its whole list] → max-content is capped by `minmax(0, …)` and the card width, with ellipsis beyond.
- [The 440 px width adds test time] → accepted, since it is the most common phone class.

## Migration Plan

Site-only change. The code push deploys it through `site.yml`, after the layout check passes at all five widths. Rollback is a revert.

## Open Questions

None.
