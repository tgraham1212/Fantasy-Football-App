# Design

## Context

The touch check in `tests/layout/test_accessibility.py` runs at 360 and 440 px. It flags any control whose bounding box is under 48 px in either dimension. Chart dots, canvas content and links inside sentences are exempt. A measurement at 440 px on 2026-11-19 grouped the 136 baseline entries into about 20 distinct controls:

| Group | Controls | Size at 440 px | CSS today |
|---|---|---|---|
| A | sub-tabs | ~80 × 42 | `.subtabs button` padding 8/14/10 |
| A | league buttons | 203 × 39 | `.leagues button` padding 9/6 (phone) |
| A | Refresh Data, "← Forecasts" | 110 × 40 | `.nav-link` padding 8/12 |
| A | theme toggle | 38 × 38 | `.theme` fixed 38 px |
| A | Season and Week selects | 75–212 × 36 | `.select-label select`, `.week-control select` padding 6/10 |
| A | week arrows, dialog close | 34 × 34 | `.week-control .step`, `.dialog-head .close` fixed 34 px |
| B | chart metric chips, calibration outcomes | 64–118 × 32 | `.metrics button` padding 5/11 |
| B | time-range chips | 62–97 × 25 | `.metrics.small button` padding 3/9 |
| B | "Show every…" | 82 × 32 | `.expand` |
| B | Model / Actual | 56 × 23 | `.view-toggle button` padding 3/10, parent `overflow: hidden` |
| C | sort headers | 21–81 × 14–41 | `th .sort`, an inline button in the header text |
| C | "Full Lineup" | 378 × 19 | `.team-players summary` |

Every group-B control is already at least 48 px wide. Only the height falls short.

## Goals / Non-Goals

**Goals:**
- Every control has a 48 × 48 px tap area on phones.
- Tap areas never overlap.
- The touch baseline goes to 0.

**Non-Goals:**
- Any change on desktop.
- Restyling the chips.
- The chart dots, which stay exempt behind their keyboard alternative.

## Decisions

1. **Phones only.** Every rule goes in a single new `@media (max-width: 599.98px)` block at the end of `styles.css`, headed "touch targets (Material Design 3, 48 px on phones)". This keeps the change easy to review and leaves desktop untouched.

2. **Group A gets a real `min-height` of 48 px.** Fixed-size buttons get `width: 48px; height: 48px`: the theme toggle, the week arrows and the dialog close. The other buttons, links and selects get `min-height: 48px` and keep their padding. The visible change is a few pixels on the header bar, the league buttons and the selects. *Alternative:* invisible tap areas here too. Rejected, because these controls sit in tight header rows where the extensions would collide, and their visual size barely changes anyway.

3. **Group B gets an invisible tap area.** Each control gets `position: relative`, and a `::before { content: ""; position: absolute; inset: -Npx 0; }`, where N is `(48 − height) / 2` rounded up: 8 px for 32 px chips and 12 px for 23–25 px chips. A click on a pseudo-element counts as a click on its element, so no script changes. Neighbours and clipping then decide the spacing:
   - **Wrapped rows** (calibration outcomes, and the rating range if it wraps): `row-gap` grows to 16 px for 32 px chips, so two rows' tap areas meet without overlapping.
   - **Horizontal neighbours** are unaffected, since the extension is vertical only.
   - **Scroll containers clip pseudo-elements.** `#metric-switcher` (`overflow: auto` on phones) gets `padding-block: 8px` so the tap areas fit inside it.
   - **`overflow: hidden` clips them too.** `.view-toggle` swaps `overflow: hidden` for border radii on its first and last buttons, so the 12 px extensions aren't cut off. It sits in a card header with nothing directly above or below within 12 px. The test proves this.

