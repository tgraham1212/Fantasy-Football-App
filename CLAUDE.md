# Fantasy Football App: working rules

The full project rules and standards are in `openspec/config.yaml` (`context`). This file
holds the same rules in brief so every session follows them, including quick fixes made
outside a planned change.

## Workflow
- Features go through OpenSpec: explore, propose, apply, then commit, push and archive with
  spec sync, each step when the owner asks.
- Before pushing, fetch: the daily refresh commits `data/` and `site/data/`.

## Site rules
- Every deploy stamps through `python -m ffapp stamp-site`; never stamp by hand. New script,
  stylesheet or import references carry `?v=__BUILD__`.
- Every new control goes into the layout check registry (`tests/layout/controls.py`).
- Every new piece of descriptive text gets a copy ID (`data-copy="ID"` or `/*copy:ID*/`) and
  `python -m ffapp site-copy` is run in the same change. When the tests report pending copy
  edits in `site-copy.txt`, ask the owner before running `--apply`.

## Standards
- **Browsers:** Chrome, Safari, Edge and Firefox on desktop; Chrome and Safari on phones.
- **Phone widths:** 360, 390, 414 and 440 px (StatCounter US mobile stats, October 2026),
  plus 768, 1000 and 1280. Review the statistics yearly.
- **Accessibility:** WCAG 2.2 AA (axe-core in the layout check, light and dark mode).
- **Colour:** define and adjust colours in OKLCH (https://oklch.fyi/); fix contrast by changing
  lightness only, keeping hue and chroma; derive new colours from existing hues. Text 4.5:1,
  focus rings and chart lines 3:1, both modes (`tests/test_colour_contrast.py`).
- **Material Design 3:** follow its usability rules (48 x 48 px touch targets on phones,
  visible focus and pressed states, consistent type scale); do not adopt its visual system.
- **Nomenclature** in anything people read (not code identifiers): Managers, Team Names,
  Players, Forecasts (simulation output), Projections (Sleeper's inputs only). Avoid
  "owner", "odds", "chances" and "predictions" in text.
- **Style:** APA; title case for titles and headings.
- **Calculations:** documented in `Calculations.txt`; a change to a calculation updates its
  section in the same change.
- Existing gaps are listed in `tests/baselines/`; baselines may only shrink.

## This machine
- Windows: run Python with `-X utf8`; long Bash heredocs with quotes break, so write
  scripts to the scratchpad and run them.
