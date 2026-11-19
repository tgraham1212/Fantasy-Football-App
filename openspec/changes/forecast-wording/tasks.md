# Tasks

## 1. Site text

- [x] 1.1 Write the proposal's wording table into the TEXT lines of the 19 entries in `site-copy.txt`. Run `python -m ffapp site-copy --check` (all 19 pending), then `python -m ffapp site-copy --apply`. Verify: `--apply` reports every entry applied with none refused, and `--check` reports in sync.
- [x] 1.2 Change the labels in the HTML:
  - the sub-tab "Predictions" becomes "Forecasts" (`data-page` unchanged)
  - the group header becomes "Playoff Forecast"
  - the calibration back link becomes "← Forecasts"
  - both meta descriptions say "forecasts"

  Verify: `tests/test_site_files.py` and the coverage test pass.
- [x] 1.3 Regenerate `tests/baselines/nomenclature.json` with `UPDATE_BASELINES=1` and confirm it is empty, or report any remaining entry with its reason. Verify: `pytest tests/test_nomenclature.py` passes with an empty baseline.

## 2. Docs

- [x] 2.1 Update the README and `Calculations.txt`:
  - Forecasts tab and table
  - forecast of record
  - "How Good Are These Forecasts?"
  - "forecasts" for the site's output (code names unchanged)

  Verify: a search for "Predictions tab", "prediction of record" and "How good are these odds" in both files finds nothing, and `tests/test_calculations_doc.py` passes.

## 3. Verify

- [x] 3.1 Run `pytest`, `node --test relay/worker.test.mjs` and `LAYOUT_REQUIRED=1 pytest tests/layout` in all engines, and `openspec validate forecast-wording --strict`. Take screenshots of the Forecasts tab header and table, the calibration page title, a Games note and the Player WAR notes at 440 and 1280 px for the owner. Verify: all pass and the screenshots are listed.

## Workflow follow-up

- Commit, push and archive with spec sync when the user asks. Next is the colour contrast change (`--muted` and the other contrast findings).
