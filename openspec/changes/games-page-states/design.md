# Design

## Context

See proposal.md (Why). What exists today:

- **Exporter:** `games_export.py` writes one file per week. Each week has `kind` (final, current, upcoming), `live` and `source`. Each game has views (`model`, `actual`), `default_view`, `projected`, `winner`, and per team `points_so_far` / `to_play` once a starter has kicked off.
- **Lineup rows:** each carries `status` (null, in_progress, final), `points`, `clock`, `kickoff`, `wpa`, `benched` and `replacement`. Only starters carry game status. Bench players appear in the Model view only when the model picks them.
- **Page:** `games.js` infers each card's look from these fields. Examples: `cardIsLive()`, the team row checking `points_so_far` before `actual`, `statusTag` checking `week.live`, and `hasAside` scanning every row.
- **Schedule:** `schedule.py` stores each NFL game's state as ESPN reports it: pre, in progress or post, mapped to scheduled, in_progress or final, with kickoff, quarter and clock.
- **Refresh:** the refresh runs the sync, forecast and export together, so the exporter sees the schedule as of that run.

The agreed state model is in the `game-card-states` spec and was explored with the owner on a diagram page; this design implements it.

## Goals / Non-Goals

**Goals:**
- One state per card, computed once from real lineups, and used for everything the page shows.
- The decided look for every state, rendered from a single table.
- A state document and gallery that can be regenerated, and tests that cover every state.

**Non-Goals:**
- Changing the week note's wording beyond picking its text by week, or the forecast and live-scoring calculations.
- Making the site update between refreshes.
- Themed colours.

## Decisions

1. **A pure state function in a new `src/ffapp/card_states.py`.**
   - **Signature:** `card_state(week_kind, projected, teams)`, where each team gives its starters and bench as player game states: `none`, `scheduled`, `in_progress` or `final`. It returns one of the 11 codes.
   - **Codes:** `projected`, `scheduled`, `not_started`, `scoring`, `bench_only`, `paused`, `paused_no_points`, `starters_done`, `starters_done_bench_playing`, `all_done`, `final`. These are stored as `state` on each card, and the docs map them to F1…PW.
   - **Why separate:** keeping it free of I/O lets the tests feed it every combination, including snapshot skips, without building a week.
2. **Player game state from the stored schedule, starters and bench alike.**
   - **Lookup:** the exporter finds each rostered player's NFL team (the projection record, else the ESPN crosswalk, as `live.py` does) and that game's state in the stored schedule.
   - **Counted as finished:** no game (bye) or an empty slot (`"0"`) counts as `final` from the start. A player ruled out is not special: he is finished when his team's game is over, like everyone else, so out statuses play no part in the state.
   - **Postponed and cancelled games:** ESPN reports a postponed game as pre (it stays `scheduled`) and a cancelled one as post (it becomes `final`). That is the agreed rule, with no new data.
   - **Lineups used:** starters and bench come from the week's matchup rosters: the managers' real lineups, never the Model view.
3. **Week kind settles the outer states.**
   - Upcoming weeks are `projected` when the game is a forecast pairing, else `scheduled`.
   - A final week (Sleeper's last scored week has reached it) is `final`.
   - Only the current week runs the live, paused and games-over rules. Before any kickoff, it returns `not_started`.
   - O3 versus PW is therefore exactly "has Sleeper scored the week".
4. **Impact-ranked key players, computed in the exporter.**
   - **Ranking:** for states O1 to PW, the Actual view's key players are the four starters with the largest `abs(round(wpa * 100))`, then by position order QB, RB, WR, TE, DEF, K.
   - **Model view:** in these states it exports no key players, and the page shows the full lineup.
   - **Other states:** they keep today's projection-based `key_players()`.
   - **Why the exporter:** ranking server-side keeps the page from needing ranking rules.
5. **The page renders from a state table.**
   - **The table:** `games.js` gets one `CARD_LOOK` table keyed by state. Its fields are `badge`, `chips`, `lineup` (`key` or `full`), `toggle`, `check` and `score` (`forecast`, `live` or `final`).
   - **What it replaces:** `cardIsLive()`, the `points_so_far` and `actual` guesses, and the week-level checks in `statusTag`.
   - **The F tag:** it keys off the state group (live, paused or games over) rather than `week.live`.
   - **Full lineups:** in `full` mode the expander and the linked-open behaviour are not rendered.
6. **Score block per state.**
   - `forecast` for F1, F2, C and P2.
   - `live` for L1, L2 and P1: points so far, forecasted, and to play.
   - `final` for O1 to PW: the actual or current score, forecasted and lineup choices, with no to-play line.
   - The winner check shows for O1 to PW. For O states it marks the team currently ahead, decided by the same comparison as the final result; a tie shows no check.
7. **Chips are small, copy-ID'd and drawn from existing tokens.**
   - **Bench playing:** grey text with a muted dot.
   - **Bench to play:** plain.
   - **Unofficial:** dashed border, with a hover title explaining that Sleeper hasn't scored the week.
   - **Colours:** existing tokens (`--ink-2`, `--muted`, `--axis`), so no new colours; the colour test covers them as they are.
8. **Fixture weeks as the single source for tests and the gallery.**
   - **Fixtures:** `tests/layout/game_states.py` builds one fixture week per state from a template, then serves it through `page.route` in place of `data/<league>/games/week_NN.json`, as the Managers worst-case test does.
   - **Layout test:** each state's card is checked for badge, chips, check, toggle, and key players or full lineup.
   - **Gallery:** `tools/games_states_gallery.py` screenshots the same fixtures into `docs/images/games-states/`.
   - **Document:** `docs/games-page-states.md` holds the diagram (an SVG committed beside it), the tables, the rules and the gallery, and the README's Games section links to it.

## Risks / Trade-offs

- **[Bench game states add schedule lookups for every rostered player]** → it's the same lookup the live forecast already makes, about 300 players per league per refresh, all from the stored schedule.
- **[A ruled-out starter keeps a card open]** → a card can wait in P1 or L2 for a game its out starter will not play in. That is accepted by the owner: the state settles when that game ends, which is also when his zero is certain.
- **[Older weeks without stored roster states]** → past weeks are always PW from their week kind, so no historical game states are needed.
- **[Removing the expander in some states changes the controls]** → the layout registry's Full Lineup entry is scoped to states that still have it, and the every-control check runs on fixture weeks.
- **[An O-state winner check can flip after a stat correction]** → this is accepted by the owner; the Unofficial chip stays until Sleeper scores the week.
