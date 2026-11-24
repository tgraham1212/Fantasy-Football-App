# Inspection Checklist

The record of every inspection the requirements standard calls for (`project-standards` 10.4.1 and 10.8.1). The requirements check (`tests/test_requirements.py`) reads both tables.

- **Requirement Inspections:** every requirement verified by Inspection, with what the inspector looks for, the date it was last inspected and the result. The ID column holds the requirement's ID.
- **Spec Standard Reviews:** every spec, with the date its judgment items were last reviewed and the result. The judgment items are the ones a parser cannot check: every value has a unit and a tolerance or bound, every non-obvious requirement has a rationale, every project term is in `openspec/glossary.md`, and no statement is compound in a way the one-SHALL rule misses.

An inspection is redone whenever its requirement or any requirement beneath it changes: the check fails when a spec holding one of them changes in a commit after the row's date.

The maintainer's approval at a spec's review is its inspection. A spec edited in a commit after its review date fails the check until it is reviewed again and its date updated in the same change. Dates are `YYYY-MM-DD`; a result is Pass, or Pass with notes.

A spec not yet brought to the standard has no row; its "no standard review" finding is listed in `tests/baselines/requirements.json` until it is reviewed.

## Requirement Inspections

| ID | Requirement | Spec | Pass criteria | Last inspected | Result |
|---|---|---|---|---|---|
| 2.1.2 | Card columns | `games-page` | the live site at 1280 px, two columns and a centred lone card | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.3 | Team rows | `games-page` | the live site, team rows of a week-11 card | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.3.1 | Forecast score | `games-page` | the live site, score blocks of an upcoming week | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.3.3 | Score distributions | `games-page` | the live site, the chart of a week-11 card | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.3.5 | Win probability box on a phone | `games-page` | the live site at 360 and 1280 px, the win probability box widths | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.4 | Win probability fill | `games-page` | the live site in both themes, boxes at 8%, 50% and 92% | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.7.1 | Actual score on the chart | `games-page` | the live site, week 10's charts | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.8.2 | Bye cards | `games-page` | the live site, week 15 before pairings are set | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.9.1 | Still badge for reduced motion | `games-page` | the live site with reduced motion turned on | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.10 | Points so far | `games-page` | the live site on a Saturday of a live week | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.11 | Player game status | `games-page` | the live site, a live week's lineups | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.11.1 | Final tag | `games-page` | the live site, a live week and finished week 9 | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.12 | Win probability added shown | `games-page` | the live site, week 9's colours | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.12.1 | Win probability added note | `games-page` | the live site, the note on the Games sub-tab | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.13.1 | Opens on Actual | `games-page` | the live site, the toggle on finished week 10 | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.13.2 | Actual scores in both views | `games-page` | the live site, week 10 in both views | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.15 | Bench tag | `games-page` | the live site, the Model view of week 10 | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.15.1 | No win probability added in the model view | `games-page` | the live site, the Model view of week 10 | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.16.2 | Aligned points | `games-page` | the live site at 1280 px, the points column of each list | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.16.3.1 | Free agent on a phone | `games-page` | the live site at 360 px, a lineup with a replacement fill | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.19.1 | Unofficial explained | `games-page` | the live site, the Unofficial chip's tooltip | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.2.1 | One week at a time | `games-page` | the browser's network log on the live site, one week file per week shown | 2026-11-23 | Pass (confirmed when the feature was built) |
| 1.1 | Season simulation | `playoff-odds-simulation` | Every `--runs` default in `src/ffapp/cli.py` (simulate, calibrate, refresh, build, hot) is 10,000 | 2026-11-23 | Pass |
| 1.3 | Forecast table | `league-odds-site` | the live site, column order of each league's table | 2026-11-23 | Pass (confirmed when the feature was built) |
| 1.3.2 | Manager cell | `league-odds-site` | the live site, Manager cells of each league's table | 2026-11-23 | Pass (confirmed when the feature was built) |
| 1.3.3 | Column alignment | `league-odds-site` | the live site at 360 and 1280 px, header and cell alignment | 2026-11-23 | Pass (confirmed when the feature was built) |
| 1.3.4 | Narrow rating columns | `league-odds-site` | the live site at 1280 px, no padding beyond the widest ELO value or header | 2026-11-23 | Pass (confirmed when the feature was built) |
| 1.3.8.1 | Probability fill | `league-odds-site` | the live site in both themes, fills at 0.3%, 50% and 99.6% | 2026-11-23 | Pass (confirmed when the feature was built) |
| 1.3.9 | Grouped probability headers | `league-odds-site` | the live site at 1280 px, the group header spans exactly the four probability columns | 2026-11-23 | Pass (confirmed when the feature was built) |
| 1.3.10.1 | Sort state shown | `league-odds-site` | the live site, headers before and after a sort | 2026-11-23 | Pass (confirmed when the feature was built) |
| 1.4 | Forecast chart | `league-odds-site` | the live site, one line per team and one point per stored as-of week | 2026-11-23 | Pass (confirmed when the feature was built) |
| 1.4.2 | Chart metric buttons | `league-odds-site` | the live site, button order on each league page | 2026-11-23 | Pass (confirmed when the feature was built) |
| 1.4.3 | Team colours | `league-odds-site` | the live site, colours before and after a sort and a metric change | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.1.3 | ELO change fill | `league-odds-site` | the live site, change cells of +20 and -33 in both themes | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.2 | Rating chart | `league-odds-site` | the live site, the dynasty rating chart from 2022 to the latest week | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.2.1 | Rating metrics | `league-odds-site` | the live site, both metrics on the dynasty rating chart | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.2.2 | Rating chart range | `league-odds-site` | the live site, each range on the dynasty rating chart | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.2.3 | Manager colours | `league-odds-site` | the live site, each current Manager's colour in both charts | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.2.3.1 | Former Managers | `league-odds-site` | the live site in both themes, the five former dynasty Managers' lines | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.2.7 | End labels | `league-odds-site` | the live site, every line on the dynasty rating chart has an end label | 2026-11-23 | Pass (confirmed when the feature was built) |
| 9.1 | League pages | `league-odds-site` | the live site, each league in `config/leagues.yaml` has a page and the league control switches between them | 2026-11-23 | Pass (confirmed when the feature was built) |
| 9.1.1 | Sub-tabs | `league-odds-site` | the live site, the sub-tab strip of each league page | 2026-11-23 | Pass (confirmed when the feature was built) |
| 9.2.1.1 | Manager names on one line | `league-odds-site` | the live site at 360 px, no Manager name in the Forecast table wraps | 2026-11-23 | Pass (confirmed when the feature was built) |
| 9.3 | Public pages | `league-odds-site` | the live site opened in a private browser window shows every page | 2026-11-23 | Pass (confirmed when the feature was built) |
| 11.1 | Static site | `league-odds-site` | `site/` holds only HTML, CSS, JavaScript and data files, and its scripts fetch only `site/data/` and the relay | 2026-11-23 | Pass (confirmed when the feature was built) |

## Spec Standard Reviews

| Spec | Last reviewed | Result | Notes |
|---|---|---|---|
| `games-page` | 2026-11-23 | Pass | 19 requirements became 54 under need 2; 4 gaps closed with layout tests; 22 inspections carried over from the feature work |
| `league-odds-site` | 2026-11-23 | Pass | 30 requirements: 7 moved to their specs, 23 became 57 under needs 1, 4, 9 and 11; 11 gaps closed with layout tests; 22 inspections carried over from the feature work |
| `playoff-odds-simulation` | 2026-11-23 | Pass | Worked example: 14 requirements became 31 under need 1; roster drift corrected to a random walk; two gaps closed with tests |
