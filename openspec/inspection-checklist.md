# Inspection Checklist

The record of every inspection the requirements standard calls for (`project-standards` 10.4.1 and 10.8.1). The requirements check (`tests/test_requirements.py`) reads both tables.

- **Requirement Inspections:** every requirement verified by Inspection, with what the inspector looks for, the date it was last inspected and the result. The ID column holds the requirement's ID.
- **Spec Standard Reviews:** every spec, with the date its judgment items were last reviewed and the result. The judgment items are the ones a parser cannot check: every value has a unit and a tolerance or bound, every non-obvious requirement has a rationale, every project term is in `openspec/glossary.md`, and no statement is compound in a way the one-SHALL rule misses.

An inspection is redone whenever its requirement, or a requirement directly linked to it (a parent or a child, primary or association), is added or changed: the check fails when one of them changes in a commit after the one that last recorded the row, and names what changed. If the direct links hold, the rest of the tree still does.

The maintainer's approval at a spec's review is its inspection. A spec edited in a commit after the one that recorded its review fails the check until it is reviewed again and its date updated in the same change. Dates are `YYYY-MM-DD`; a result is Pass, or Pass with notes.

A spec not yet brought to the standard has no row; its "no standard review" finding is listed in `tests/baselines/requirements.json` until it is reviewed.

## Requirement Inspections

