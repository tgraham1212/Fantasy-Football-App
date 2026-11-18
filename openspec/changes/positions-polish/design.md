# Design

## Context

See proposal.md for motivation. Current state:

- **Positions page (`site/positions.js`).**
  - Each chart computes its own row height from its widest dot-lane spread (at least 28 px). Cards in a CSS grid row stretch to the taller card, so a chart beside a crowded neighbour leaves empty space at the bottom.
  - Labels are one line: the team name, falling back to the display name.
  - The top name is anchored `end` near the right edge, because `.pos-plot` has `overflow: hidden`.
  - The popup shows the name and PPG only.
- **Status lists.** There are three:
  - `injuries.NOT_PLAYING` = {Out, Doubtful, IR, PUP→"Out", Sus→"Out"}. It is display-only, used by `games_export` for the cards' not-playing list.
  - `war.UNAVAILABLE_STATUSES` = {IR, Out, PUP, Sus, NA, DNR}.
  - `positions.INJURED_STATUSES` = {IR, Out}.
  - Saved Sleeper statuses seen in 2026: IR, Out, Questionable, NA, PUP, DNR.
- **Owners.** Code reads owners straight from `rosters.json`'s `owner_id`:
  - `league.owners()` (odds, positions)
  - `war.holders_by_week()`
  - `ratings` (vacant rosters become `vacant:<season>:<rid>`)
  - `export.war_export` names via `store.read_users`

  The only vacant roster stored is dynasty 2023 roster 11, owned by DeekBurg in 2022 and Z28kid86 in 2024 and 2025. DeekBurg is absent from 2023's `users.json`.

## Goals / Non-Goals

**Goals:**
- One place decides who owns a vacant roster, and every reader agrees.
- One place defines the out statuses and their labels.
- Positions page polish with no layout regressions; the layout check covers it.

**Non-Goals:**
- Making the simulation sit players with an out status. That is a separate, known limitation: the model still reads projections.
- Rewriting stored Sleeper files.

## Decisions

**1. Vacant fallback at the store's read layer.** `Store.read_rosters()` and `Store.read_users()` (and so `read_season()`) apply the fallback:
- For a roster whose `owner_id` is empty, look through the league's other stored seasons:
  - first the most recent earlier season where that roster id has an owner;
  - otherwise the earliest later one.
- Fill `owner_id` with that user, and mark the roster `"owner_inherited": "<season>"`.
- `read_users()` appends that user's record from the season it came from, so the display name and `metadata.team_name` resolve, unless the user is already in the list.
- The per-league map of roster ownership across seasons is computed once per `Store` instance and cleared by `write_season()`.
- Raw `rosters.json` and `users.json` stay as fetched.

Because every consumer reads through these methods, they all pick up the inherited owner without changes: odds labels, positions, WAR holders and owner names, games export, and ratings. Ratings' existing vacant path still handles a roster with no owner in any stored season.

Alternative: patch each consumer. Rejected: five call sites would have to agree, and the next feature would forget.

**2. Shared out statuses in `src/ffapp/injuries.py`.**
- `OUT_STATUSES = {"Out": "Out", "Doubtful": "Doubtful", "IR": "IR", "PUP": "PUP", "Sus": "Suspended", "NA": "Not active", "DNR": "Did not report"}`.
- `NOT_PLAYING` is replaced by it. `not_playing()` labels reasons from it, so Games cards now show PUP and Suspended instead of "Out".
- `war.UNAVAILABLE_STATUSES` becomes `frozenset(OUT_STATUSES)`, which adds Doubtful. Its comment block and the README subsection note the shared list.
- `positions` flags a player when his latest status is in the list, and exports `status` as the label (or null) alongside `injured`.

**3. Equal row heights per grid row.**
- `drawCharts()` first computes each chart's geometry (dot placement and its needed row height) without drawing.
- When the grid has two columns (`getComputedStyle(grid).gridTemplateColumns` has two tracks), the charts are paired in order (QB+RB, WR+TE, K+DEF) and each pair uses the larger row height. A lone last chart keeps its own.
- The minimum row height rises from 28 to 38 px for two-line labels.
- On one column, each chart keeps its own height.

**4. Two-line labels.**
- Each `.pos-label` holds `<span class="owner-name">display_name</span><span class="team">team_name</span>`, reusing the site's existing classes.
- Both lines get `white-space: nowrap; overflow: hidden; text-overflow: ellipsis`, and the full text goes in `title`.
- Label rows use the chart's row height through the existing `--pos-row` property, vertically centred.

**5. Centred top name.**
- `.pos-plot` drops `overflow: hidden`. The svg keeps `overflow: visible`.
- After drawing, the name is measured (`getBBox`). Centred on the dot, it is shifted only by the amount it would cross the card's inner edge: the card rect minus 6 px, converted to svg coordinates from the plot's offset.
- The layout test that the top name stays inside its card stays in force.

**6. Popup lines and the gold token.**
- The popup adds `<span class="pos-status">label</span>` in `var(--bad)` and `<span class="pos-taxi">Taxi</span>` in a new `--gold` token, status first.
- `--gold` is about #8a6100 in light mode and about #e3b341 in dark mode, set in all three theme blocks. Both are checked to reach at least 4.5:1 against `--surface` before use.
- The dot carries `data-status` and `data-taxi` for the popup.

**7. Layout check.**
- The registry's "position dot" states focus a taxi player's dot and an injured player's dot, and assert the popup lines.
- New tests:
  - the charts in each desktop grid row have equal row heights;
  - labels show two lines;
  - a WAR, ratings and export run on the real store shows roster 11's 2023 owner as DeekBurg.

## Risks / Trade-offs

- [Ratings change for every dynasty manager from 2023] → expected. The vacant entry is replaced by DeekBurg, so 2023 weekly rankings are unchanged, but his history continues and the vacant entry disappears. Regenerate ratings and export, and report his new rating.
- [Inheriting a later owner when no earlier one exists credits a manager with a season before they joined] → only for a roster vacant from its first stored season. There is none in the data today, and it is the user's stated rule.
- [Reading other seasons' rosters on every `read_rosters`] → cached per `Store` instance. There are at most six seasons per league.
- [Games labels change: PUP and Sus no longer read "Out"] → intended, for one vocabulary across the site.
- [Taller minimum rows (38 px) make every chart taller] → needed for two-line labels. The layout check confirms no overflow.

## Migration Plan

1. Land the store fallback and the shared statuses with tests.
2. Regenerate `ratings`, `war`, `simulate`, `games` and `export`, and check DeekBurg's 2023 and the roster-11 WAR owners.
3. Land the page polish. Code push deploys, and the next refresh keeps the data current.
4. Rollback: revert and regenerate. Raw files were never changed.

## Open Questions

None.
