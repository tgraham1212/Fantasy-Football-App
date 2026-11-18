# Design

## Context

See proposal.md for motivation. Current state, from the code and data:

- `src/ffapp/war.py` picks the cut with `cut_mode()`: weekly when every scored week has `data/espn/<season>/week_NN.json`, otherwise yearly, ranking every week by `season.json`.
  - For 2026, `season.json` is byte-identical to `week_11.json`. The snapshot command rewrites it on every in-season run with ESPN's current-week figures.
  - Weekly snapshots exist for 2026 weeks 10 and 11 only, and week 11 is not yet scored.
  - Result: 2026 RB replacement level 5.0 in both leagues, against 7.8 to 11.8 in 2021 to 2025.
- An in-memory test that ranked each player by the higher of his `season.json` and week 10 start % moved 2026 redraft levels from QB 18.0 / RB 5.0 / WR 8.2 to QB 17.4 / RB 6.3 / WR 10.5. The remaining RB gap matches players hurt before week 10, whom no snapshot shows active.
- Rosters:
  - `data/leagues/<league>/<season>/rosters.json` holds `players`, `taxi` and `reserve` lists.
  - For a completed season, it equals the final week's matchup rosters. Checked for redraft 2025: 12 of 12 teams match.
  - For the current season, the refresh re-syncs it every run.
- Stats are in `data/stats/<season>/week_NN.json` for every player, free agents included. Projections are in `data/projections/<season>/week_NN.json`, stored through week 17 for 2026. Both are scored with `scoring.actual_points` and `scoring.projected_points` under `league.resolve_settings`.
- Injury statuses are in `data/injuries/<season>/week_NN.json`: Sleeper player id to status, such as `IR` or `Out`.
- Manager colours: `app.js` assigns `--team-1..12` by roster id and hands `colorOf(rid)` to page modules (`games.js`). Former members use the grey tokens from `tools/team_palette.py --greys`.
- The sub-tab menu is `nav.subtabs#subtabs`, an inline-flex row of three buttons. The layout check registry lists the sub-tabs and checks that `#subtabs` stays inside the screen.

## Goals / Non-Goals

**Goals:**
- A replacement level for partly captured seasons that a bye or injury in one snapshot week cannot distort, with the reasoning recorded in the spec, the README and the code.
- A Positions page drawn as plain SVG with the clean look of the 538 charts, readable on phones.
- A sub-tab menu that holds four or more tabs on a phone without widening the page.

**Non-Goals:**
- A dynamic axis per season. The fixed range is tried first, and the user can ask for dynamic later.
- Converting points per game to Elo or WAR on this page.
- Playoff weeks in points per game.
- Storing positional rankings under `data/`. They are derived at export time from stored data.

## Decisions

**1. Merged cut for partly captured seasons.** `cut_mode()` gains a third answer, `merged`, used when some but not all scored weeks have a weekly snapshot.
- A scored week with its own snapshot ranks by it, exactly as in the weekly cut, so players without a game are skipped as before.
- Every other week ranks by a merged start percentage per Sleeper id, built once per league-season:
  1. **Trusted snapshots.** A weekly snapshot of a scored week counts for a player only if he played that week ("played" is the same `stats.played()` test the consensus lineup uses). A weekly snapshot of a week not yet scored always counts.
  2. **The figure.** A player's figure is the highest `started` across his trusted snapshots.
  3. **The ownership fallback.** A player who played in no scored captured week, and whose latest stored injury status for the season (`injuries.statuses_for_week` with a week past the last save) is IR, Out, PUP, Sus, NA or DNR, takes the higher of his figure and his `owned`. Ownership comes from the latest weekly snapshot holding him, else `season.json`.
  4. **Ranking.** Rank by the figure, ties by ESPN id.