| ID | Requirement | Spec | Pass criteria | Last inspected | Result |
|---|---|---|---|---|---|
| 9.5.1 | Phone widths from statistics | `project-standards` | `openspec/config.yaml`, the dated StatCounter figures, next due 2027-10 | 2026-11-23 | Pass (confirmed when the feature was built) |
| 9.6 | Material Design 3 usability | `project-standards` | the live site, focus and pressed states and the type scale | 2026-11-23 | Pass (confirmed when the feature was built) |
| 9.7 | Colour standard | `project-standards` | `site/styles.css`, adjusted tokens carry their OKLCH note | 2026-11-23 | Pass (confirmed when the feature was built) |
| 10.1 | Requirements standard recorded | `project-standards` | `openspec/config.yaml` (context and `rules.tasks`), `CLAUDE.md` | 2026-11-23 | Pass (inspected against the repository) |
| 10.4 | Tolerances on values | `project-standards` | `openspec/inspection-checklist.md`, the spec's standard review | 2026-11-23 | Pass (the maintainer's review of every spec) |
| 10.5 | Rationale where not obvious | `project-standards` | `openspec/inspection-checklist.md`, the spec's standard review | 2026-11-23 | Pass (the maintainer's review of every spec) |
| 10.10 | Glossary | `project-standards` | `openspec/inspection-checklist.md` | 2026-11-23 | Pass (the maintainer's review of every spec) |
| 10.12 | Specs archived before the standard | `project-standards` | the folder and `git tag --list specs-before-requirements-standard` | 2026-11-23 | Pass (inspected against the repository) |
| 10.14 | Standards recorded | `project-standards` | `openspec/config.yaml` (context) and `CLAUDE.md`, each listed standard is present | 2026-11-23 | Pass (inspected against the repository) |
| 10.15 | Writing style | `project-standards` | `openspec/inspection-checklist.md`, each spec's standard review | 2026-11-23 | Pass (the maintainer's review of every spec) |
| 9.4.1.1 | Services simulated | `layout-checks` | `tests/layout/conftest.py`, the simulated relay and the stamped local copy of the site | 2026-11-23 | Pass (confirmed when the feature was built) |
| 9.4.3 | Runs on code pushes | `layout-checks` | `.github/workflows/site.yml`, the tests run with `LAYOUT_REQUIRED` before the deploy | 2026-11-23 | Pass (confirmed when the feature was built) |
| 9.4.3.1 | No browser locally | `layout-checks` | `tests/layout/conftest.py`, the skip and the `LAYOUT_REQUIRED` failure | 2026-11-23 | Pass (confirmed when the feature was built) |
| 8.2.2 | Kept current | `calculation-docs` | each change's review, the changed calculations' sections | 2026-11-23 | Pass (confirmed when the feature was built) |
| 6.7.4.2 | Unmatched report | `start-percentage-snapshots` | `src/ffapp/espn.py`, the unmatched report and its 2% threshold | 2026-11-23 | Pass (confirmed when the feature was built) |
| 6.3 | Projection coverage | `player-projections` | `src/ffapp/projections.py`, each refresh requests every regular-season week of the current season | 2026-11-23 | Pass (confirmed when the feature was built) |
| 5.4.1 | Relay credential | `manual-refresh` | `relay/README.md` and the relay's secrets, the token's scope and that no token is in the repository or `site/` | 2026-11-23 | Pass (confirmed when the feature was built) |
| 5.4.4.3 | Refresh that never lands | `manual-refresh` | `site/refresh.js`, the 10-minute give-up timer and its message | 2026-11-23 | Pass (confirmed when the feature was built) |
| 5.3.2 | Local copy | `site-updates` | `site/updates.js`, an unstamped page skips the version and bundle checks | 2026-11-23 | Pass (confirmed when the feature was built) |
| 5.3.3.2 | Week gone from the new data | `site-updates` | `site/games.js`, a missing week falls back to the index's current week | 2026-11-23 | Pass (confirmed when the feature was built) |
| 5.3.4.2 | Updated time | `site-updates` | `site/updates.js`, the time given to the refresh note is the newer of the two | 2026-11-23 | Pass (confirmed when the feature was built) |
| 5.3.5 | New version note | `site-updates` | the live site, the note and its Refresh button after a code deploy | 2026-11-23 | Pass (confirmed when the feature was built) |
| 5.2.2 | Hot run inputs | `live-refresh` | `.github/workflows/hot.yml`, the cache restore and the offline build when it misses | 2026-11-24 | Pass (re-inspected after linked 6.1.4.1 changed in approved batches; requirement unchanged) |
| 5.2.3.1 | Failed hot run | `live-refresh` | `.github/workflows/hot.yml`, the bundle is sent only after every step succeeds | 2026-11-23 | Pass (confirmed when the feature was built) |
| 5.2.4.2 | Bundle expiry | `live-refresh` | `relay/worker.js`, the bundle is written with a 7-day expiry | 2026-11-23 | Pass (confirmed when the feature was built) |
| 5.1.1 | Worker clock | `refresh-scheduling` | `relay/wrangler.toml`, the cron trigger runs every minute | 2026-11-23 | Pass (confirmed when the feature was built) |
| 5.1.8 | Refresh modes document | `refresh-scheduling` | `docs/refresh-modes.md` holds each listed part | 2026-11-24 | Pass (re-inspected after linked 6.1.7 changed in approved batches; requirement unchanged) |
| 5.5.1 | Started by hand | `refresh-scheduling` | `.github/workflows/refresh.yml` has a `workflow_dispatch` trigger | 2026-11-23 | Pass (confirmed when the feature was built) |
| 5.6 | Deploy on code push | `refresh-scheduling` | `.github/workflows/site.yml`, the build, test and deploy steps | 2026-11-24 | Pass (re-inspected after linked 9.4.3 changed in approved batches; requirement unchanged) |
| 5.6.1 | Deploys never overlap a cold run | `refresh-scheduling` | `.github/workflows/site.yml` and `.github/workflows/refresh.yml` share the `refresh-odds` concurrency group | 2026-11-23 | Pass (confirmed when the feature was built) |
| 5.6.2 | Data pushes deploy nothing | `refresh-scheduling` | `.github/workflows/site.yml`, its path filter excludes the data folders | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.7 | Team News stories | `team-news` | `src/ffapp/news.py`, stories are built for the current season only | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.6.7.1 | Variants kept off the site | `manager-ratings` | `src/ffapp/export.py`, the exported rating history holds only the mean and career mean z | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.5 | Manager identity | `manager-history` | `src/ffapp/managers.py`, the name comes from the latest season's users | 2026-11-24 | Pass (re-inspected after linked 6.2.5, 6.2.5.1 changed in approved batches; requirement unchanged) |
| 4.5.3 | Honours | `manager-history` | each dynasty Manager's Honours against Sleeper's league history | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.5.6 | Luck figures | `manager-history` | `src/ffapp/managers.py`, points against per game beside the league average | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.5.9 | Best players | `manager-history` | `src/ffapp/managers.py`, the best-player and most-seasons picks in the Players block | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.5.9.2 | Most seasons on the team | `manager-history` | `src/ffapp/managers.py`, the most-seasons pick counts seasons with a week on the roster | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.5.10.1 | Drafted Players | `manager-history` | `src/ffapp/moves.py`, moves are built only from stored transactions | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.5.10.3.1 | Offseason moves | `manager-history` | `src/ffapp/moves.py`, an offseason move's week maps to week 1 of the next season | 2026-11-23 | Pass (confirmed when the feature was built) |
| 3.4.5 | Points for any team | `positional-rankings` | `src/ffapp/positions.py`, points per game reads each Player's own stat lines, not matchup points | 2026-11-23 | Pass (confirmed when the feature was built) |
| 7.8 | Calibration on demand | `odds-calibration` | `src/ffapp/cli.py`, the cold run's steps include no calibration | 2026-11-23 | Pass (confirmed when the feature was built) |
| 7.9.1 | Calibration page contents | `odds-calibration` | the live calibration page, each listed figure is present | 2026-11-23 | Pass (confirmed when the feature was built) |
| 8.1 | Forecasts explained | `odds-calibration` | the live calibration page, the "how it works" card covers the four parts | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.10.6.1 | Generated gallery | `game-card-states` | `tools/games_states_gallery.py` writes every state's image to `docs/images/games-states/` from fixture weeks | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.4.3 | Team info bar | `manager-pages` | the live site, the team info bar of a current dynasty Manager | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.4.3.1 | Crest | `manager-pages` | the live site, a Manager with a logo, one with an avatar only and one with neither | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.4.3.3 | Retired Manager's bar | `manager-pages` | the live site, TateFM's dynasty page | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.4.3.4 | Form bars | `manager-pages` | the live site, Form bars of a Manager with wins and losses | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.4.3.4.1 | Form before week one | `manager-pages` | the live site after a draft and before week 1 | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.4.3.4.2 | Form for screen readers | `manager-pages` | the Form bars' accessible name in the browser's accessibility tree | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.4.4.1 | Rivalry Week badge | `manager-pages` | the live site in rivalry week | 2026-11-24 | Pass (re-inspected after linked 4.5.7 changed in approved batches; requirement unchanged) |
| 4.4.4.2 | Projected top scorer | `manager-pages` | the live site after a draft and before week 1 | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.4.4.3 | Retired Manager's tiles | `manager-pages` | the live site, TateFM's dynasty tiles | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.4.4.4 | Tile layout | `manager-pages` | the live site at 1280 px, the first lines of the seven tiles | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.4.4.7 | Tiles link to their source | `manager-pages` | the live site, each tile's link target | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.4.4.8 | Tiles on a phone | `manager-pages` | the live site at 360 px, the tile grid | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.4.6 | Roster card | `manager-pages` | the live site, a dynasty Manager's Roster card | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.4.6.2 | Slot pills | `manager-pages` | the live site, each kind of slot pill in both themes | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.4.6.3 | Status badges | `manager-pages` | the live site, an Out, a Doubtful and a Questionable Player | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.4.7.1 | History tab | `manager-pages` | the live site, a champion's History tab | 2026-11-24 | Pass (re-inspected after linked 4.5.3, 4.5.6 changed in approved batches; requirement unchanged) |
| 4.4.7.3 | Records tab | `manager-pages` | the live site, a Records tab | 2026-11-24 | Pass (re-inspected after linked 4.5.5 changed in approved batches; requirement unchanged) |
| 4.4.7.4 | League History chart | `manager-pages` | the live site, a champion's chart | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.4.7.4.1 | Current season on the chart | `manager-pages` | the live site, a current Manager's chart in week 11 | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.4.9 | Moves card | `manager-pages` | the live site, a 2026 Moves card | 2026-11-23 | Pass (confirmed when the feature was built) |
| 3.2.2.2 | Two columns | `war-leaderboard-page` | the live site at 1280 px, both leagues' grids | 2026-11-23 | Pass (confirmed when the feature was built) |
| 3.2.4.3 | Career Manager | `war-leaderboard-page` | `site/war.js`, the career rows take Manager, team and name from the latest season | 2026-11-23 | Pass (confirmed when the feature was built) |
| 3.2.8 | Calculation explained | `war-leaderboard-page` | the live site, the flow chart below the leaderboards | 2026-11-23 | Pass (confirmed when the feature was built) |
| 3.2.8.3 | No 2024 file | `war-leaderboard-page` | `site/war.js`, the worked example is hidden when the 2024 file or either Player's series is missing | 2026-11-23 | Pass (confirmed when the feature was built) |
| 3.1.2.1 | Two columns | `positional-rankings-page` | the live site at 1280 px, both leagues' grids | 2026-11-23 | Pass (confirmed when the feature was built) |
| 3.1.2.3.1 | Long labels | `positional-rankings-page` | the live site at 360 px, the longest Team Name's label and tooltip | 2026-11-23 | Pass (confirmed when the feature was built) |
| 3.1.5 | Player dots | `positional-rankings-page` | the live site, dots on the dynasty charts | 2026-11-23 | Pass (confirmed when the feature was built) |
| 3.1.5.1 | Shared Manager colours | `positional-rankings-page` | the live site, a Manager's colour on the Forecasts and Positions sub-tabs, and a 2022 former Manager | 2026-11-23 | Pass (confirmed when the feature was built) |
| 3.1.9.1 | Stable offsets | `positional-rankings-page` | `site/positions.js`, the dot placement uses no random numbers | 2026-11-23 | Pass (confirmed when the feature was built) |
| 3.1.10 | Dot popup | `positional-rankings-page` | the live site, hover on desktop and tap on a phone | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.2 | Card columns | `games-page` | the live site at 1280 px, two columns and a centred lone card | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.3 | Team rows | `games-page` | the live site, team rows of a week-11 card | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.3.1 | Forecast score | `games-page` | the live site, score blocks of an upcoming week | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.3.3 | Score distributions | `games-page` | the live site, the chart of a week-11 card | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.3.5 | Win probability box on a phone | `games-page` | the live site at 360 and 1280 px, the win probability box widths | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.4 | Win probability fill | `games-page` | the live site in both themes, boxes at 8%, 50% and 92% | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.7.1 | Actual score on the chart | `games-page` | the live site, week 10's charts | 2026-11-24 | Pass (re-inspected after linked 2.1.7 changed in approved batches; requirement unchanged) |
| 2.1.8.2 | Bye cards | `games-page` | the live site, week 15 before pairings are set | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.9.1 | Still badge for reduced motion | `games-page` | the live site with reduced motion turned on | 2026-11-24 | Pass (re-inspected after linked 2.1.9 changed in approved batches; requirement unchanged) |
| 2.1.10 | Points so far | `games-page` | the live site on a Saturday of a live week | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.11 | Player game status | `games-page` | the live site, a live week's lineups | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.11.1 | Final tag | `games-page` | the live site, a live week and finished week 9 | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.12 | Win probability added shown | `games-page` | the live site, week 9's colours | 2026-11-24 | Pass (re-inspected after linked 2.9 changed in approved batches; requirement unchanged) |
| 2.1.12.1 | Win probability added note | `games-page` | the live site, the note on the Games sub-tab | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.13.1 | Opens on Actual | `games-page` | the live site, the toggle on finished week 10 | 2026-11-24 | Pass (re-inspected after linked 2.1.13 changed in approved batches; requirement unchanged) |
| 2.1.13.2 | Actual scores in both views | `games-page` | the live site, week 10 in both views | 2026-11-24 | Pass (re-inspected after linked 2.1.13 changed in approved batches; requirement unchanged) |
| 2.1.15 | Bench tag | `games-page` | the live site, the Model view of week 10 | 2026-11-24 | Pass (re-inspected after linked 2.1.13 changed in approved batches; requirement unchanged) |
| 2.1.15.1 | No win probability added in the model view | `games-page` | the live site, the Model view of week 10 | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.16.2 | Aligned points | `games-page` | the live site at 1280 px, the points column of each list | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.16.3.1 | Free agent on a phone | `games-page` | the live site at 360 px, a lineup with a replacement fill | 2026-11-23 | Pass (confirmed when the feature was built) |
| 2.1.19.1 | Unofficial explained | `games-page` | the live site, the Unofficial chip's tooltip | 2026-11-24 | Pass (re-inspected after linked 2.1.19 changed in approved batches; requirement unchanged) |
| 2.2.1 | One week at a time | `games-page` | the browser's network log on the live site, one week file per week shown | 2026-11-23 | Pass (confirmed when the feature was built) |
| 1.1 | Season simulation | `playoff-odds-simulation` | Every `--runs` default in `src/ffapp/cli.py` (simulate, calibrate, refresh, build, hot) is 10,000 | 2026-11-24 | Pass (re-inspected after linked 2.3, 1.1.12, 7.1 changed in approved batches; requirement unchanged) |
| 1.3 | Forecast table | `league-odds-site` | the live site, column order of each league's table | 2026-11-23 | Pass (confirmed when the feature was built) |
| 1.3.2 | Manager cell | `league-odds-site` | the live site, Manager cells of each league's table | 2026-11-23 | Pass (confirmed when the feature was built) |
| 1.3.3 | Column alignment | `league-odds-site` | the live site at 360 and 1280 px, header and cell alignment | 2026-11-23 | Pass (confirmed when the feature was built) |
| 1.3.4 | Narrow rating columns | `league-odds-site` | the live site at 1280 px, no padding beyond the widest ELO value or header | 2026-11-23 | Pass (confirmed when the feature was built) |
| 1.3.8.1 | Probability fill | `league-odds-site` | the live site in both themes, fills at 0.3%, 50% and 99.6% | 2026-11-23 | Pass (confirmed when the feature was built) |
| 1.3.9 | Grouped probability headers | `league-odds-site` | the live site at 1280 px, the group header spans exactly the four probability columns | 2026-11-23 | Pass (confirmed when the feature was built) |
| 1.3.10.1 | Sort state shown | `league-odds-site` | the live site, headers before and after a sort | 2026-11-23 | Pass (confirmed when the feature was built) |
| 1.4 | Forecast chart | `league-odds-site` | the live site, one line per team and one point per stored as-of week | 2026-11-23 | Pass (confirmed when the feature was built) |
| 1.4.2 | Chart metric buttons | `league-odds-site` | the live site, button order on each league page | 2026-11-23 | Pass (confirmed when the feature was built) |
| 1.4.3 | Team colours | `league-odds-site` | the live site, colours before and after a sort and a metric change | 2026-11-24 | Pass (re-inspected after linked 2.1.3, 3.1.5.1 changed in approved batches; requirement unchanged) |
| 4.1.3 | ELO change fill | `league-odds-site` | the live site, change cells of +20 and -33 in both themes | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.2 | Rating chart | `league-odds-site` | the live site, the dynasty rating chart from 2022 to the latest week | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.2.1 | Rating metrics | `league-odds-site` | the live site, both metrics on the dynasty rating chart | 2026-11-24 | Pass (re-inspected after linked 4.6.6.1 changed in approved batches; requirement unchanged) |
| 4.2.2 | Rating chart range | `league-odds-site` | the live site, each range on the dynasty rating chart | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.2.3 | Manager colours | `league-odds-site` | the live site, each current Manager's colour in both charts | 2026-11-23 | Pass (confirmed when the feature was built) |
| 4.2.3.1 | Former Managers | `league-odds-site` | the live site in both themes, the five former dynasty Managers' lines | 2026-11-24 | Pass (re-inspected after linked 3.1.5.1 changed in approved batches; requirement unchanged) |
| 4.2.7 | End labels | `league-odds-site` | the live site, every line on the dynasty rating chart has an end label | 2026-11-23 | Pass (confirmed when the feature was built) |
| 9.1 | League pages | `league-odds-site` | the live site, each league in `config/leagues.yaml` has a page and the league control switches between them | 2026-11-23 | Pass (confirmed when the feature was built) |
| 9.1.1 | Sub-tabs | `league-odds-site` | the live site, the sub-tab strip of each league page | 2026-11-24 | Pass (re-inspected after linked 2.1, 4.4, 3.1, 3.2 changed in approved batches; requirement unchanged) |
| 9.2.1.1 | Manager names on one line | `league-odds-site` | the live site at 360 px, no Manager name in the Forecast table wraps | 2026-11-23 | Pass (confirmed when the feature was built) |
| 9.3 | Public pages | `league-odds-site` | the live site opened in a private browser window shows every page | 2026-11-23 | Pass (confirmed when the feature was built) |
| 11.1 | Static site | `league-odds-site` | `site/` holds only HTML, CSS, JavaScript and data files, and its scripts fetch only `site/data/` and the relay | 2026-11-23 | Pass (confirmed when the feature was built) |

