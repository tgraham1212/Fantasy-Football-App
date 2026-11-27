# Proposal

## Why

Managers argue every season about who had the easy schedule, and the site has no way to settle it. The League sub-tab was planned with a Strength of Schedule tab; this change adds it with two views that answer two different questions: how strong were the opponents a Manager faced (Weekly Ranks), and how many wins the schedule cost or gave them (Schedule Swap).

## What Changes

- **Weekly Ranks:** each regular-season week, every team is ranked by points scored (1 = most, equal scores share the better rank). Each team is credited with its opponent's rank that week, and the averages over played weeks, upcoming weeks and the whole season are kept. The lowest season average is the hardest schedule ("1st Hardest"). Upcoming weeks rank teams by the simulation's forecast team score.
- **Schedule Swap:** an N x N table of each Manager's wins had they played every other Manager's schedule with their own weekly scores. When the other schedule has its Manager playing this one, this Manager plays that schedule's Manager instead. Played weeks count actual wins (a tie is half a win); upcoming weeks count the simulation's win probability for that pairing, in line with the Forecasts. The Schedule Difficulty Index is the average wins across all N schedules minus wins on the Manager's own schedule; the highest index is the hardest schedule. The range of wins across schedules is shown.
- **Simulation:** for each upcoming regular-season week, each run of the season simulation also records every team's forecast score and every pairing's win probability, so the swap uses the same simulated scores as the Forecasts.
- **Export:** a strength of schedule file per league, holding every stored season (past seasons fully played).
- **Page:** a second League tab, "Strength of Schedule", with a Weekly Ranks | Schedule Swap switch and a Season selector, laid out as in the canvas mockups: heat-grid cells coloured by bucket (opponent rank 1–3, 4–6, 7–9, 10–12; swap wins 2+ fewer, fewer than 2 fewer, fewer than 2 more, 2+ more than on the Manager's own schedule), played weeks faded and forecast weeks solid, cell text a tint of its cell colour. On phones each table scrolls sideways inside its card with the Manager column pinned, as on the Forecast table.
- **Docs:** a new Calculations section, glossary terms, and a feature doc with its diagram.

## Capabilities

### New Capabilities
- `strength-of-schedule`: the Weekly Ranks and Schedule Swap figures for every stored season of a league, their rules (regular season only, ties, substitution, forecast weeks) and the export file.
- `strength-of-schedule-page`: the League sub-tab's Strength of Schedule tab: the view switch, Season selector, the two heat-grid tables, sorting, colours, the pinned Manager column on phones and the URL.

### Modified Capabilities
- `playoff-odds-simulation`: the season simulation also stores, for each upcoming regular-season week, every team's forecast score and the win probability of every pairing of teams.

## Impact

- **Code:** `src/ffapp/simulate.py` and `src/ffapp/odds.py` (pairwise results in the Forecast payload); new `src/ffapp/schedule_strength.py`; `src/ffapp/export.py` (new file per league); `site/index.html`, `site/league.js` (or a new `site/schedule.js`), `site/styles.css`.
- **Data:** each stored Forecast file gains an upcoming-weeks block (about 12 x 12 probabilities per week); a new `site/data/<league>/schedule.json` built by `python -m ffapp build`.
- **Tests:** new unit tests for the figures and export, layout tests for the tab, registry entries in `tests/layout/controls.py`, copy IDs in `site-copy.txt`.
- **Docs:** `Calculations.txt` (new section 24), `openspec/glossary.md`, `docs/strength-of-schedule.md` and `tools/strength_of_schedule_diagram.py`, `docs/requirements.md` diagrams.
