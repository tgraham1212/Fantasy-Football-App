## 1. State Model

- [x] 1.1 `src/ffapp/card_states.py`: `card_state()` returning the 11 codes from week kind, projected flag and each team's starter and bench game states
- [x] 1.2 Unit tests for every state, each real transition's before and after, a snapshot skip (C to P1), no-game starters and empty slots counted as finished, an out starter finished only when his game ends, postponed (unfinished) and cancelled (finished) games, and Model picks never changing the state
- [x] 1.3 Document the state rules and the key-player ranking in `Calculations.txt`

## 2. Exporter

- [x] 2.1 `games_export.py`: each rostered player's game state from the stored schedule (starters and bench, real lineups), with no game and empty slots counted as finished (out players finish when their game ends)
- [x] 2.2 Store `state` on every card; keep `kind`, `live` and the team live totals the page still needs
- [x] 2.3 Impact-ranked Actual-view key players for O1 to PW (largest |whole % win probability added|, ties QB, RB, WR, TE, DEF, K); no Model-view key players in those states
- [x] 2.4 Export tests: states on a current-week fixture, ranking with a tie, Model view without key players in finished states

## 3. Page

- [x] 3.1 `games.js`: one `CARD_LOOK` table keyed by state (badge, chips, lineup mode, toggle, check, score mode); remove `cardIsLive()` and the score-block and F-tag guesses
- [x] 3.2 Full-lineup mode for L1, L2, P1 (both views) and the Model view of O1 to PW: no key-players block, no Full Lineup control
- [x] 3.3 No toggle in F1, F2 and C; toggle in P2 and later states
- [x] 3.4 Winner check for O1 to PW; final score block (no to-play line) for O states
- [x] 3.5 Chips (Bench playing with a dot, Bench to play, Unofficial with a hover explanation) styled from existing tokens; copy IDs; run `python -m ffapp site-copy`

## 4. Fixtures, Tests and Gallery

- [x] 4.1 `tests/layout/game_states.py`: a fixture week per state, served with `page.route`
- [x] 4.2 Layout test per state: badge, chips, check, toggle, and key players or full lineup, at the tested widths with the wide-font pass
- [x] 4.3 Scope the layout registry's Full Lineup control to states that keep it; the every-control check runs on the fixture weeks
- [x] 4.4 `tools/games_states_gallery.py`: screenshot every state's fixture card into `docs/images/games-states/`
- [x] 4.5 `docs/games-page-states.md`: diagram (SVG), state, transition and snapshot-only tables, rules, and the gallery
- [x] 4.6 README: a "Card states" note in the Games section linking `docs/games-page-states.md`

## 5. Verify

- [x] 5.1 Python test suite and the full layout check (accessibility and touch, light and dark)
- [x] 5.2 Check real weeks: a past week (PW), this week's cards (C and P1 today), a future week and a projected playoff week, at 360, 768 and 1280 px
