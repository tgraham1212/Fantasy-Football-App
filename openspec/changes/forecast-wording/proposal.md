# Proposal

## Why

The project standards (project-standards, 2026-11-19) set the nomenclature for anything people read:
- Managers for league members
- Team Names for managers' team names
- Players for NFL players
- Forecasts for anything the simulation produces
- Projections only for Sleeper's inputs

The site still says "odds", "chances" and "predictions" for the simulation's output, "owner" in two notes, and "projected" where it means a forecast. The nomenclature baseline lists 29 uses in 19 copy entries. This change applies the owner's chosen wording, and the baseline shrinks to empty.

## What Changes

**Site labels (not in `site-copy.txt`):**
- The **Predictions sub-tab is renamed "Forecasts"**. Its URL is unchanged (`#<league>` with no suffix).
- The forecast table's group header changes from "Playoff chances" to **"Playoff Forecast"** (APA title case).
- The calibration page's header link changes from "← Playoff odds" to **"← Forecasts"**.
- The page meta descriptions say "forecasts" instead of "odds".

**Copy entries, applied through `site-copy.txt` (the owner approves this list by approving the change):**

| ID | Now | Becomes |
|---|---|---|
| CAL-01, CAL-02 | How good are these odds? | How Good Are These Forecasts? |
| HDR-04 (footer link) | How good are these odds? | How Good Are These Forecasts? |
| CAL-23 | Back to the playoff odds | Back to the forecasts |
| CAL-05 | ...rosters, projections and scoring... The chances the site would have shown... If the odds are honest... | ...rosters, Sleeper projections and scoring... The forecasts the site would have shown... If the forecasts are honest... |
| CAL-06 | How the odds are made | How the Forecasts Are Made |
| CAL-12 | Predicted vs observed | Forecast vs. Observed |
| CAL-13 | ...band of predicted chance... above it the odds were too cautious... | ...band of forecast percentage... above it the forecasts were too cautious... |
| CAL-14 | ...mean squared error of the chances... | ...mean squared error of the forecasts... |
| CAL-25 | ...using this week's projections. | ...using this week's Sleeper projections. |
| GAME-02 | ...from before the projection log began. | ...from before the Sleeper projection log began. |
| GAME-03 | Shown against the prediction of record: | Shown against the forecast of record: |
| GAME-05 | Playoff pairings are projected: | Playoff pairings are forecast: |
| GAME-08 | ...moved the team's chance against the pre-kickoff forecast, everyone else as projected. | ...moved the team's win probability against the pre-kickoff forecast, everyone else at their Sleeper projections. |
| GAME-10 | · projected, happens in N% of simulations | · forecast, happens in N% of simulations |
| POS-05, POS-06 | ...projected points for weeks... | ...Sleeper's projected points for weeks... |
| PRED-01 | These are chances, not predictions: | These are forecasts, not certainties: |
| PRED-18 | Hover for every team's chance after a given week; | Hover for every team's forecast after a given week; |
| WAR-07 | Weekly win chance. ... the win chance is... | Weekly win probability. ... the win probability is... |
| WAR-08 | Win chances sum over... | Win probabilities sum over... |
| WAR-12 | ...owner and team from their latest season. | ...manager and team from their latest season. |
| WAR-18 | Hover an owner to see who else held the player that season. | Hover a manager's name to see who else held the player that season. |
| WAR-20 | Each week's win chance is... | Each week's win probability is... |

**Docs that name these labels:**
- The README and `Calculations.txt` say "Forecasts tab", "forecast of record" and "How Good Are These Forecasts?", and use "forecast" where they describe the simulation's output.
- Code identifiers stay (`predictions` page id, `record`, `odds-table`, `data/odds/`).

**Specs that name these labels:**
- `league-odds-site`: the sub-tab, the group header, the live-week requirement's text, and the calibration page's text.
- `manual-refresh`: the button no longer sits beside the removed header link.

**The baseline:** `tests/baselines/nomenclature.json` becomes empty, so the nomenclature check fails on any new retired term.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `league-odds-site`:
  - "League pages": the first sub-tab is "Forecasts".
  - "Grouped chance headers": the "Playoff Forecast" group header.
  - "Live odds on the Predictions page": text refers to the Forecasts page and forecasts; the requirement name is kept.
  - "Calibration page": text refers to forecasts.
- `manual-refresh`: "Refresh button" sits in the header, aligned with the league buttons; the removed "How good are these odds?" header link is no longer referenced.

## Impact

- **Site:**
  - `site/index.html`: tab label, group header and meta description.
  - `site/calibration.html`: back link and meta description.
  - The copy edits above, written by `python -m ffapp site-copy --apply` into the HTML and scripts.
- **Docs:** `README.md`, `Calculations.txt`, `site-copy.txt` (regenerated) and `tests/baselines/nomenclature.json`.
- **Tests:** the layout-check registry selectors do not change (`data-page="predictions"` stays), and screenshots are taken for the owner.
- **No data, behaviour or URL changes.**
