# Design

## Context

See proposal.md for motivation. Current state:

- A week file (`data/games/<league>/<season>/week_NN.json`) holds `log`, `forecast` (latest simulation's games for the week), `record` (finished weeks: `source` `log` = real starters at frozen projections, or `pre-week` = the as-of-(week-1) forecast with the model's lineup) and, during the live week, `baseline`. Records carry `wpa` per team.
- `record_lineup` builds the real starters at frozen projections; `simulate_fixed` simulates fixed lineups with the model's noise and one week of drift; `last_unlocked` reads a player's frozen projection from the log.
- `lineup_from_projections(projections, scoring, slots, players, floor)` builds the model's best lineup; the floor comes from `weekly_level(...)` over free agents.
- Realised replacement levels per week and position are already stored in `data/replacement/<league>/<season>.json` (`weeks[week][pos].realised`).
- The site renders one lineup per team from `games_export.named(...)` rows; the WPA column is always 3.2em wide; `.refresh` is a column flexbox under the header's `align-items: center`, so the note shifts the button up.

## Goals / Non-Goals

**Goals:**
- Two self-consistent pre-kickoff forecasts per finished game, built from stored data only and stable once written.
- No change to existing records' probabilities for weeks with a log (their actual view is the record as stored).

**Non-Goals:**
- Season totals of lineup choices (later owner stats).
- Re-deciding the live week's model (the Actual view during the week is the live forecast from change B).

## Decisions

**1. Store views beside the record, keep `record` as is.** Each finished week file gains `views: {"model": {...}, "actual": {...}}` per game, keyed by game key, each `{teams: [{roster_id, mean, win_prob, lineup, wpa?}], hist, margin_mean, margin_sd, source}`. For `log` records, `actual` is the record (copied, so the export reads one shape) and `model` is new; for `pre-week` records, `model` is the record and `actual` is new with `source: "rebuilt"`. Views are computed once like the record (missing views are filled on the next run; `--force-records` recomputes both). Alternative: replace the record with the actual view (rejected: the record's meaning is fixed in the main spec and other code reads it).

**2. Model lineup from frozen projections.** For each team: roster = the week's matchup row `players`; each player's projection = `last_unlocked(log)` else his stored projection; candidates built as in `lineup_from_projections` but with those values; the floor is that week's projected replacement level (`weekly_level` over free agents with the week's stored projections and rostered set). Simulated with `simulate_fixed` and the record's seed scheme (`model:` prefix) so it is deterministic.

**3. Rebuilt actual view for pre-log weeks.** `record_lineup` with empty log entries (it falls back to stored projections), simulated with `simulate_fixed` and an `actual:` seed. Labelled `rebuilt` in the export and on the card.

**4. Live week.** `views.actual` is the live forecast game (already has live rows and WPA); `views.model` is the model lineup at frozen projections (decision 2, recomputed each run while the week is live).

**5. Lineup choices.** Per team per game: `sum(points of actual starters) - sum(points of model lineup players)`, where a replacement fill counts the week's realised replacement level for its position (from `data/replacement`, projected level as a fallback when realised is missing). Live week: both sums over players whose games have kicked off, fills only once final. Stored as `lineup_choices` on both views' team entries (same value), rounded to one decimal.

**6. Export.** `games_export` emits per game `views: {model, actual}` (each with teams in the existing row format via `named(...)`), `default_view` (`actual` for final and live weeks, `model` otherwise), and per model-view row `benched: true` when the player is not among the actual starters. WPA rows are emitted only in the actual view. Upcoming weeks keep today's single forecast as `views.model` only.

**7. Site.** `games.js` keeps a per-card view state (default from the export), renders a two-button pill toggle in the card header, and re-renders that card's rows and chart on switch. "Full Lineup" uses one `<details>` per team with a shared toggle listener that mirrors `open` to the sibling. Rows become `pos | name (+live status) | value | aside`, with the aside column `auto` width holding WPA (actual view) or kickoff time; a card with no asides gets a class that collapses the column. The "F" tag renders only when the week is live. `refresh.js` renames the button; the note becomes absolutely positioned under the button so the button participates in the header's centring.

## Risks / Trade-offs

- [Rebuilt actual views use stored projections that may include post-kickoff updates] → labelled "rebuilt"; affects 2026 weeks 1 to 10 only.
- [Larger week files] → one extra lineup and histogram per game, roughly doubling a finished week file (still tens of KB).
- [Model lineup floor uses projected replacement levels, lineup choices the realised ones] → deliberate: the model chooses on projections, choices are judged on what happened.

## Migration Plan

1. Ship; run `python -m ffapp games` once to fill views for every finished week; export.
2. Rollback: the export falls back to `record` when `views` is missing.
