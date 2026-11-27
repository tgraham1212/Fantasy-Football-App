# Design

## Context

See proposal.md for the why. What exists today:

- **Played weeks:** every stored season's matchups (scores and opponents) are in `data/`, read through `Store.read_season`.
- **Upcoming weeks:** the season simulation (`simulate.simulate`) already holds every team's simulated score for each unscored week (`SimResult.weekly_scores`, runs x teams), but only per-game summaries leave the run: the Forecast payload and the game files carry each real matchup's means and margin histogram, not pairings of teams that do not meet.
- **League sub-tab:** `site/league.js` renders the Records tab. `#lg-tabs` already exists as a tab strip with one button, and the URL is `#<league>/league/records[/players]`.
- **Shared site pieces:** `site/sorting.js` handles sortable headers, and the Forecast table already pins its Manager column on phones (`.col-owner`, requirement 9.2.1).
- **Feature docs:** `docs/simulation.md` is registered for `simulate.py` and `odds.py`, and `docs/league-records.md` for `site/league.js`.

## Goals / Non-Goals

**Goals:**
- Upcoming-week figures that use exactly the simulated scores behind the Forecasts.
- One export file per league that the page renders without further calculation.
- A tab that fits the existing League sub-tab, URL scheme and layout checks.

**Non-Goals:**
- Playoff weeks, and any schedule other than the real one: no "what if" editor.
- Recomputing Forecasts: the export reads the latest stored Forecast and never runs the simulation.
- Divisions or median-score games. The leagues have neither, so each week is one opponent per team.

## Decisions

**1. Upcoming pairings come from the simulation run.**
`simulate()` computes, for each unscored regular-season week, each team's mean score and the n x n win share from the same `weekly_scores` arrays: `(a > b).mean() + 0.5 * (a == b).mean()`. These are stored in the Forecast payload under `upcoming`, as `{week: {"mean": {rid: x}, "win": {rid: {rid: p}}}}`, rounded to 3 decimals: about 150 numbers per week.
- *Alternative:* rebuild the probabilities at export time from the stored per-game histograms, assuming independent teams (as the explore prototype did). Rejected: it is an approximation, it differs from the Forecasts by up to about 0.1 wins, and it cannot see pairings that do not meet.
- *Alternative:* re-run the simulation inside the export. Rejected: far too slow for every build.

**2. The latest Forecast supplies the upcoming weeks.**
The export takes the league's live result when there is one, else the newest as-of result for the current season. A week is "played" once it is final in the stored matchups. A week in progress is therefore upcoming and uses the live run's scores, which already lock in started players. Past seasons need no Forecast. If the current season has no Forecast yet (preseason, before the first run), it is left out until one exists.

**3. A new module and file.**
`src/ffapp/schedule_strength.py` builds `site/data/<league>/schedule.json`, wired into `export.py` next to `records.json` and listed in the league entry of the site index as `schedule`. Shape:

```
{"generated_at", "seasons": {"2026": {
   "weeks": [1..14], "played_through": 11, "teams": [rid...],
   "ranks": [{"user", "rank", "played", "upcoming", "season",
              "cells": [{"week", "opp", "points", "opp_rank", "upcoming"}]}],
   "swap":  {"order": [user...], "rows": [{"user", "rank", "own", "avg",
              "index", "lo", "hi", "wins": [..N..]}]}}},
 "managers": {user: {name, logo/avatar}}}
```

Rows are keyed by Sleeper user ID, as in `records.json`, so pictures and Manager links reuse `league.js`'s helpers. Means are stored to 0.01, wins to 0.01 (shown to 0.1), and points to 0.1.

**4. The page is its own module.**
`site/schedule.js` renders the tab. `league.js` only adds the second `#lg-tabs` button, routes the URL and hides the Records view switch while Strength of Schedule is open.
- **URL:** `#<league>/league/schedule[/swap][/<season>]`. With no season named, the current season opens.
- **New controls** (each registered in `tests/layout/controls.py`): `#sos-views` (two buttons), `#sos-season` (a `<select>`) and sortable header buttons.

**5. One table per view at every width.**
The phone layout is the same table inside an `overflow-x: auto` card. The Manager cell is `position: sticky`, using the same left offset and shadow as the Forecast table's `.col-owner`, and names don't wrap (`white-space: nowrap`).
- **Weekly Ranks:** below 600 px, only Rank and Season come before the week cells. Played and Upcoming are left out there, as in the phone mockup.
- **Schedule Swap:** the Index column moves next to Rank below 600 px. The table re-renders when a `matchMedia("(max-width: 599px)")` listener fires.
- *Alternative:* Records-style phone lists. Rejected: a heat grid only reads as a grid.

**6. Colours are OKLCH tokens.**
Each bucket has `--sos-*` custom properties in `site/styles.css`: a background and a text tint, with faded and solid shades for Weekly Ranks, plus dark-mode values. They start from the mockup's values (for example, solid dark green `oklch(0.40 0.10 150)` with `oklch(0.95 0.04 150)` text, and faded red `oklch(0.94 0.04 25)` with `oklch(0.47 0.13 25)` text), and are adjusted by lightness only until each pair passes 4.5:1. `tests/test_colour_contrast.py` gains these pairs for both modes.
- **Weekly Ranks buckets:** `floor((rank - 1) * 4 / N)`, so other league sizes split into quarters.
- **Schedule Swap buckets:** the cut-offs are at ±2 wins, and anything within 0.05 of the Manager's own-schedule wins is neutral.

**7. Sorting reuses `site/sorting.js`.**
- **Default orders:** Weekly Ranks by rank (season mean, lowest first) and Schedule Swap by Index, highest first.
- **Schedule columns:** they stay in Schedule Swap order whatever the row sort, so the diagonal stays a diagonal only in the default order; after a re-sort the own-schedule cell is still outlined.

**8. Docs.**
- **New:** `docs/strength-of-schedule.md` and `tools/strength_of_schedule_diagram.py`, registered in `tests/test_feature_docs.py` for `schedule_strength.py` and `site/schedule.js`. Calculations section 24 "Strength of Schedule", and glossary terms Strength of Schedule, Weekly Ranks, Schedule Swap and Schedule Difficulty Index.
- **Affected:** `docs/simulation.md` gains the `upcoming` output and its diagram is redrawn. `docs/league-records.md` notes that `league.js` routes the second tab, and its diagram is redrawn if its boxes change.

## Risks / Trade-offs

- **Forecast payload size** → about 150 numbers per upcoming week and fewer each week. Stored Forecast files grow by a few kB at most.
- **Older stored Forecasts have no `upcoming` block** → the export uses only the latest Forecast, which the next scheduled run writes. Until then, the current season's upcoming weeks are left out and the page shows played weeks only.
- **14 week columns plus summary columns are about 1,220 px wide** → the desktop table scrolls inside its card below that width, with the Manager column pinned at every width so the rows stay readable.
- **Opponent shown by picture only** → the full name is on hover and in the accessible name. The owner chose to try this and revisit it later.
- **Colour alone separates buckets of similar lightness (red, yellow and light green solids)** → the large rank number in every cell carries the same information.

## Migration Plan

No data migration. The first refresh after deploy writes Forecasts with `upcoming`, and `python -m ffapp build` writes `schedule.json`. To roll back, revert the commit; the extra payload key is ignored by older code.