4. **Group C changes layout.**
   - **Sort headers:** on phones, `thead th:has(> .sort)` loses its padding, and `.sort` becomes `display: flex; align-items: flex-end; width: 100%; min-height: 48px; min-width: 48px;` with the cell's old padding moved inside the button. The whole cell becomes the button: the sorted dark fill and the arrow still apply, and the arrow keeps its 14 px right padding.
   - **Narrow numeric columns** ("#", ELO) grow to 48 px wide. The tables already scroll sideways on phones, and the pinned Manager column's `left: -14px` rule is unaffected.
   - **`:has()`** is supported in all target browsers (Safari 15.4+, Chrome 105+, Firefox 121+).
   - **"Full Lineup"** gets `min-height: 48px; display: flex; align-items: center;`, so the `<summary>` keeps its disclosure marker via `list-style`.

5. **The test probes hit areas instead of measuring boxes.** For each visible control (same query and exemptions as today):
   - Scroll it to the centre of its scroll containers with `scrollIntoView({block: "center", inline: "center"})`.
   - Take a probe rectangle centred on the control, 48 px or the control's own size in each dimension, whichever is larger, then inset it by 1 px.
   - Probe 9 points: the corners, the edge midpoints and the centre. Each point passes if `document.elementFromPoint(x, y)` is the control or inside it.
   - Report any failure as `view | control (w × h, first failing point)`.

   The fingerprint stays `view | control` so the baseline format is unchanged. Hit testing counts pseudo-element tap areas and padding automatically. A neighbour's overlapping tap area, or a clipping container, makes a point land on something else, so overlap and clipping fail with no separate check.

   *Risks:* a fixed header could cover a probe point. The site has none on phones, apart from the pinned Manager column, which pins horizontally only, and centring the control avoids it. Snap scrolling could stop short of centre, so a short wait after scrolling lets snapping settle before probing.

6. **The baseline goes to `[]`** once everything passes, and stays enforced.

## Changes Made During Apply

- **The probe was refined in four ways:**
  - A control larger than 48 px is probed over its visible part, so a table row wider than the screen isn't failed for being off-screen.
  - Corner points sit 7 px in from the corners, because a 10 px rounded corner isn't part of the box for hit testing.
  - Controls behind an open dialog are skipped, because they are inert.
  - A control covered by the pinned Manager column is scrolled clear of it, as a reader would, and probed again.
- **Tap areas extend 9 px, not 8.** An absolutely positioned `::before` is measured from the padding box, inside the 1 px border.
- **Spacing adjustments:**
  - Calibration chip rows use a 17 px gap, because the rows are about 31.5 px tall.
  - The rating range chips move 14 px clear of the chart.
  - The Model/Actual row gets 4 px of space above and below.
- **The sort label is wrapped in a `<span>`.** A flex column of raw text plus `<br>` splits the label into separate items. With a single span, `justify-content: flex-end` keeps the bottom alignment, and `safe` alignment stops a long word from spilling into the next column.
- **Row colours, approved by the owner.** `--muted` failed on hovered and selected rows in both modes. The fix lowers lightness only, following the colour standard: light #6b6964 (L 0.522), dark #8f8d87 (L 0.643). `tests/test_colour_contrast.py` computes the hovered row (surface plus 4% ink) and the selected row (surface plus 12% accent) and checks the row text (`--ink`, `--ink-2`, `--muted`) against both. The worked-example table has no hover highlight: it is static, and its blue mark needs the plain card.

## Risks / Trade-offs

- **Taller header and table header on phones** (+6 to +10 px). Accepted by the owner. Screenshots before and after at 360 and 440 for review.
- **Calibration outcome rows grow** from a 38 px to a 48 px row pitch when they wrap. This is the cost of tap areas that don't overlap.
- **`elementFromPoint` differs slightly between engines.** The touch test runs in Chromium only, as today. WebKit and Firefox still run the layout checks, which catch overflow and movement caused by the new sizes.
- **Moving the sort header's padding into the button** could change header alignment. Mitigation: the existing alignment rules move with it (left of Manager left-aligned, Manager centred, right of it right-aligned), and screenshots of the forecast table and the WAR tables are reviewed.
