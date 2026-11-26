# Design

## Context

See proposal.md for why. Today `views.lineup_choices` totals two lineups: the Manager's starters
(`record_lineup`) and the Games page model lineup (`model_lineup` with the replacement floor), scoring a
`None` row (a free-agent fill, or an empty actual slot) at the week's realised replacement level. It runs
in two places:

- `build_views` (games.py `update_games`), once per finished or live week; the result is stored on both
  views in `data/games-derived/` (build cache, not git) and shown on the game cards.
- `season_lineup_choices`, for the League records: it reuses the stored values when a week has game views
  and otherwise rebuilds the week from its stored Projections.

Stored views are computed once and kept (`stored.get("views") is None`), so old values survive a code
change unless something recomputes them.

## Goals / Non-Goals

**Goals:**
- One definition of the default lineup, used by both the game cards and the League records.
- Stored 2026 values replaced automatically on the next cold run or build, without re-simulating.

**Non-Goals:**
- Changing the Model view, the simulation, or the replacement floor.
- Choosing a projection source other than Sleeper's, or the exact pre-kickoff figure for seasons before
  the game log.

## Decisions

1. **Default lineup = the model lineup without the floor.** `model_lineup(..., floor=None)` already picks
   the best legal lineup from the week's rostered Players at their frozen projections (the log's last
   unlocked value, else the stored Projection). A `default_lineup` helper calls it with no floor, so the
   card's Model view and Lineup Choices share the picker but not the fills. *Alternative:* strip the fills
   from the stored model view, rejected because a fill hides which rostered Player the default starts.
2. **Empty slots count 0.** `lineup_choices` drops its `fills` argument; a row with no Player adds 0 on
   either side. With no fills in the default lineup, the only `None` rows are empty actual slots and
   slots no rostered Player can fill.
3. **A basis marker drives the one-time recompute.** The derived part of each week's game file gets
   `"lineup_basis": "roster-default"`. In `update_games`, a week with views but another basis has only its
   `lineup_choices` recomputed (default lineup plus totals: no simulation, no change to the committed
   record). `season_lineup_choices` trusts stored values only when the basis matches, else computes the
   week itself. *Alternative:* `--force-records`, rejected because it re-simulates every week and rewrites
   records.
4. **Live week unchanged in shape.** `counted(pid)` still limits both sides to Players whose games have
   kicked off; since there are no fills, the "fills once final" rule simply goes away.
5. **Explanations.**
   - GAME-09 hover: "Points vs starting the highest Sleeper projections on the roster: what the manager's
     starters scored minus what those players scored".
   - League tab lineup records, as luck does: a hover and focus tip on the two rows and a note at the top
     of their pop-ups, "Your starters' points minus what starting your roster's highest Sleeper
     projections would have scored; following the projections scores 0." (new copy ID LG-48). The tip
     is a new layout-check control, like "luck explanation".

## Risks / Trade-offs

- [Seasons before 2026 use the last Projection stored each week, which can trail late news] → kept as
  today; noted in Calculations.txt section 23.
- [A code deploy exports League records from the cached game views before a cold run recomputes them] →
  decision 3 makes `season_lineup_choices` ignore old-basis values, so the records are right at once; the
  game cards catch up on the next cold run (at most about 15 minutes in season).
- [The greedy picker can misplace a Player eligible at two positions] → unchanged; standard lineups are
  unaffected.
- [Values move noticeably in redraft, where streaming made up 58% of the figure] → expected; the League
  records and cards all follow the same rule.

## Migration Plan

Merge, then the next cold run (or `python -m ffapp build`) recomputes Lineup Choices for every stored
week and exports the records. Rollback: revert the commit; the old code ignores `lineup_basis` and keeps
whatever values are stored, so a full `ffapp build` restores the old figures.
