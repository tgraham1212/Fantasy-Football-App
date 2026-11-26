# Proposal

## Why

Managers want to find league history, all-time figures and season-over-season records quickly. Today the site only answers "what about this one Manager?" (the Managers sub-tab); nothing answers "what about the league?". Most of the data is already stored (every season's matchups, brackets, rosters, transactions and Player WAR), so a league-wide Records page is mainly new calculation and display work.

## What Changes

- A sixth league sub-tab, **League**, for league-wide information about the current and past seasons. It holds its own tabs; this change adds the first, **Records**. Later changes add Strength of Schedule, History (with draft data) and Trades.
- **Records** has two views behind a Managers / Players switch:
  - **Managers:** Champions (each finished season's champion, runner-up, toilet bowl champion or last place, the champion's record, points and best Player by WAR); All-Time Standings (regular-season record, win %, point differential, playoff appearances and record, finishes in 1st, 2nd and 3rd, and toilet bowl or last place; current Managers first, former Managers in their own unranked group); Weekly Records (eight records from games that matter, each with its holder and tags for the game); Season Records (fourteen records per Manager-season, with the season's result).
  - **Players:** Best Games, Best Bench Games, Career Scoring and Championships, each filtered by position.
  - Selecting a record opens a pop-up with its top 25. Equal values share a rank, the oldest first.
- A new glossary term, **game that matters**: the regular season, the winners-bracket games on the path to the final, the 3rd place game, and in a toilet-bowl league the losers-bracket games on the path to the toilet bowl final and that final. Consolation and placement games do not count.
- Lineup choices are recalculated for past seasons (2021 to 2025) from the stored weekly Projections, so the lineup-choices season records cover every season. (The lineup-choices feature itself is reviewed in a later change.)
- A new data export per league holds everything the Records page draws.

## Capabilities

### New Capabilities
- `league-records`: the league-wide records computed from stored league data: champions, all-time standings, weekly records, season records and Player records, with ranking, tie and eligibility rules, exported for the site.
- `league-records-page`: the League sub-tab's Records page: its layout, the Managers and Players views, the record pop-up, tags and phone layout.

### Modified Capabilities
- `league-odds-site`: requirement 9.1.1 (sub-tabs) gains a sixth sub-tab, League.
- `game-predictions`: lineup choices (2.8) are also computed for past seasons from stored weekly Projections.

## Impact

- **Code:** a new records module and export (`src/ffapp/`), the build and export steps, a new site page script and styles (`site/`), the sub-tab strip and URL routing, the past-season lineup-choices calculation (`src/ffapp/views.py`).
- **Data:** a new derived file per league (`site/data/<league>/records.json`), built by `python -m ffapp build`, not stored in git. Past-season lineup choices are derived from stored Projections and matchups.
- **Docs and checks:** new `Calculations.txt` sections, a feature doc and diagram, glossary entry, site-copy IDs, layout-check controls, requirements, inspection checklist rows and requirement diagrams.
- **Dependencies:** none new. Logos, avatars and Player photos come from Sleeper's image server, as on the Managers sub-tab.
