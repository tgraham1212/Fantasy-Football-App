# Design

## Context

- **Where rules live today.** Project rules are in the `openspec/config.yaml` `context`: stamping, `?v=__BUILD__`, the layout-check registry and site copy. That context reaches OpenSpec workflows only. There is no `CLAUDE.md`.
- **The layout check today.** It runs only in installed Chrome (`channel="chrome"`), at 375, 440, 768, 1000 and 1280 px. A full run takes about 8 minutes on GitHub's runner (628 cases).
- **Calculation docs today.** Calculations are described across README sections: Replacement level, Manager ratings, Player WAR (with "Current-season start percentages"), Out statuses, Positional Rankings, Games (forecasts, lineups, live weeks, win probability added), How the simulation works, and Calibration.
- **Calculation modules:**
  - `simulate.py` and `noise.py`
  - `lineup.py`
  - `replacement.py` and `drift.py`
  - `odds.py`, `standings.py` and `bracket.py`
  - `forecast.py`, `games.py`, `views.py` and `live.py`
  - `ratings.py`
  - `war.py`
  - `positions.py`
  - `calibrate.py`
  - `scoring.py` and `stats.py` (points)
  - `injuries.py` (out rules)
- **StatCounter, US mobile, October 2026:** 414×896 20.3%, 390×844 9.5%, 384×832 9.0%, 360×780 4.6%, 402×874 4.3%, 393×852 4.1%.
- **Terms in use:** the site text currently uses "odds", "chances", "predictions" (the Predictions tab), "owner" in a few notes, and "projections" both for Sleeper inputs and loosely.

## Goals / Non-Goals

**Goals:**
- One place each for planned work (`config.yaml`) and everyday sessions (`CLAUDE.md`), saying the same thing.
- Automatic checks wherever a standard is checkable, starting from honest baselines rather than a wall of red.
- A `Calculations.txt` complete enough that the README no longer needs its formula sections.

**Non-Goals:**
- Fixing the baselined findings. Each becomes a follow-up change. The renames to "forecast" go through `site-copy.txt` for the owner's approval.
- Adopting Material Design 3's visual system.
- Real-device testing. WebKit stands in for Safari, and the owner checks big layout changes on their iPhone.

## Decisions

**1. The standards text.**
- **`config.yaml` context** gains a "Project standards" block. It names each standard and its check, and states what is followed and what is not:
  - **MD3 followed:** touch targets, focus and press states, type scale.
  - **MD3 not followed:** components, colour roles, shapes, elevation.
  - **APA:** title case for titles and headings, APA conventions in prose.
  - **Nomenclature scope:** text people read, not identifiers.
  - **Phone widths:** the source and date, and the yearly review rule.
- **`CLAUDE.md`** is under 60 lines. It holds the same standards in brief, the existing project rules (stamping, layout registry, site copy, ask before applying copy edits), and a pointer to `config.yaml` for detail.
- Both say the standards apply to all new work, and that existing gaps are tracked by the baselines.

**2. Browsers and widths in the layout check.**
- `conftest.py` gains a `browser_name` dimension. Chromium uses the installed Chrome as today. WebKit and Firefox come from Playwright's own builds.
- **The matrix:**
  - Chromium runs every test at 360, 390, 414, 440, 768, 1000 and 1280 px.
  - WebKit and Firefox run the control-keeps-the-layout, sideways-scroll, pinned-column, stacking and wide-font tests at 390, 440 and 1280 px.

  That covers the engine-specific risks (sticky, `display: contents`, `:has()`, scroll snapping, fonts) without tripling the run.
- **Missing engines:** WebKit and Firefox skip when not installed, unless `LAYOUT_REQUIRED=1`.
- **CI:** `site.yml` runs `python -m playwright install --with-deps webkit firefox` before the tests.
- **Expected run time** is about 12 to 15 minutes. If it grows past 20, the WebKit and Firefox control matrix drops to 440 and 1280 px.
- Faults found in WebKit or Firefox are fixed in this change when small. Otherwise they are baselined as known engine gaps (a skip list with reasons) and become follow-ups.

