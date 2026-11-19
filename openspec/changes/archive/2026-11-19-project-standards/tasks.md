# Tasks

## 1. Record the standards

- [x] 1.1 Add a "Project standards" block to the `openspec/config.yaml` context covering:
  - browsers and devices
  - phone widths 360, 390, 414 and 440, with their StatCounter source and date, and the yearly review rule
  - WCAG 2.2 AA
  - Material Design 3 usability rules followed and its visual system not followed
  - nomenclature (Managers, Team Names, Players, Forecasts, Projections) and its scope (text people read, not identifiers)
  - APA style (title case for titles and headings)
  - the `Calculations.txt` rule

  Verify: the YAML parses and `openspec validate project-standards --strict` passes.
- [x] 1.2 Add `CLAUDE.md` (under 60 lines): the standards in brief, the existing project rules (stamp-site, `?v=__BUILD__`, layout registry, site copy and confirming copy edits), and a pointer to `config.yaml`. Verify: the file exists and matches the config.

## 2. Calculations.txt

- [x] 2.1 Write `Calculations.txt` with the format header and the 18 sections listed in the design. Each has Code, Data sources, Depends on, Formula, In plain English, and Assumptions and decisions, written from the code and the README. Verify: each formula is checked against its module, with spot checks: the WAR win probability, the replacement shrinkage, the merged cut, the PPG blend and the Brier skill.
- [x] 2.2 Move the README's calculation sections into `Calculations.txt`, leaving short overviews with links to the sections. Verify: no formula is left only in the README, and the README's command examples are unchanged.
- [x] 2.3 Add `tests/test_calculations_doc.py`: every listed calculation module appears on a `Code:` line, and every section has all seven headings. Verify: it passes, and fails when a module is removed from the file.

## 3. Browsers and phone widths

- [x] 3.1 Extend `tests/layout/conftest.py` with Chromium (installed Chrome), WebKit and Firefox, and set the widths to 360, 390, 414, 440, 768, 1000 and 1280. WebKit and Firefox run the control, sideways-scroll, pinned-column, stacking and wide-font tests at 390, 440 and 1280 px, and skip when not installed unless `LAYOUT_REQUIRED=1`. Install WebKit and Firefox locally. Verify: the full check runs in all three engines.
- [x] 3.2 Fix the WebKit and Firefox faults found if small; otherwise list them as engine gaps with reasons (skip list) for follow-up. Verify: the check passes, and any gap is listed.
- [x] 3.3 Add `python -m playwright install --with-deps webkit firefox` to the `site.yml` test job. Verify: the code-push run installs the engines and passes.
- [x] 3.4 Fix the pinned columns clipping their neighbour on phones. The 14 px left cover added in ui-cleanup (`box-shadow: -14px 0 0 var(--surface)` on the pinned Manager cell and the Player WAR full-list name cell) also paints over the column to their left at the start position: the full list's # column shows only half of each number. Replace it with a cover that applies only while the column is pinned (for example `left: -14px`, so the stuck cell sits flush with the scroll box's edge, or a pseudo-element). Add a layout test: at the start position, no column left of a pinned column is overlapped by it, and the full list's rank numbers show in full (`scrollWidth <= clientWidth` and not covered). Verify: the test passes in all three engines at 360, 390, 414 and 440 px, and before-and-after screenshots of both tables.

## 4. Accessibility, touch targets and nomenclature checks

- [x] 4.1 Vendor axe-core (pinned 4.x, with its licence header) at `tests/layout/vendor/axe.min.js`, and add `tests/layout/test_accessibility.py` using the WCAG 2.2 A and AA tags. It runs on the coverage views at 390 and 1280 px and compares against `tests/baselines/axe.json` both ways (`UPDATE_BASELINES=1` rewrites it). Verify: it passes against the generated baseline, and fails when a contrast problem is added to a scratch copy.
- [x] 4.2 Add the touch-target test: controls of at least 48 × 48 px at 360 and 440 px, with inline links, chart canvases and Positions dots exempt as the design says, compared both ways against `tests/baselines/touch.json`. Verify: it passes against the baseline, and fails for a deliberately shrunk button on a scratch copy.
- [x] 4.3 Add `tests/test_nomenclature.py` over `site-copy.txt`: retired terms, the Sleeper "projection" exemption, `NOTE: nomenclature-ok` exceptions, and the baseline `tests/baselines/nomenclature.json` compared both ways. Verify: it passes against the baseline, and fails for a new entry using "odds".

## 5. Verify and report

- [x] 5.1 Run `pytest`, `node --test relay/worker.test.mjs` and `LAYOUT_REQUIRED=1 pytest tests/layout`, and validate the change strictly. Then report each baseline's findings to the owner as the follow-up list: accessibility rules by count, small controls, retired terms by entry, and engine gaps. Verify: all pass, and the follow-up list is shown.

## Workflow follow-up

- Commit, push and archive with spec sync when the user asks. Then propose the follow-up changes the owner picks from the reported list, starting with the forecast wording pass through `site-copy.txt`.
