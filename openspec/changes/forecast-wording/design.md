# Design

## Context

- **The nomenclature baseline** (`tests/baselines/nomenclature.json`) lists 29 retired-term uses in 19 `site-copy.txt` entries: CAL-01, 02, 05, 06, 12, 13, 14, 23, 25; GAME-02, 03, 05, 08, 10; HDR-04; POS-05, 06; PRED-01, 18; WAR-07, 08, 12, 18, 20.
- **Labels outside the copy file** carry old terms in `site/index.html`:
  - the sub-tab button "Predictions"
  - the group header "Playoff chances"
  - the meta description "Monte Carlo playoff odds..."

  `site/calibration.html` has the back link "← Playoff odds" and its meta description. `index.html` also has the copy-marked paragraph PRED-01, which says "These are chances, not predictions".
- **Copy edits.** The owner applies copy through `site-copy.txt` and approves edits before `--apply`. Approving this change's wording table counts as that approval.
- **Identifiers stay:** `data-page="predictions"`, `#page-predictions`, `odds-table`, `data/odds/`, the `record` field and the `forecast_of_record` concept in code. The standards exempt code identifiers.

## Goals / Non-Goals

**Goals:**
- Every piece of site text people read uses the standard terms, and the nomenclature baseline is empty.
- Spec and doc text that names a visible label matches the site.

**Non-Goals:**
- A full prose sweep of every spec and of the README for "chance" or "odds" where they describe internals (for example the playoff-odds-simulation spec's capability name). Those are code-adjacent names or historical change records. The README is updated where it names visible labels or describes the forecast.
- Renaming URLs, ids, files or data fields.
- APA title case for headings this change does not otherwise touch. That is left for the type-scale and heading pass.

## Decisions

**1. Copy edits go through `site-copy.txt` and `--apply`.** The wording table in proposal.md is written into the file's TEXT lines, `--apply` writes them into the code, and the placeholder guard protects the `${...}` expressions. Entries keep their IDs.

**2. Labels change in the HTML directly:**
- the sub-tab button text "Forecasts"
- the group header "Playoff Forecast"
- the calibration back link "← Forecasts"
- the two meta descriptions

The sub-tab keeps `data-page="predictions"`, so links, the URL hash and the layout registry selectors are unchanged.

**3. "Projection" stays where it means Sleeper's input.**
- GAME-02 and CAL-05 say "Sleeper projection(s)", and POS-05 and POS-06 say "Sleeper's projected points", so the check reads them as inputs.
- GAME-05 and GAME-10 use "forecast", because there the word describes the simulation's output.

**4. "Win chance" becomes "win probability".** It is a probability computed for one game or one player-week, not a simulation forecast, and the site already calls it "win probability" elsewhere.

**5. Docs.** README and `Calculations.txt` replacements:
- "Predictions tab" or "Predictions table" becomes "Forecasts tab" or "Forecasts table"
- "prediction of record" becomes "forecast of record"
- "How good are these odds?" becomes "How Good Are These Forecasts?"
- "odds" becomes "forecasts" wherever it means the site's output

Code names in backticks stay.

**6. Baseline.** After applying, `tests/baselines/nomenclature.json` is regenerated and should be `[]`. Any entry still flagged is reworded, or carries a `NOTE: nomenclature-ok <reason>`, and is reported to the owner.

## Risks / Trade-offs

- [Longer text could wrap differently: "How Good Are These Forecasts?" is longer than "How good are these odds?"] → the layout check runs in all engines at all widths.
- [Returning visitors know the "Predictions" tab name] → the tab keeps its position and URL.

## Migration Plan

A site and doc change only. The code push deploys it after the tests pass. Rollback is a revert.

## Open Questions

None. The wording was agreed in the conversation and is listed in proposal.md for the owner's approval.
