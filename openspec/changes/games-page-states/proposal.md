# Proposal

## Why

The Games page has no single idea of what state a game card is in. The exporter sets `kind`, `live` and `source` per week; the forecast sets live totals per team; and the page guesses each card's look from which numbers happen to exist. As a result "live" means three different things, some states have no look of their own (a bench player playing, a game that is over but not yet official), and each new feature mixes data and format a little more. The owner and Claude worked through every state a card can be in and decided how each should look; this change writes that down and builds the page around it.

## What Changes

- **A defined state model for game cards.** It has 11 states in five groups:
  - Pre game: F1 future (projected pairing), F2 future (scheduled), C current week (not started).
  - Live: L1 points being scored, L2 no points being scored.
  - Paused: P1 scoring started, P2 no points yet.
  - Games over: O1 starters done with bench to play, O2 starters done with bench playing, O3 all done but unofficial.
  - Past: PW past week.

  The model has 21 real transitions and a separate group of snapshot-only transitions, which happen only because the site refreshes on a schedule. Rules: the managers' real lineups decide; a player with no game (bye, empty slot) counts as finished, while a ruled-out player finishes when his game ends; a cancelled game counts as 0; a week becomes past when Sleeper scores it.
- **States computed once, in the exporter.** Every card carries its state, and the page renders from a table keyed by state instead of inferring it.
- **Decided looks per state:**
  - C has no Model / Actual toggle.
  - L1, L2 and P1 show both teams' full lineups (no key-players block, no Full Lineup button) in both views.
  - Only L1 shows the LIVE badge.
  - L2 and O2 show a grey "Bench playing" chip; O1 shows "Bench to play"; O1 to O3 show "Unofficial".
  - O1, O2, O3 and PW show a winner check. Their key players are the four starters with the largest win probability added (either sign), largest first, ties by position QB, RB, WR, TE, DEF, K on the whole percentage shown. Their Model view shows the full lineup.
  - P2 and every later state keep the toggle.
- **Documentation:** a state document with the diagram, the state and transition tables, the rules, and a gallery screenshot of every state. The screenshots are generated from fixture weeks, so they stay current as the page changes.
- **Tests that walk every state:** state computation (including the edge rules and snapshot skips) and a layout check of each state's card.

## Capabilities

### New Capabilities

- `game-card-states`: the state model for one game card — the states, the transitions (real and snapshot-only), the rules that decide them, and the documentation and gallery that describe them.

### Modified Capabilities

- `games-page`: how each state looks. This covers which states show key players or full lineups, the impact-ranked key players for finished games, the LIVE badge and new chips, the winner check from O1 on, the toggle rules, and the linked Full Lineup control only where it remains.

## Impact

- **Code:**
  - `src/ffapp/games_export.py`: computes each card's state and the impact-ranked key players. It needs each player's NFL game state from the stored schedule, including bench players.
  - `site/games.js`: renders from the state table.
  - `site/styles.css`: the chips and full-lineup layout.
- **New files:**
  - `docs/games-page-states.md` and its images in `docs/images/games-states/`, linked from the README's Games section.
  - A gallery script that renders fixture weeks with the layout harness.
  - Fixture weeks shared by the gallery and the tests.
- **Tests:** new state-computation tests; layout tests per state, registered in `tests/layout/controls.py` where controls change (the Full Lineup control disappears in some states).
- **Site copy:** new chip text gets copy IDs (`python -m ffapp site-copy`).
- **Calculations:** `Calculations.txt` gains the state rules and the key-player ranking.
- **Data:** no new stored data. The exported week files gain a state per card.
