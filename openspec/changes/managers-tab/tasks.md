# Tasks

## 1. Data and Figures (Python)

- [x] 1.1 Rivals config: add the `rivals` block (pairs by roster id, `rivalry_week` per season) to `config/leagues.yaml` for redraft, seeded per design decision 5. Parse and validate it in `config.py`. Verify: config tests cover a valid block, an unknown roster id and a league without the block.
- [x] 1.2 Player details and trending:
  - `injuries.py` saves `data/players/<season>/week_NN.json` (body part, practice, depth chart);
  - `sleeper.py` adds `trending_adds()`;
  - a new optional refresh step saves `data/trending/<season>/<date>.json`.

  Verify: tests for the week-overwrite rule, and for a failed trending fetch warning without stopping the refresh.
- [x] 1.3 `managers.py`, identity and finishes: managers across seasons (current or retired), team names by season, crest source, chart colour, and final places from brackets (toilet bowl reversed). Verify: tests that 2021–2025 champions and toilet bowl teams match the league's history in both leagues, that the dynasty retired managers are KoPe17, DeekBurg and Hildebrand009 (2022) and TateFM (2022–2023), that redraft has none, and that the SpookyCast/Jdeguire account is one manager.
- [x] 1.4 `managers.py`, history figures:
  - honours, head to head, and records with all-time ranks (ties share);
  - luck: all-play record, wins above pace, points against compared with the league average, bench points from `ppts`;
  - form, the dynasty nemesis, and rivalry-week records.

  Verify: unit tests for each with hand-checked fixtures, including the 113.46 bench example and a three-way tie in ranks.
- [x] 1.5 `managers.py`, move windows and players: added and departed windows from weekly matchup rosters, window WAR from the weekly WAR rows, Best Player All-Time, most seasons on the team, the one that got away, FAAB used by season. Verify: tests for the drop / re-add / drop example, redraft windows ending at the season, and dynasty windows carrying over.
- [x] 1.6 `news.py`: every story type in the team-news spec, ranking and the feature pick, the per-week cap, Team of the Week, and the retired managers' final-season story. Verify: a test per story type, plus feature selection (a record beats a result) and the cap.
- [x] 1.7 Export `site/data/<league>/managers.json` from `export.py`, with every block the page needs, for current and retired managers. Verify: an export test checks the file lists every manager and validates its shape.

## 2. WAR Wording (Folded In)

- [x] 2.1 Refactor `player_weeks` and `baseline_wins` in `war.py` to active weeks only, keeping missed weeks in the weekly rows with `played: false` and no score. Verify: a test rebuilds WAR for every stored season and league and matches the previous values to four decimal places.
- [x] 2.2 Walkthrough cells in `war.js`: missed weeks read "Bye" (no NFL game) or "Out", with no score or win probability. Update the WAR-21 note text in code with a copy ID; the owner reviews the pending `site-copy.txt` edit. Update `Calculations.txt` section 16 wording. Verify: `tests/test_calculations_doc.py` and the WAR page layout tests pass.

## 3. The Page (Site)

- [x] 3.1 Sub-tab, routing and picker:
  - "Managers" between Positions and Player WAR in `index.html`;
  - routing with the manager in the URL, in `app.js`;
  - the dropdown with ‹ › arrows and the Retired group, all 48 px on phones;
  - a new `site/managers.js` loaded with `?v=__BUILD__`.

  Register the controls in `tests/layout/controls.py`. Verify: the coverage test and URL tests pass.
- [x] 3.2 Team info bar per the mockup: crest order with image fallbacks, team name, banner rods (stacking when out of room), form bars, and the facts with dividers, plus the retired state. Verify: layout tests at every width, with a manager holding many banners.
- [x] 3.3 Season info bar: the seven tiles in the aligned two-line layout, the score shrinking first, short player names, links, the pre-season and retired states, and two columns on phones. Verify: a layout test with the worst-case values (188.6 score, +12.4 WAR · 11 seasons, J. Smith-Njigba at 360 px), with nothing cut and nothing outside its tile.
- [x] 3.4 Roster card: slot pills (FLEX thirds, IR red, Taxi gold), status badges from the out list, the PPG chip scale, the starter and bench footer, sortable headers. Verify: layout tests show no name cut and no sideways scroll.
- [x] 3.5 Team History card: the three tabs, the League History chart (trophy, 💩, forecast dot, one-line legend), Honours, Luck, Head to Head (scores never wrap), Records with rank tags and team names. Verify: layout tests on every tab in all engines.
- [x] 3.6 Moves card in its change 1 state: season picker and filter, FAAB meter, skeleton list rows with the "on its way" line, and the live Players block. Verify: layout tests at every width.
- [x] 3.7 Team News card: the feature story with a picture sized to the card, More Stories, the templates with `NEWS-` copy IDs for every story type, and "Show more" on phones. Verify: a layout test that nothing leaves the card at 1366, 1280, 1100 and phone widths.
- [x] 3.8 Card layout and phones: equal-height desktop cards scrolling vertically only, the 2 × 2 grid under 1100 px, the phone card tab row with no inner scroll and a shared minimum height, and the WebKit `min-width: 0` fix. Verify: the full layout check in all engines, plus a test that no phone card scrolls inside itself.
- [x] 3.9 Manager name links from Forecasts, Games, Positions, Player WAR and the Head to Head rows. Verify: a test that each page's manager names link to the right Managers URL.
- [x] 3.10 New colour tokens in all three blocks, classified in `tests/test_colour_contrast.py`. Run `python -m ffapp site-copy` for all new text, and bring pending edits to the owner before `--apply`. Verify: the colour, axe (both modes), touch (with the wide-font pass), nomenclature and copy checks pass with empty baselines.

## 4. Docs and Verify

- [x] 4.1 `Calculations.txt` sections 19 (MANAGER HISTORY) and 20 (TEAM NEWS), with `managers.py` and `news.py` registered in `tests/test_calculations_doc.py`. README: the Managers tab, the rivals config and the new data files. Verify: the docs tests pass.
- [x] 4.2 Full verification:
  - `pytest`;
  - `node --test relay/worker.test.mjs`;
  - `LAYOUT_REQUIRED=1 pytest tests/layout` in all engines;
  - `python -m ffapp site-copy --check`;
  - `openspec validate managers-tab --strict`.

  Take screenshots of the tab at 1366, 1100, 440 and 360 px in light and dark mode, for a current manager, a retired manager and a dynasty manager, and list them for the owner. Verify: everything passes and the screenshots are listed.

## Workflow follow-up

- Commit, push and archive with spec sync when the owner asks.
- Then explore change 2: the transactions and drafts sync, the Moves lists with WAR grades, Moves stories, optional ESPN headline links and keepers.
