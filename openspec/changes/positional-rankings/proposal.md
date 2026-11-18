# Proposal

## Why

League members can see odds, games and player WAR, but nothing compares rosters position by position, the way 538's quarterback Elo charts compared every team's QBs at a glance. A "Positional Rankings" tab answers "who has the best running backs, and how deep is everyone" with one dot per rostered player against a replacement-level line.

The line has to be the WAR replacement level, and while exploring this the 2026 WAR replacement level turned out to be wrong. During a season, ESPN's "season" start percentage is only the current week's figure: `data/espn/2026/season.json` is identical to the week 11 snapshot. Players on a bye or hurt that week (Josh Jacobs: owned 91.5%, started 8.6%) look like bench players for every week back to week 1. The consensus starter cut lands too deep, and the 2026 RB replacement level comes out at 5.0 points against 8 to 11 in every stored season. That also inflates every 2026 RB and WR WAR value on the Player WAR tab. It has to be fixed before the new tab draws its line from it.

## What Changes

- **2026 WAR replacement cut fixed** for any season captured live (one with weekly snapshots but not one for every week):
  - Weeks that have their own weekly snapshot use it, as the weekly cut already does.
  - Every other week ranks players by a merged start percentage. A player's figure is the highest percent started across the weekly snapshots of scored weeks in which he played, so bye and injury weeks never count against him.
  - A player who played in none of those weeks (for example, a season-ending injury before snapshots began) uses his percent owned instead.
  - The WAR file records this as a new cut mode, `merged`. Past seasons (no weekly snapshots) and fully captured seasons are unchanged.
  - The reasoning is written down in the WAR spec, the README's Player WAR section and the code.
- **New positional rankings data.** Per league and season, every player on each team's final roster, with:
  - a points-per-game figure over the regular season: actual points in weeks played plus projected points for the remaining regular-season weeks, over games played plus games projected
  - a taxi flag, and an IR or Out flag for the current season
  - each position's WAR replacement level
  - The data is exported to the site and refreshed with the rest.
- **New "Positions" sub-tab** between Games and Player WAR, titled "Positional Rankings":
  - One dot-plot chart per position the league starts (QB, RB, WR, TE, K, DEF in redraft; no K in dynasty), laid out in two columns.
  - One row per manager, ordered by that manager's best player at the position and then their second best, so the labelled top player always sits top right.
  - A dotted "Replacement Level" line on each chart.
  - Dots in manager colours: a light fill with a dark outline, a dotted outline for taxi players, and a red cross for IR or Out.
  - Overlapping dots step up and down off the line.
  - Hovering a dot shows the player's name and PPG.
  - A season dropdown covers past seasons.
- **Swipeable sub-tab menu on phones.** When the sub-tabs don't fit the screen, the menu scrolls sideways under a finger, with snapping and an edge fade, and the page itself never scrolls sideways.
- Layout check registry, README, and tests cover all of the above.

## Capabilities

### New Capabilities
- `positional-rankings`: per league and season, each manager's rostered players by position with their regular-season points per game (actual plus projected), roster flags and the replacement level, stored and exported for the site.
- `positional-rankings-page`: the Positions sub-tab, covering the per-position dot charts, row order, replacement line, dot styling, overlap handling, hover, season control and phone layout.

### Modified Capabilities
- `player-war`: "Yearly and weekly cut" gains the merged cut for partly captured seasons, which replaces the yearly cut for those seasons. It covers the merged start percentage, the ownership fallback, and the scenarios for bye, injury and early season-ending injury.
- `war-leaderboard-page`: "Season control" describes the merged cut for a season marked merged, in place of the yearly-cut note.
- `league-odds-site`: "League pages" gains a fourth sub-tab, "Positions", between Games and Player WAR. "Usable on phones" gains the swipeable sub-tab menu.

## Impact

- **Code:**
  - `src/ffapp/war.py`: cut selection and the merged ranking.
  - New `src/ffapp/positions.py`: PPG and roster rows.
  - `src/ffapp/export.py`: the positions files and their index entry.
  - `src/ffapp/cli.py`: a `positions` step if built separately, or folded into `export`.
- **Site:**
  - `site/index.html`: tab and page section.
  - New `site/positions.js`.
  - `site/app.js`: page routing, hash and reload hook.
  - `site/styles.css`: charts and swipeable sub-tabs.
  - `site/war.js`: the merged-cut note.
- **Data:**
  - `data/war/*/2026.json` is regenerated (cut mode `merged`, new 2026 values).
  - New `site/data/<league>/positions/<season>.json` and `index.json`.
- **Tests:** WAR cut tests, positions tests, export tests, and `tests/layout/controls.py` entries for the new tab, season dropdown, dot hover and swipeable menu.
- **No new dependencies.** The refresh workflow is unchanged apart from the extra export output.