- The file's `cut` field says `merged`.
- **Why it was revised during apply.** The first version, as proposed, trusted only scored-week snapshots and gave ownership to everyone not seen active. On real data, every player with a bye in week 10 (the only scored captured week) fell back to ownership. Backups, owned far above their start rate, then flooded the replacement zone: 2026 WR 6.5, RB 6.4. Measured alternatives for 2026 redraft:

  | rule | QB | RB | WR | TE | K | DEF |
  |---|---|---|---|---|---|---|
  | single-week season snapshot (old) | 18.0 | 5.0 | 8.2 | 7.5 | 9.0 | 6.9 |
  | scored weeks only, ownership for all not seen active | 17.4 | 6.4 | 6.5 | 6.7 | 8.3 | 6.9 |
  | + unscored week, ownership for all not seen active | 17.4 | 7.7 | 7.1 | 6.7 | 8.3 | 6.9 |
  | **+ unscored week, ownership only if injured (chosen)** | **15.6** | **9.6** | **8.8** | **6.6** | **9.4** | **7.0** |
  | 2021-2025 range | 15-18 | 8-12 | 8-11 | 6-7.5 | 7.4-9.4 | 6-8 |

  The user chose the last rule. Each newly captured week adds evidence, so the merged figure improves through the season.
- The rationale goes in three places:
  - the `player-war` requirement: the in-season season snapshot is the current week; byes and injuries only lower a start %; why the current week is always trusted; why ownership is only for injured players; why past and fully captured seasons are untouched
  - a "Current-season start percentages" subsection of the README's Player WAR section, with the Jacobs and week 11 example and the table above
  - a comment block above the merged-ranking function, pointing to that README subsection
- Alternatives considered:
  - Use `owned` for everyone. Rejected: ownership holds stashed backups and handcuffs, so it ranks them as starters.
  - Keep the yearly cut and accept the bias. Rejected by the user.

**2. Positions built at export time.** A new `src/ffapp/positions.py` builds one season's rankings from stored data, and `export_site` writes:
- `site/data/<league>/positions/<season>.json` for every stored season
- `site/data/<league>/positions/index.json` with the seasons and the current one
- a `positions` entry per league in `site/data/index.json`, beside `war` and `games`

Nothing is stored under `data/`, and the refresh workflow needs no new step: export already runs last. Alternative: a `positions` command writing `data/positions/`. Rejected: the result is a pure function of files the store already keeps, and storing it adds a merge-conflict surface for the daily refresh.

**3. Points per game.**
- Final weeks are regular-season weeks up to the league's `last_scored_leg` that have stat lines.
- Points per game = (sum of actual points over final weeks the player played + sum of projected points over the remaining regular-season weeks whose projection is above 0) / (played weeks + projected weeks).
- A week whose games are in progress is not final, so it uses its stored projection.
- Players with a zero numerator are dropped.
- Scoring uses `resolve_settings` per week, so a league that changed scoring mid-history is scored correctly.
- Names and NFL teams come from the same source the WAR file uses for player names.

**4. Roster and flags.**
- Players are the union of `players`, `taxi` and `reserve`, filtered to positions in the league's roster slots. FLEX positions count once, under their own position.
- The `taxi` flag comes from the taxi list.
- `injured` is true when the player's status in the latest stored injury file of the season in progress is `IR` or `Out`. Past seasons carry no flags.
- Each team entry carries roster id, owner user id, display name and team name, so the page can colour by manager.

**5. Fixed axis per league and position.**
- Over every season's points-per-game values at that position: low = min(0, floor5(1st percentile)), high = ceil5(max(99th percentile, highest replacement level)).
- The same range is written into every season file of the league. A value outside it is drawn at the edge with an arrow.
- Alternative: the full min to max range. Rejected: a one-game outlier would squash the rows. The user accepted trying this first, with a dynamic axis as the fallback.

**6. SVG dot chart in `site/positions.js`.** No Chart.js.
- **Structure:** each chart is a card containing an `<svg>` sized to the card width.
  - A label column holds the team names. On phones it is narrower and the names are truncated with an ellipsis.
  - Rows are 28 px.
  - A top band holds the axis ticks and the "Replacement Level" label.
- **Dots** are circles of radius 7:
  - Fill: `color-mix(in srgb, <team colour> 40%, var(--surface))`.
  - Stroke: the team colour, 2 px, or `stroke-dasharray: 2 2` for taxi players.
  - Injured dots get a red plus (two 1.5 px strokes in `--bad`) drawn over the centre.
