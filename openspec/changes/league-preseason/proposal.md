# Proposal

## Why

The Draft tab grades each pick, but not each team. After a draft, Managers want to know how good the team they just built is: a title contender, a playoff team, or a team heading for last place. That should come from the same season simulation behind the Forecasts, and depth should count, since a bench decides how a team survives injuries.

## What Changes

- **Preseason Forecast:** for every season with a complete draft, one preseason Forecast is made once and kept as a record: redraft 2021 to 2026, dynasty 2022 to 2026, and each future season at the first cold run after its draft.
- **Preseason values:** each Player's per-game value is his preseason projected season stat line, scored with that league-season's own scoring and divided by 17. He scores nothing in his NFL team's bye week.
  - **Sources:** ESPN's season projections for 2021, 2022 and 2024 onward. They keep the preseason line even for Players hurt early.
  - **2023:** ESPN's 2023 lines are blank for many top Players, so 2023 uses Sleeper's season projections, and a Player's week-1 Projection where Sleeper has none.
  - **Matching:** ESPN Players are matched to Sleeper Players by normalised name, position and NFL team, and defences by team.
- **Rosters:** the drafted roster in redraft, and the week-1 roster without taxi Players in dynasty. A team with no kicker or defence plays replacement level (Calc 14) in that slot.
- **Absences:** in every simulated week, any rostered Player can miss the game at his position's pooled injury rate, measured from the 2021 to 2025 injury reports: QB 10.6%, RB 11.9%, WR 11.4%, TE 10.2%, K 4.4%, DEF 0%. The best healthy bench Player fills an absent starter's slot, else replacement level.
- **Outputs:** per team:
  - title, playoff and last-place shares, forecast record and points per week;
  - Wins Saved, the Forecast wins the bench saves (the same draws with absent starters replaced at replacement level instead);
  - for finished seasons, the actual final place.
- **Grades:**
  - **Letters:** A Title Contender, B Playoff Team, C Playoff Bubble, D Unlikely Playoffs, F Last Place.
  - **Plus and minus:** for teams near the edges of a band, using the agreed thresholds.
  - **F only when earned:** no team gets an F unless its last-place share reaches 20%.
  - **Checked before going live:** the thresholds are replayed over every stored season, and the owner confirms the grade counts.
- **Page:** a fourth League tab, "Preseason", as in the canvas mockups (PreseasonGrades, Preseason, PreseasonPhone).
  - **Desktop:** a Season picker, then one table per season with the columns Grade, Manager, Title, Playoffs, Last (each share with a bar), Forecast, Pts/Wk, Wins Saved and Finished. A grade key and a method note sit below.
  - **Phones:** one row per team.
  - **Grade colours:** 13, with the same hue within a letter and lightness stepping towards the ends of the scale.
- **Docs:** a new Calculations section, glossary terms, a feature doc with its diagram, and the requirement diagrams.

## Capabilities

### New Capabilities
- `preseason-forecast`: the preseason Forecast and its grades. It covers the preseason values and their sources, ESPN matching, the rosters, absences with the bench filling in, the outcomes, Wins Saved, the grade bands, the actual finish, when it runs, and the export.
- `preseason-page`: the League sub-tab's Preseason tab. It covers the Season picker and URL, the table with share bars and sorting, the grade colours and key, the explanation, and the phone layout.

### Modified Capabilities
- `data-storage-tiers`: the preseason Forecasts, with the per-Player values they used, join the records committed to git.

## Impact

- **Code:**
  - New `src/ffapp/preseason.py`: values, matching, rosters, the absence simulation, grades and export.
  - `src/ffapp/espn.py`: the season projections call.
  - `src/ffapp/cli.py`: a `preseason` command and cold-run step.
  - `src/ffapp/export.py`.
  - `site/index.html`, `site/league.js`, new `site/preseason.js`, `site/styles.css`.
- **Data:**
  - A new record per league-season: `data/preseason/<league>/<season>.json`.
  - A derived `site/data/<league>/preseason.json`.
  - A backfill of 11 league-seasons, using ESPN requests for 2021 to 2026.
- **Tests:** unit tests for the values, matching, absences, Wins Saved, grades and export; layout tests for the tab; entries in `tests/layout/controls.py`; contrast checks for the 13 grade colours in both modes; copy IDs.
- **Docs:**
  - `Calculations.txt`: a new section 26.
  - `openspec/glossary.md`: Preseason Forecast, Preseason grade, Wins Saved.
  - New `docs/preseason.md` and `tools/preseason_diagram.py`.
  - `docs/refresh-modes.md` ("Where Data Lives").
