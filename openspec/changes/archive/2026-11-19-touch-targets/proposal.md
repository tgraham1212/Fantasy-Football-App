# Proposal

## Why

The project standard asks for 48 × 48 px touch targets on phones (Material Design 3), and the touch baseline lists 136 controls that miss it. Measured at 440 px, those entries are about 20 distinct controls repeated across views, in three groups:

- **Near misses (34 to 42 px):** the header buttons, sub-tabs, selects, week arrows and dialog close.
- **Compact chips (23 to 32 px tall):** the chart metric buttons, the time-range chips, the calibration outcome buttons, the Model/Actual toggle and Player WAR's "Show every…" button.
- **Dense rows:** table sort headers (14 px tall) and "Full Lineup" (19 px).

The sort headers and the Model/Actual toggle also fail WCAG 2.2's 24 px minimum.

## What Changes

The touch changes apply on phones only, below 600 px; desktop layout stays exactly as it is. The grey-text fix added during apply applies at every width.

- **Near misses grow to 48 px:** league buttons, sub-tabs, Refresh Data, the calibration back link, the theme toggle, the Season and Week selects, the week arrows and the dialog close button. The visible change is a header bar a few pixels taller.
- **Compact chips keep their look.** Each gets a transparent tap area (`::before`) that extends it to 48 px tall. A tap area never overlaps a neighbour's. Rows of chips that wrap get enough vertical spacing for this, and scrolling strips get enough padding that their own edges don't clip the tap areas.
- **Dense rows change layout.** Each sort header's button fills its whole header cell, in a header row at least 48 px tall, and narrow columns get at least 48 px of width. "Full Lineup" becomes 48 px tall.
- **The touch check measures what responds to taps.** It probes a 48 × 48 px square centred on each control and requires every probe point to land on that control. The square follows the control's own box, so a control taller or wider than 48 px is not penalised. A point landing on a neighbour fails, so the same probe catches overlapping tap areas.
- **The touch baseline drops from 136 to 0** and stays enforced.
- **Added during apply, with the owner's approval:** grey text on hovered and selected table rows. The touch work moved the mouse over a table row, and the accessibility check found that `--muted` failed there in both modes (4.17 to 4.48:1). Following the OKLCH rule (change lightness only), light `--muted` goes from #716f6a to #6b6964 and dark from #898781 to #8f8d87. The colour token test now also checks text on hovered and selected rows. The static worked-example table in Player WAR loses its hover highlight, so its blue mark keeps 4.5:1.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `layout-checks`: "Touch targets" measures the tap area by hit testing, not the visible box, and fails on overlapping tap areas.

## Impact

- **Site:**
  - `site/styles.css`: the phone media queries, plus the `--muted` values and the worked-example hover rule for all widths.
  - Calibration's wrapped outcome buttons and the card headers gain a little height on phones.
  - Each table sort label is wrapped in a `<span>` (`index.html`, `war.js` and `app.js`), so the whole header cell can be the button. Its rendering is unchanged.
- **Tests:** `tests/layout/test_accessibility.py` (the touch-target probe); `tests/test_colour_contrast.py` (hovered and selected rows); `tests/baselines/touch.json` goes from 136 entries to 0. The other layout checks must still pass at every width, including the pinned Manager column and the controls that must not move.
- **Docs:** none beyond the spec. There is no site text, so `site-copy.txt` is untouched, and there are no calculations.
