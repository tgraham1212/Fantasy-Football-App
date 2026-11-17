# Proposal

## Why

Finished-week cards for weeks 1 to 10 show the model's lineup instead of the one the manager started (tg1212's week 10 shows Xavier Worthy, projected 0.2 more than the Adonai Mitchell who actually started), and managers want to see both: what the model would have played and what they played, each judged by its own pre-kickoff forecast. Showing the two side by side also measures lineup decisions, a first piece of owner skill. Several small layout issues came up on the deployed page at the same time.

## What Changes

- **Model / Actual toggle** on finished and live game cards. Model: each roster's best lineup at every player's last pre-kickoff projection, with replacement fills. Actual: the lineup each manager started at the same projections. The toggle switches lineups, means, win percentages and the chart together; actual scores are drawn in both. Finished and live weeks open on Actual; upcoming weeks show Model only, without a toggle.
- **Data for both views.** Weeks with a projection log get a model-lineup forecast built from the log's frozen projections and the week's replacement level (the actual view is the existing prediction of record). Weeks 1 to 10 keep the pre-week forecast as their model view and get an actual view rebuilt from the real starters at their stored projections, labelled "rebuilt". The live week's Actual view is the live forecast; its Model view is the model lineup at frozen projections.
- **Lineup choices.** Each team on a finished or live card shows "Lineup choices: ±N pts vs model": the starters' points minus the model lineup's points (replacement fills count the week's realised replacement level), points so far on the live week.
- **WPA and bench tag.** Win probability added shows in the Actual view only; in the Model view, model picks the manager benched carry a "BN" tag.
- **Small fixes.** "Full Lineup" (capital L) opens and closes both teams of a card together; finished weeks drop the "F" tag and keep bold points (the live week keeps "F"); the right-hand column of a player row shows win probability added for scored players and the kickoff time for players yet to play, so names get the middle width; the refresh button is renamed "Refresh Data" and lines up with the other header buttons.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `game-predictions`: finished and live weeks store a model-lineup view and an actual-lineup view; weeks before the log get a rebuilt actual view; lineup choices are computed per team.
- `games-page`: the Model / Actual toggle, lineup choices, the bench tag, linked "Full Lineup", key players and WPA per view, the player row layout and the "F" tag rule.
- `manual-refresh`: the button reads "Refresh Data" and its note does not shift the header.

## Impact

- Code: `src/ffapp/games.py` (model-lineup forecast from frozen projections, rebuilt actual views, lineup choices), `src/ffapp/games_export.py` (both views per game, bench flags), `site/games.js` (toggle, linked expand, row layout), `site/refresh.js`, `site/index.html`, `site/calibration.html`, `site/styles.css`.
- Data: week files under `data/games/` gain the second view; `site/data/<league>/games/week_NN.json` grows by one lineup set and histogram per game.
- Out of scope: season-long owner stats built on lineup choices (a later owner-stats change can sum them).