**2b. Pinned-column cover fix (found after ui-cleanup shipped).**
- **The bug:** the pinned Manager cell and the full-list name cell carry `box-shadow: -14px 0 0 var(--surface)`. It hides the scroll box's padding strip while they are pinned, but at the start position it also paints over the 14 px of the column to their left. The owner saw the full list's # column cut in half on their phone.
- **The fix:** the cover should exist only while the cell is stuck. The preferred way is `left: -14px` (the scroll box's padding), so a stuck cell sits flush with the box's padding edge and needs no shadow. If an engine treats negative sticky offsets differently, the fallback is a pseudo-element shown only when the box has scrolled (a `scrolled` class set from the scroll handler).
- **The test:** at the start position, the column left of each pinned column is not overlapped, and the full list's rank cells are fully visible. It runs in all three engines, since sticky behaviour differs between them.

**3. Accessibility check (`tests/layout/test_accessibility.py`).**
- **The engine:** axe-core is vendored as `tests/layout/vendor/axe.min.js`, a pinned 4.x release from cdnjs with its licence header. It is injected with `page.add_script_tag` and run with tags `wcag2a`, `wcag2aa`, `wcag21aa` and `wcag22aa`.
- **Where:** every coverage view (Predictions, Games upcoming and final, Positions, Player WAR and its full list, Calibration) at 390 and 1280 px, in Chromium.
- **Fingerprints:** each finding is reduced to `rule | view | target selector`.
- **The baseline:** `tests/baselines/axe.json`, compared both ways. A new finding fails, and a listed finding that is gone fails with "remove from baseline". A `--update-baselines` helper (an environment variable, `UPDATE_BASELINES=1`) rewrites it intentionally.

**4. Touch targets.**
- **Where:** at 360 and 440 px in Chromium, on the same views.
- **What:** every visible control matched by the layout registry's control query.
- **The measure:** its bounding box, extended by any clickable padding (the box already includes padding). A control fails below 48 × 48 px.
- **The baseline:** `tests/baselines/touch.json` by `view | selector | rounded size`, with the same both-ways comparison.
- Inline links inside sentences are exempt, as WCAG allows for inline text. Chart canvases and SVG dots are exempt from the 48 px rule, but they must offer a keyboard alternative, which the Positions dots do.

**5. Nomenclature check (`tests/test_nomenclature.py`).**
- **What it scans:** the TEXT of every `site-copy.txt` entry.
- **Retired terms, case-insensitive, whole words:** `owner`/`owners`, `odds`, `chance`/`chances`, `prediction`/`predictions`/`predicted`, and `projection`/`projections`/`projected` where the entry is about simulation output.
- **Allowed uses:**
  - "projection" is allowed when the entry's label or text refers to Sleeper or player projections;
  - an entry can carry `NOTE: nomenclature-ok <reason>` for a justified exception, such as "win probability".
- **The baseline:** `tests/baselines/nomenclature.json` lists today's entries by ID with their flagged terms, and only shrinks.
- The README and specs are reviewed by hand in follow-ups rather than linted, because their prose legitimately discusses code names.

**6. `Calculations.txt`.**
- **Format:** plain text with a header explaining the format, then one section per calculation:

  ```
  ================================================================
  <NAME>
  ================================================================
  Code:          src/ffapp/<module>.py[, ...]
  Data sources:  ...
  Depends on:    <other sections>
  Formula:
    ...
  In plain English:
    ...
  Assumptions and decisions:
    - ... (why)
  ```
- **Sections:**
  1. Fantasy points (scoring)
  2. Player stats and projections (inputs)
  3. Out statuses
  4. Noise model
  5. Best lineup and the replacement floor
  6. Roster drift
  7. Season simulation and standings
  8. Playoff bracket
  9. Forecast outcomes (the table's chances)
  10. Game forecasts
  11. Lineup views and lineup choices
  12. Live forecasts
  13. Win probability added
  14. Replacement level (free agents)
  15. Manager ratings (Openskill, reversion, z-scores)
  16. Player WAR (consensus lineup, replacement cut, merged cut, win probability, WAR)
  17. Positional rankings (PPG, axis)
  18. Calibration (reliability, Brier, skill, coverage)
- **Where the text comes from:** written from the code and the README's existing sections, which are moved here. The README keeps a one-paragraph overview per feature and links "see Calculations.txt, section N".
- **The coverage test (`tests/test_calculations_doc.py`)** holds the calculation-module list and asserts that each module appears on some section's `Code:` line, and that every section has all seven headings.

**7. Where future work learns the rule.** The `config.yaml` context adds: "A change that alters a calculation updates its Calculations.txt section in the same change."

## Risks / Trade-offs

- [Engine downloads and longer CI] → only the code-push workflow pays it. The data refresh is unaffected.
- [Baselines can hide problems] → they only shrink, both-ways comparison makes a stale entry fail, and each baseline gets a follow-up change.
- [axe flags canvas charts lacking text alternatives] → expected. Baselined now, with a follow-up giving each chart a data-table alternative.
- [`Calculations.txt` drifting from the code] → the coverage test catches missing modules, and the config rule covers changed formulas. A formula changed without its doc can only be caught in review.
- [The nomenclature lint misreads "chance" in non-forecast text] → `nomenclature-ok` notes in the copy file.

## Migration Plan

1. Write the standards, `CLAUDE.md` and `Calculations.txt`, and move the README sections.
2. Add the engines, widths and checks, generate the baselines, and run everything locally and in CI.
3. Open follow-up changes:
   - a forecast wording pass through `site-copy.txt`
   - contrast and target-size fixes
   - chart text alternatives
   - any engine gaps

## Open Questions

None. The follow-up changes are scheduled by the owner after this lands.
