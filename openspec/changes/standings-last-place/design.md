# Design

## Context

Every final place comes from one function, `bracket_places` in `src/ffapp/managers.py`. The Managers
tab (`final_places`, `honours`), Team News (`news.py`, through `final_places`) and the League tab
(`league_records._Context.places`) all read it. In a consolation league it maps the losers bracket's
placement game p to places 6 + p (winner) and 7 + p (loser). It returns `{}` unless all 12 places are
filled, and `season_complete` uses that as the test for a finished season.

`regular_season_order` already orders rosters by wins, then losses, then points for. `final_places`
falls back to it for seasons whose brackets are not finished. The Forecasts "#1 Pick" column comes from
the simulation's regular-season seed (`seeds == n`), so it already means last in the standings.

**Live Actual view.** In `views.build_views`, a live week's Actual view is a copy of the live Forecast's
games (`source: "live"`). That Forecast's lineups come from `odds.build_inputs`, which calls
`live.live_lineup` with an `open_lineup` that is `lineup_from_projections(..., floor)`. So each open slot
is the model's best pick, or a free-agent fill when nothing on the roster beats the replacement level
(Calculations section 12: "Open slots keep the model's best pick"). That is right for the season
Forecasts, which assume Managers will set their best lineup. It is wrong for a view named Actual. The
Model view's `benched` marks in `games_export.team_out` compare with Sleeper's real starters, and they
are correct: Sleeper's live matchup on 2026-11-26 had Evans, Hockenson and Taylor on tg1212's bench.

## Goals / Non-Goals

**Goals:**
- One change in `bracket_places`, so every page that shows a place agrees.
- A season still counts as finished once its winners bracket has placed everyone in the playoffs.

**Non-Goals:**
- The simulation's consolation bracket and every Forecast stay as they are.
- Toilet-bowl leagues are untouched: the toilet bowl decides places 7 to 12 there.
- No new site text. "Last" and "Last Place" are existing labels.
- The live season Forecasts keep the model's picks for open slots: they forecast the rest of the week,
  and Managers can still change lineups. Only the game card's Actual view changes.
- The pre-kickoff current week has no Actual view (the card shows the Model view alone). That stays.

## Decisions

1. **Places outside the playoffs from the standings, in `bracket_places`.** In a league without a toilet
   bowl, take places 1 to `playoff_teams` from the winners bracket. Then give the remaining rosters the
   next places in `regular_season_order`, skipping rosters the winners bracket placed. The losers bracket
   is not read. *Alternative:* change only the League tab's last place. That would leave a 2-12 team
   "9th" on the Managers tab and "Last" on the League tab, so it was rejected.
2. **The completeness test is unchanged in form.** `bracket_places` still returns `{}` until every
   roster has a place. In a consolation league that now means "the winners bracket is placed", because
   the standings always fill the rest. `season_complete` needs no change.
3. **Standings order is wins, then losses, then points for.** This reuses `regular_season_order`, which
   matches Sleeper's standings tiebreak (points for) and the fallback already used.
4. **The rename is wording only.** "Games that matter" becomes "Meaningful Games" in the glossary, the
   spec, Calculations section 23, `docs/league-records.md`, the diagram box, code comments and two test
   names (`test_only_meaningful_games_count`, `test_streaks_count_meaningful_games`). The rule in
   `bracket_kinds` and `season_games` does not change.
5. **The "This season" chip on Player games** is already fixed in `site/league.js` (the phone top 25
   leaves it out today), and `test_player_games_this_season` covers it. The change adds the requirement
   (4.9.2.2.2) the test verifies.

6. **The live Actual view gets its own one-week simulation.** In the live branch of `build_views`,
   build each team's lineup with `live_lineup`. Locked starters are as today. `open_lineup` returns
   the Manager's set starters for the open slots, at their latest Projections, with an empty slot
   scoring 0 and no floor. Then simulate both teams with the live scoring rule from section 12
   (`fixed + share * (projected + bias) + sqrt(share) * (residual - bias)`), the record's noise and one
   week of drift, as `simulate_fixed` does for finished weeks. The rows keep the live fields (status,
   points, clock), so the card shows them as it does today. The Actual view is still labelled `live`.
   *Alternative:* run the live Forecast a second time with set starters. That simulates the whole
   season to change one week, so it was rejected.
7. **WPA and points so far come from the live Forecast.** WPA for a locked starter is measured on the
   live Forecast against the pre-kickoff baseline (section 13), and locked starters are the same in
   both lineups, so `wpa` and `points_so_far` are copied from the Forecast's team. `to_play` is counted
   on the Actual lineup.

## Risks / Trade-offs

- [The card's headline win probability (the Actual view's) now differs from the probability inside the
  live season Forecast, which assumes the best lineup.] → This is intended. The card shows what the
  Managers set, and the Model view shows the best-lineup figure beside it.
- [WPA is still measured on the Forecast's lineup, so a locked starter's WPA can differ slightly from
  the swing in the Actual view's probability.] → Locked starters are identical in both. The gap comes
  only from open slots and is small. Accepted for this change and noted in Calculations section 13.

- [The 2025 dynasty and other past seasons change places 7 to 12 on the Managers tab, and Honours could
  shift.] → Honours use places 1, 2 and the playoff line only, so they do not change in a consolation
  league. The re-inspection of 4.5.3 confirms this against Sleeper's league history.
- [Sleeper's own standings may break a tie differently, for example by head-to-head.] → None of the
  stored seasons has a points-for tie among teams outside the playoffs. The scenario fixes the rule as
  points for.
- [The requirements check links 4.5.2 to its parent 4.5 and child 4.5.3, which are verified by
  inspection.] → Re-inspect both and record the results (the owner's call) before archiving.

## Migration Plan

The change touches derived data only. `python -m ffapp build` (or the next cold run) rewrites
`managers.json`, `records.json` and Team News. No committed record changes. To roll back, revert the
commit and rebuild.
