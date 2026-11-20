# Proposal

## Why

Managers want to see their own story in the league: results against each rival, how they finished each year, their records, their players and their luck. The site has the data (matchups, brackets, rosters, ratings, WAR and forecast history) but no page that puts it together for one manager. This change adds a **Managers** tab, inspired by Football Manager's club page. It is the first of two changes; the second adds the transactions and drafts sync behind the Moves lists, then keepers.

## What Changes

- **New sub-tab:** "Managers", between Positions and Player WAR. It shows one manager at a time.
  - **Picker:** a dropdown plus previous and next arrows. Current managers come first, then a "Retired" group.
  - **URL:** the manager is kept in the URL, for example `#redraft/managers/<user>`.
  - **Links:** every manager name in the site's tables links to that manager's page.
- **Team info bar:**
  - **Crest:** team logo, then avatar, then initials in the team colour.
  - **Team name.**
  - **Banners:** champion banners and, after a gap, toilet bowl banners. They stack when out of room.
  - **Form:** bars for the last five results (+1 win, −1 loss, 0 draw or no game; all 0 before week 1).
  - **Facts:** Founded (current managers) or Seasons (retired), All-Time record, Rating, Rival.
- **Season info bar:** seven tiles.
  - Current League Position, Last Result, Next Matchup (with a Rivalry Week badge), Manager (Win Rate), Top Scorer, Best Player All-Time, Playoff Forecast.
  - Before week 1, Top Scorer is the highest projected scorer, marked "(Projected)".
  - Retired managers see their last season.
- **Four cards** (desktop: equal height, scrolling inside, roster widest; phone: a second tab row, no inner scroll, a shared minimum height):
  1. **Roster:**
     - slot pills in Sleeper's position colours (FLEX in thirds, IR red, Taxi gold);
     - status badges from the site's one out-status list;
     - a PPG chip coloured green, grey or red against the position's replacement level;
     - starter and bench points in the footer.
  2. **Team History**, with three tabs:
     - **History:** an About sentence, the finishes chart (trophy, 💩, forecast dot), Honours, and Luck (all-play record, points against compared with the league average, points left on bench).
     - **Head to Head:** one row per opponent.
     - **Records:** with "#1 / #2 / #3 All Time" tags in gold, silver and bronze, and team name history.
  3. **Moves:**
     - **Live in this change:** a FAAB meter and a Players block (most seasons on the team, "the one that got away").
     - **Placeholder:** skeleton rows where the add, drop and trade lists go. The layout is final, so the second change fills it in without anything moving.
  4. **Team News:** a feature story, then More Stories. Stories are generated from data for the current season only:
     - results, forecast moves, injuries, practice reports, depth-chart moves and trending adds;
     - records and streaks, WAR milestones and rivalry week;
     - Team of the Week, shown only when the manager's player made it.

     Every headline is a template in `site-copy.txt`.
- **New data:**
  - **Rivals table:** in the league config, redraft only. Rivals are attached to the team, and each season records its rivalry week.
  - **Sleeper player details:** body part, practice participation and depth-chart order, saved each week alongside the injury statuses.
  - **Trending adds:** Sleeper's trending adds, saved at each refresh.
- **WAR wording, folded in at the owner's request** (no WAR value changes):
  - **Calculations:** `Calculations.txt` and the WAR spec describe WAR as summed over active weeks.
  - **Code:** `war.py` sums active weeks against an active-weeks baseline.
  - **Worked example:** Kittle vs Bowers shows missed weeks as "Bye" or "Out", not as replacement-level fill-ins.
- **Fixes the page needs:** a WebKit rule (`min-width: 0`) so a scrolling strip cannot widen the page column.

## Capabilities

### New Capabilities

- `manager-pages`: the Managers sub-tab, its picker and URL, the two info bars, the four cards and their phone behaviour, and links from manager names.
- `manager-history`: the per-manager figures:
  - finishes and honours;
  - head to head, records and their all-time ranks;
  - luck, form, rivals and the dynasty nemesis;
  - best player all-time, the player move windows and the players block;
  - the exported manager file.
- `team-news`: story generation, its templates, ordering and limits, the trending adds and the player-detail stories.

### Modified Capabilities

- `league-odds-site`: "League pages" gains the Managers sub-tab between Positions and Player WAR.
- `player-war`: "Weekly win probability" and "Wins above replacement" are restated over active weeks, with identical values.
- `war-leaderboard-page`: the "Calculation explained" walkthrough marks missed weeks as Bye or Out.
- `injury-history`: adds saving the extra player details each week.

## Impact

- **Python:**
  - new `src/ffapp/managers.py` (history figures) and `src/ffapp/news.py` (stories);
  - `export.py` writes `site/data/<league>/managers.json`;
  - `injuries.py` saves player details;
  - `sleeper.py` adds the trending endpoint;
  - `war.py` gets the active-weeks sum;
  - `config.py` reads rivals from `config/leagues.yaml`.
- **Site:**
  - new `site/managers.js` and styles in `site/styles.css`;
  - `index.html` gets the sub-tab and page container;
  - `app.js` adds routing and name links, also in `games.js`, `positions.js` and `war.js`;
  - `war.js` gets the walkthrough cells.
- **Docs and copy:**
  - `Calculations.txt`: new sections for manager history and team news, section 16 reworded, and the new modules added to `tests/test_calculations_doc.py`;
  - new copy IDs in `site-copy.txt` for all new text and story templates;
  - README.
- **Tests:**
  - unit tests for each figure and story type;
  - the layout check's new views and controls in `tests/layout/controls.py`, at every width and engine;
  - accessibility (axe, touch targets, colour tokens) with the new tokens;
  - a test that WAR values are unchanged.
- **Data:**
  - `data/players/<season>/week_NN.json` (details);
  - `data/trending/<date>.json`;
  - the rivals block in `config/leagues.yaml`.
- **Second change:** transactions and drafts sync, Moves lists with WAR grades, Moves stories, optional ESPN headline links, keepers.
