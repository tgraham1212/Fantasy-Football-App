# Inspection Checklist

The record of every inspection the requirements standard calls for (`project-standards` 10.4.1 and 10.8.1). The requirements check (`tests/test_requirements.py`) reads both tables.

- **Requirement Inspections:** every requirement verified by Inspection, with what the inspector looks for, the date it was last inspected and the result. The ID column holds the requirement's ID.
- **Spec Standard Reviews:** every spec, with the date its judgment items were last reviewed and the result. The judgment items are the ones a parser cannot check: every value has a unit and a tolerance or bound, every non-obvious requirement has a rationale, every project term is in `openspec/glossary.md`, and no statement is compound in a way the one-SHALL rule misses.

The maintainer's approval at a spec's review is its inspection. A spec edited in a commit after its review date fails the check until it is reviewed again and its date updated in the same change. Dates are `YYYY-MM-DD`; a result is Pass, or Pass with notes.

A spec not yet brought to the standard has no row; its "no standard review" finding is listed in `tests/baselines/requirements.json` until it is reviewed.

## Requirement Inspections

| ID | Requirement | Spec | Pass criteria | Last inspected | Result |
|---|---|---|---|---|---|
| 1.1 | Season simulation | `playoff-odds-simulation` | Every `--runs` default in `src/ffapp/cli.py` (simulate, calibrate, refresh, build, hot) is 10,000 | 2026-11-23 | Pass |

## Spec Standard Reviews

| Spec | Last reviewed | Result | Notes |
|---|---|---|---|
| `playoff-odds-simulation` | 2026-11-23 | Pass | Worked example: 14 requirements became 31 under need 1; roster drift corrected to a random walk; two gaps closed with tests |