- **Top label:** the top player's last name sits above his dot, anchored at the end when near the right edge, so it never leaves the chart.
- **Outliers:** a value beyond the axis sits at the edge with a small chevron.
- **Overlap:** within a row, walk the dots in descending points per game. A dot closer than one dot width to an already placed dot takes the next free lane in the order 0, -1, +1, -2, +2, -3, +3, -4, +4 steps (6 px, or 5.5 px with 5.5 px dots on plots narrower than 300 px). A chart's row height grows to fit its widest lane spread, so offset dots never reach a neighbouring row. Found during apply: dynasty RB and WR rows at 375 px needed the smaller dots, taller rows and a fourth lane. The order is deterministic, so the picture is stable between visits.
- **Popup:**
  - The dots are focusable (`tabindex="0"`, `role="img"`, `aria-label` with name and PPG).
  - One shared popup `div` per chart card is positioned on hover, focus or tap, and clamped inside the card so it can never widen the page.
- **Colours:**
  - The page receives `colorOf(rid)` from `app.js`, as `games.js` does.
  - A past-season team whose owner is a current member uses that member's colour, found by owner user id, because roster ids in a past redraft league can belong to someone else.
  - Former members get the grey tokens.
- **Layout:**
  - The grid mirrors the WAR page: two columns, a lone last chart centred, one column below 760 px.
  - Charts redraw on resize with a debounce.
- **Data swap:** a `reloadPositions()` hook refetches and redraws, keeping the selected season.
- **URL:** the page is in the URL hash as `#<league>/positions`. The season is module state, as on the WAR page.

**7. Swipeable sub-tabs.** CSS on `.subtabs`:
- **Scrolling:** `overflow-x: auto; scroll-snap-type: x mandatory; overscroll-behavior-x: contain; scrollbar-width: none`, with `::-webkit-scrollbar { display: none }` and `scroll-snap-align: start` on the buttons.
- **Edge fade:** a `mask-image` gradient whose side is set by classes `fade-left` and `fade-right`. A small scroll and resize handler in `app.js` toggles them from `scrollLeft`, `clientWidth` and `scrollWidth`.
- **Selected tab:** on load and on a sub-tab change, the selected button is brought into view by setting the menu's `scrollLeft`, not by `scrollIntoView`, so the page never scrolls vertically.
- **Wide screens:** when the tabs fit, the menu has no overflow and no fade, so desktop looks as before.

**8. Layout check.** The registry gains:
- the "positions" sub-tab state
- a "positions season" control (select another season; the regions are the page content)
- a "position dot" control (`.pos-dot`; hover and focus only change the popup region)
- a swipe test: at 375 px, the menu's scrollWidth exceeds its clientWidth, the page does not scroll sideways, a link to `#<league>/war` shows the Player WAR tab inside the visible strip, and scrolling the strip leaves the page's `scrollY` unchanged

The wide-font pass and the coverage test cover the new views ("positions" and "positions-past").

## Risks / Trade-offs

- [Ownership overstates the start rate of a player hurt early] → it is limited to players with an injury status that keeps them out, it only decides consensus-starter membership for weeks he played, and the effect ends once seasons are fully captured. The verify task reports the 2026 levels next to the 2021 to 2025 range before shipping.
- [A player who was hurt early but has since come back has no out status, so he gets no ownership fallback] → he played in a recent captured week, so his own start percentage from that week is used.
- [2026 WAR values change on the live Player WAR tab] → expected and wanted. The Player WAR page note explains the merged cut.
- [The fixed axis can still look empty for a weak season or crowded for a strong one] → accepted for now; a dynamic axis is the stated fallback.
- [Twelve rows of many dots in dynasty RB and WR can crowd on phones] → lane offsets, smaller dots on narrow plots, and rows that grow to fit; a layout test fails if any two dots overlap by more than 2 px at 375 or 1280 px.
- [Mid-season transfers: a player's points per game includes games for another team] → intentional, and stated in the spec. The page rates players, not managers.
- [An `injured` flag from a stale injury file] → the injury file is written by every refresh in season, and past seasons carry no flags.

## Migration Plan

1. Land the WAR cut fix and regenerate the WAR files (`python -m ffapp war`). Check the 2026 levels, then export.
2. Land positions data, the page and the sub-tab menu together. The code-push workflow tests and deploys them, and the next refresh keeps the files current.
3. Rollback: revert the commit and re-run `war` and `export`. The yearly cut returns for 2026 and the Positions files are no longer written. Stale files left in `site/data/<league>/positions/` are harmless, because no page links to them.

## Open Questions

None. The user settled the replacement line, row order, rosters, flags, axis approach and menu behaviour in exploration.
