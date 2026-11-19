# Tasks

## 1. The Check First

- [x] 1.1 Replace `_small_controls` in `tests/layout/test_accessibility.py` with the hit-area probe from design decision 5:
  - scroll each control to the centre;
  - probe 9 points in a 48 px square centred on it, or the control's own size where larger, inset by 1 px;
  - each point must hit the control or something inside it;
  - keep the same exemptions and the `view | control` fingerprint.

  Verify: run it against the current site with the baseline in place. Every entry it reports must already be in the baseline (no new findings), and its count must be at most 136.

## 2. Phone Styles

- [x] 2.1 Take "before" screenshots at 360 and 440 px, light mode, into the scratchpad: Forecasts (header, table, chart chips, rating range), a final Games card, Positions, Player WAR (table, "Show every…", full-list dialog) and calibration (outcome buttons).
- [x] 2.2 Add the phone-only block at the end of `site/styles.css`:
  - **group A:** `min-height: 48px`, or 48 × 48 for the fixed-size buttons;
  - **group B:** `::before` tap areas, with the `row-gap` and scroll-padding adjustments, and the `.view-toggle` overflow swap;
  - **group C:** sort headers fill their cells at 48 × 48 minimum, and "Full Lineup" is 48 px tall.

  Verify: the touch test reports no controls at 360 and 440.
- [x] 2.3 Regenerate `tests/baselines/touch.json` with `UPDATE_BASELINES=1`. Verify: it is `[]` and the touch test passes.

- [x] 2.4 (Added during apply, with the owner's approval.) Set light `--muted` to #6b6964 and dark `--muted` to #8f8d87. Check hovered and selected rows in `tests/test_colour_contrast.py`, and remove the hover highlight from the worked-example table. Verify: the colour token test and the axe check pass with empty baselines.

## 3. Verify

- [x] 3.1 Run the full checks:
  - `pytest`;
  - `node --test relay/worker.test.mjs`;
  - `LAYOUT_REQUIRED=1 pytest tests/layout` in all engines, including the pinned-column, no-movement and no-overflow checks;
  - `python -m ffapp site-copy --check`;
  - `openspec validate touch-targets --strict`.

  Take the "after" screenshots matching 2.1, plus 1280 px of the Forecasts and Games pages to show desktop is unchanged, and list the before/after pairs for the owner. Verify: everything passes, the desktop screenshots differ only in the shade of the grey text from 2.4, and the pairs are listed.

## Workflow follow-up

- Commit, push and archive with spec sync when the owner asks.
