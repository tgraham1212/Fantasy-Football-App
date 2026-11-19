# Tasks

## 1. Colours

- [x] 1.1 Take "before" screenshots of the Forecasts tab, a Games card, the Positions page, the Player WAR table and the calibration page, at 440 and 1280 px in light and dark mode, into the scratchpad. Verify: 20 files exist.
- [x] 1.2 In `site/styles.css`:
  - set light `--muted` to #716f6a;
  - set light `--accent` to #2170cd;
  - add `--accent-fill: #2170cd` to all three token blocks;
  - point `.leagues button[aria-pressed="true"]` at `var(--accent-fill)`.

  Leave the dark `--muted` and `--accent` values as they are. Verify: the two dark blocks are still identical, and `tests/test_site_files.py` passes.

## 2. Checks

- [x] 2.1 Add `tests/test_colour_contrast.py`, following design decision 3:
  - parse the three token blocks;
  - assert the two dark blocks match;
  - check the text pairs at 4.5:1 and the non-text pairs at 3:1;
  - fail on any token that is neither checked nor exempt;
  - name the mode, both tokens and the ratio on failure.

  Verify: it passes, and it fails when light `--muted` is set back to #898781.
- [x] 2.2 Make the axe check in `tests/layout/test_accessibility.py` run in light and dark mode (`data-theme`), with the mode in the fingerprint. Regenerate `tests/baselines/axe.json` with `UPDATE_BASELINES=1`. Verify: the baseline is `[]`, and the test passes in both modes.

## 3. Standards and Docs

- [x] 3.1 Add the colour standard to the project-standards block of `openspec/config.yaml`:
  - OKLCH, with https://oklch.fyi/ as the reference;
  - fix contrast by changing lightness and keeping hue and chroma;
  - derive new colours from existing hues;
  - 4.5:1 for text and 3:1 for focus rings and chart lines, in both modes, checked by `tests/test_colour_contrast.py`.

  Add a one-line summary to `CLAUDE.md` under Standards. Correct the `BRAND_HUE` comment in `tools/team_palette.py`: 258 is the start hue, and the accent measures 255.5. Verify: `python tools/team_palette.py` prints the same team colours as before.

## 4. Verify

- [x] 4.1 Run the full checks:
  - `pytest`;
  - `node --test relay/worker.test.mjs`;
  - `LAYOUT_REQUIRED=1 pytest tests/layout` in all engines;
  - `python -m ffapp site-copy --check`;
  - `openspec validate color-contrast --strict`.

  Take the "after" screenshots matching 1.1 and list the before/after pairs for the owner. Verify: everything passes and the screenshots are listed.

## Workflow follow-up

- Commit, push and archive with spec sync when the owner asks. The touch-target baseline (136 controls) remains a follow-up.