## Spec Standard Reviews

| Spec | Last reviewed | Result | Notes |
|---|---|---|---|
| `needs` | 2026-11-23 | Pass | Twelve needs, each with children; no orphans found, so no need added |
| `project-standards` | 2026-11-24 | Pass | Re-reviewed after the archive synced 10.1 to 10.13 (approved in group 7) into the main spec, with 10.8.1's re-inspection scenarios set to the maintainer's linked-requirement rule; earlier: 8 existing requirements became 11 under 9.5 to 9.8, 10.10.1, 10.14 and 10.15 |
| `layout-checks` | 2026-11-23 | Pass | 6 requirements became 9 under 9.4; WebKit and Firefox widths corrected to 440 and 1280 |
| `site-copy` | 2026-11-23 | Pass | 6 requirements became 9 under 10.16 |
| `calculation-docs` | 2026-11-23 | Pass | 3 requirements became 4 under 8.2 |
| `start-percentage-snapshots` | 2026-11-23 | Pass | 5 requirements became 9 under 6.7 |
| `injury-history` | 2026-11-23 | Pass | 3 requirements became 7 under 6.6 |
| `nfl-schedule` | 2026-11-23 | Pass | 3 requirements became 6 under 6.5; live clock kept in the rebuilt copy |
| `player-stats` | 2026-11-23 | Pass | 4 requirements became 6 under 6.4 |
| `player-projections` | 2026-11-23 | Pass | 7 requirements rewritten under 6.3 |
| `sleeper-league-sync` | 2026-11-23 | Pass | 10 requirements became 16 under 6.2; simulation settings left to the specs that use them |
| `data-storage-tiers` | 2026-11-23 | Pass | 7 requirements became 9 under 6.1 |
| `manual-refresh` | 2026-11-23 | Pass | 3 requirements became 10 under 5.4 |
| `site-updates` | 2026-11-23 | Pass | 7 requirements (1 moved from league-odds-site) became 17 under 5.3; update cadence tested |
| `live-refresh` | 2026-11-23 | Pass | 5 requirements became 9 under 5.2 and 11.2; relay tests now run from pytest |
| `refresh-scheduling` | 2026-11-23 | Pass | 8 requirements (2 moved from league-odds-site) became 20 under 5.1, 5.5 and 5.6 |
| `team-news` | 2026-11-23 | Pass | 9 requirements became 22 under 4.7, one per story type |
| `manager-ratings` | 2026-11-23 | Pass | 10 requirements became 20 under 4.6; settings defaults stated; unverifiable scale clause cut |
| `manager-history` | 2026-11-23 | Pass | 13 requirements became 27 under 4.5; compound requirements split |
| `replacement-level` | 2026-11-23 | Pass | 6 requirements became 10 under 3.5; free agents need a positive projection |
| `positional-rankings` | 2026-11-23 | Pass | 9 requirements became 16 under 3.4 |
| `player-war` | 2026-11-23 | Pass | 8 requirements became 22 under 3.3; merged-cut rationale moved to Calculations.txt section 16 |
| `odds-calibration` | 2026-11-23 | Pass | 14 requirements (4 moved from league-odds-site) became 29 under needs 7 and 8; duplicates and an unverifiable clause cut; 5 tests added |
| `game-card-states` | 2026-11-23 | Pass | 8 requirements became 12 under 2.10; verification-only requirement cut; games-page requirements naming states now trace to 2.10 |
| `win-probability-added` | 2026-11-23 | Pass | 3 requirements became 9 under 2.9; baseline corrected to include the live week's provisional Forecast; two tested behaviours stated |
| `live-scoring` | 2026-11-24 | Pass | Re-reviewed: 1.1.12.5's redundant 1.1.12.2 trace dropped to stay under 500 characters |
| `game-predictions` | 2026-11-23 | Pass | 12 requirements became 29 under needs 2 and 1 (1.2.5 slate Forecasts); every requirement verified by an existing test |
| `manager-pages` | 2026-11-23 | Pass | 19 requirements became 51 under need 4; page logic covered by 6 layout tests; 20 inspections carried over from the feature work |
| `war-leaderboard-page` | 2026-11-23 | Pass | 9 requirements became 28 under need 3; untested behaviours covered by 7 layout tests; 4 inspections carried over from the feature work |
| `positional-rankings-page` | 2026-11-23 | Pass | 12 requirements became 26 under need 3; 7 gaps closed with layout tests; 6 inspections carried over from the feature work |
| `games-page` | 2026-11-24 | Pass | Re-reviewed: trace lines to 2.10 added in the approved group 4 batch; statements unchanged |
| `league-odds-site` | 2026-11-23 | Pass | 30 requirements: 7 moved to their specs, 23 became 57 under needs 1, 4, 9 and 11; 11 gaps closed with layout tests; 22 inspections carried over from the feature work |
| `playoff-odds-simulation` | 2026-11-23 | Pass | Worked example: 14 requirements became 31 under need 1; roster drift corrected to a random walk; two gaps closed with tests |
