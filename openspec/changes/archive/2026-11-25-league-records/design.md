# Design

## Context

Everything the Records page shows can be built from data already stored as records:
- every season's matchups (team points, starters, rostered Players), brackets, rosters (with reserve and taxi), users (Team Names) and transactions under `data/leagues/<league>/<season>/`;
- Player WAR files per season (`data/war/<league>/<season>.json`), whose weekly entries hold each Player's league-scored points, played or not;
- weekly stats (`data/stats/<season>/`), which record each Player's NFL team that week;
- stored weekly Projections (`data/projections/<season>/`) and realised replacement levels (`data/replacement/`).

`src/ffapp/managers.py` already computes per-Manager history:
- Manager identity across seasons, a vacant roster counting as its previous Manager (4.5);
- final places from the brackets (4.5.2), honours (4.5.3), records ranked against league history (4.5.5) and all-play luck (4.5.6);
- Player windows on each team (4.5.8).

`src/ffapp/export.py` writes one file per league per site page. The site loads each sub-tab's script from `site/app.js`, which also routes `#<league>/<sub-tab>` URLs.

The mockup canvas (https://claude.ai/artifact/C6NJmtDnhbZVJro3ddDn9v) holds the approved layouts with real data. It covers:
- Champions;
- All-Time Standings;
- Weekly Records and the top-25 pop-up;
- Season Records;
- the Players view.

## Goals / Non-Goals

**Goals:**
- One league records file per league, computed from stored data at build time, holding the top 25 of every league record (per position for Player records).
- The League sub-tab and its Records tab as in the mockups, on every supported browser and phone width.
- One definition of "game that matters", used by every league record that counts games.
- Lineup choices for 2021 to 2025, so the lineup-choices season records cover every season.

**Non-Goals:**
- The other League tabs: Strength of Schedule, History (with draft data) and Trades come in later changes.
- Reviewing or changing how lineup choices are calculated. The owner expects a review after this change. This change only applies the existing formula to past weeks.
- Changing the Managers sub-tab's own records or playoff figures. They keep their rules; aligning them is a follow-up if wanted.

## Decisions

1. **Two capabilities, two modules.**
   - **Where:** a new `src/ffapp/league_records.py` computes everything, and `export.py` writes it to `site/data/<league>/records.json`. A new `site/league.js` draws the page.
   - **Why:** this mirrors `player-war` and `war-leaderboard-page`, and keeps the Managers code from growing further.
   - **Alternative:** extending `managers.json`. Rejected, because the Managers file is already the largest export and is loaded per visit.

2. **Reuse the Manager history building blocks.**
   - **Reused:** identity, final places, honours, all-play luck and Player windows come from `managers.py`, imported, not copied, so a Manager's history and the league records can't disagree.
   - **Best Player:** the champion's Best Player is the Player with the most WAR summed over his weeks on the champion's roster that season (the windows of 4.5.8).

3. **One game classifier.** A single function labels every stored game:
   - regular season;
   - Playoffs, Championship, 3rd Place;
   - Toilet Bowl, Toilet Bowl Final;
   - not counted.

   It reads the brackets: winners-bracket games with no placement or placement 1 or 3; in a toilet-bowl league, losers-bracket games with no placement or placement 1. A bracket round maps to week `playoff_week_start + round - 1`. Every league record, the streaks and the playoff record use this classifier. The glossary gains **game that matters**, and also **league record**, because the glossary's **Record** means stored data.

4. **Ranking.** Each league record is sorted by value, then by date (oldest first), then by a record-specific tie-break:
   - points scored for best and worst record;
   - WAR in title seasons for championships;
   - point differential for standings.

   Records use competition ranking, where equal values share a rank (1, 2, 2, 4). Standings and championships use their tie-break for distinct ranks, as approved. The export keeps the top 25 entries; the front page shows the first.

5. **Current season.**
   - **Season records:** in progress, the current season enters only the most, best and longest season records, marked current.
   - **Champions:** a season enters Champions only once its final has a winner.
   - **Weekly records:** they include current-season games that matter, tagged This season.

6. **Season figures.**
   - Points, points against, record, luck and the playoff-line records use regular-season games.
   - Streaks run over games that matter within one season.
   - Bench points are Sleeper's potential points minus actual points (as 4.5.6).
   - Luck is actual wins minus all-play wins (Calculations.txt section 19), the same figure as Managers → History.

7. **Player records.**
   - **Points:** best games and career scoring read the WAR files' weekly league-scored points for every Player, whatever his roster status.
   - **Status:** a week's status (started, bench, free agent) comes from that week's matchup `players` and `starters`.
   - **NFL team:** taken from that week's stored stats; a defence's team is its ID.
   - **Championships:** the champion's title-week matchup `players` plus the season roster's `reserve` and `taxi`. The stored roster file is the end-of-season snapshot, which is the title week.

8. **Lineup choices for past seasons.** For each finished week of 2021 to 2025, the build:
   - rebuilds each team's model lineup from that week's stored Projections, with `views.model_lineup`;
   - takes the actual starters from the matchup;
   - fills replacements with the week's realised level;
   - computes lineup choices with the existing `views.lineup_choices`.

   The results are derived data, computed during the build and not stored. The 2026 game log keeps its own values. The stored Projections are the last ones fetched each week, not always the exact pre-kickoff figures; the feature doc and `Calculations.txt` say so.

9. **Page structure.**
   - **URL:** `#<league>/league/records[/players]`, routed by `app.js` like the other sub-tabs.
   - **Controls:** the League tab strip and the Managers / Players switch are pressed-state buttons, as in the mockups.
   - **Pop-up:** a native `<dialog>`. At phone widths CSS turns it into a bottom sheet with a 48 by 48 px close button. Focus moves into the pop-up and back to the record on close.
   - **Phone lists:** below 600 px the tables become lists, each record row one button.
   - **Pictures:** logos, avatars and Player photos use the same Sleeper image helpers as the Managers sub-tab, moved to a shared module, so both pages fall back the same way.

10. **Colours.** Tag and medal colours reuse the existing hues: gold, the roster position colours, the rivalry pink family, and the accent blue for This season. Bronze and silver are new tokens derived in OKLCH from the existing gold hue and neutral grey. All are checked by `tests/test_colour_contrast.py` in both modes.

11. **Copy and checks.**
    - **Copy IDs:** every heading, column label, tag, note and the luck explanation gets a copy ID, and `python -m ffapp site-copy` runs in the same change.
    - **Layout checks:** every new control goes into `tests/layout/controls.py`: the League sub-tab, League tab, view switch, position filters, Top 25 buttons and pop-up close.

12. **Feature docs.**
    - **New:** `docs/league-records.md`, with `tools/league_records_diagram.py`, registered in `tests/test_feature_docs.py` for `src/ffapp/league_records.py` and `site/league.js`.
    - **Affected:** `docs/requirements.md`, because the glossary and inspection checklist change, so it is updated and its diagrams redrawn.
    - **Not affected:** `docs/simulation.md`, unless `src/ffapp/games.py` is edited (not planned), and `docs/refresh-modes.md`.

## Risks / Trade-offs

- **Requirements check before apply.** The new requirements name tests that don't exist yet, so `tests/test_requirements.py` reports them as missing until the apply step writes the tests. Commit the proposal together with the first apply work, or the deploy check fails.
- **Past lineup choices use the last stored Projections.** They are close to, but not always, the exact pre-kickoff figures. The lineup-choices review that follows this change can revisit this.
- **Title-week rosters.** IR and taxi come from the end-of-season roster snapshot. A Player moved to IR after the final would count. That is acceptable, since nothing changes after the final.
- **Build time.** Past-season lineup choices add a model-lineup pass over about 90 league-weeks per league. That is small next to the simulation, and the build stays local-only.
- **Two playoff records.** Managers → History's playoff record keeps its current rule, which may differ from the League record's games-that-matter rule. If Managers notice, aligning them is a small follow-up.
