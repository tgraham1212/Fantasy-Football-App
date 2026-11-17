# Proposal

## Why

The simulation already plays every remaining game 10,000 times, but it keeps only season-level chances, so league members can't see what the model thinks of this week's matchups or how a game it called actually went. A Games page puts each matchup in front of them: who the model favours, by how much, which players it is counting on and who is sitting out, and for finished weeks where the real scores landed on the forecast. Weekend news changes forecasts by the hour, so the forecast a past game is judged against has to be the best one available before each player kicked off. A once-a-day refresh can't capture that, so runs need to follow the NFL schedule.

## What Changes

- **Game detail from the simulation.** Every simulated week stores, per game, each team's mean score, a score histogram, the win probability and the model's lineup with projected points. Playoff weeks get a projected bracket (seeded by expected seed, the favourite advancing, the 1 seed at the top, toilet bowl games only), with how often each pairing happens across the simulations; real pairings replace projected ones once Sleeper sets them.
- **Projection log and prediction of record.** Every run appends, per game, each team's model lineup, every rostered player's projection and whether his game has kicked off, plus the win probability. A player's entries stop changing at kickoff. Once a week is final, its prediction of record is simulated from the lineup each manager actually started, each player at his last projection before kickoff. Weeks played before the log existed fall back to the pre-week forecast.
- **NFL schedule feed.** ESPN's public scoreboard gives every game's kickoff time and state, stored per week. It decides when a player locks and when the refresh runs.
- **Game-aware refresh.** The workflow wakes hourly and runs the full refresh about 40 minutes before a kickoff window and after games go final, at most once every three hours; the daily 11:00 UTC run stays.
- **Injury history.** Each run saves every fantasy player's Sleeper injury status for the current week. For weeks without a saved status, a player is inferred out when he was rostered, projected for 0 or not projected, and his NFL team played.
- **Projections keep the game date** Sleeper sends, needed to place players in the schedule.
- **Games page.** A third sub-tab between Predictions and Player WAR: a week dropdown with arrows covering this season's regular-season and playoff weeks, opening on the current week, with matchup cards in the two-column layout. Each card shows both teams (owner colour, name, team name, mean points, win probability on a validated diverging green-grey-red fill, overlaid score distributions in owner colours), four key players per team (QB, top RB, top WR, next best RB/WR/TE) with an expand to the full model lineup, and a not-playing list (bye, Out, Doubtful, IR). Finished weeks show the prediction of record, a check on the winner's probability and each team's actual score as a line on its distribution.

## Capabilities

### New Capabilities
- `game-predictions`: per-game forecasts from the simulation, the projected playoff bracket, the projection log, the lock rule and the prediction of record.
- `nfl-schedule`: the stored NFL schedule and game states from the scoreboard feed.
- `refresh-scheduling`: when the refresh runs: the hourly check, the kickoff and final-game triggers, the three-hour spacing and the daily run.
- `injury-history`: saved weekly injury statuses and the inferred-out rule for earlier weeks.
- `games-page`: the Games page, its week control, cards, key players, not-playing list and finished-week display.

### Modified Capabilities
- `league-odds-site`: league pages gain the Games sub-tab between Predictions and Player WAR; the scheduled refresh follows the game-aware schedule and also refreshes the NFL schedule, injury statuses and game predictions.
- `player-projections`: stored projection records keep the game date.

## Impact

- Code: `src/ffapp/simulate.py` (per-game records, bracket pairing counts), `src/ffapp/odds.py` (games in odds payloads), new `src/ffapp/games.py` (log, lock, record, bracket projection), new `src/ffapp/schedule.py` (scoreboard feed, run gate), `src/ffapp/injuries.py`, `src/ffapp/projections.py` (date), `src/ffapp/cli.py` (`schedule`, `should-run`, `games` commands, refresh order), `src/ffapp/export.py`, `.github/workflows/refresh.yml` (hourly trigger and gate), `site/index.html`, new `site/games.js`, `site/app.js`, `site/styles.css`, `tools/team_palette.py` (diverging ramp).
- Data: `data/nfl/<season>/week_NN.json`, `data/injuries/<season>/week_NN.json`, `data/games/<league>/<season>/week_NN.json` (log and record), larger odds files, `site/data/<league>/games/`; more commits per week from the extra runs.
- External: ESPN's scoreboard once an hour (a single small request when the gate decides not to run).
- Out of scope (change B): feeding actual or in-progress results into the simulation mid-week, live score state on cards, season odds that use a partial week. Past seasons' games, which can be added later from the calibration replays.
