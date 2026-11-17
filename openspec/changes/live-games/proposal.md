# Proposal

## Why

The Games page and the season odds ignore everything that happens during a week until Sleeper marks it final on Tuesday, so on a Saturday the site still treats Thursday night's 30-point performance as a projection. League members want the forecasts to move with the games, to see who is playing, done or still to come, and to see how much one player's day swung a matchup. They also want to refresh the site themselves instead of waiting for the next scheduled run.

## What Changes

- **Live week in the simulation.** From the first kickoff of a week: a slot whose player has kicked off holds the manager's real starter; a finished player counts his actual points with no noise; a player in progress counts points so far plus his projection times the share of the game left, with noise scaled by the square root of that share; unlocked slots keep the model's best pick from players not yet locked. Applies to both the game forecasts and the season odds.
- **Live odds file.** The as-of file for completed week N freezes at week N+1's first kickoff as the last pre-week forecast; every later run writes a separate live result. The Predictions table shows the live odds while a week is in progress, labelled with how many games are final; the odds history chart keeps its weekly points. The prediction of record and the frozen pre-kickoff log are unchanged.
- **Game clock in the schedule.** The stored NFL schedule adds each game's quarter, clock and score, used for the share of the game left (overtime counts as none left).
- **Live cards.** A "LIVE" badge (signal icon, neon green arcs with a moving gradient, still for reduced-motion visitors), each team's points so far beside its projected final, how many starters are still to play, and per-player status (in progress in green with the game clock, final in bold dark with an F tag, yet to play in grey with the kickoff time).
- **Win probability added.** Every player with an actual score (live or final) gets the change in his team's win probability from his score against his last pre-kickoff projection, everyone else as projected, using the prediction-of-record lineups and the opponent's projected score. Shown wherever such a player appears, green when positive and red when negative, on live and past weeks.
- **Manual refresh.** A "Refresh" button beside "How good are these odds?" calls a small Cloudflare Worker that holds a GitHub token scoped to running this repository's workflows and starts the refresh, refusing within 15 minutes of the last run's start. Under the button: "Updated N min ago" when available, "Available in N min" while held. The button is hidden until the Worker's address is configured, so the site works without it.

## Capabilities

### New Capabilities
- `live-scoring`: how a week in progress is simulated: locks, final and in-progress players, the share of the game left, and noise scaling.
- `win-probability-added`: the per-player win probability added computation for final and in-progress players.
- `manual-refresh`: the refresh relay, its cooldown and the button.

### Modified Capabilities
- `playoff-odds-simulation`: the as-of point and the odds history change: as-of files freeze at the next week's first kickoff and live results go to a separate file.
- `nfl-schedule`: the stored schedule adds quarter, clock and score.
- `games-page`: cards gain live state, player status and win probability added.
- `league-odds-site`: the Predictions table shows live odds during a week; the site stays static, with the refresh relay optional.

## Impact

- Code: `src/ffapp/simulate.py` and `src/ffapp/odds.py` (fixed and partial points per starter, live result), new `src/ffapp/live.py` (locks, game share left, live inputs), `src/ffapp/schedule.py` (clock and score), `src/ffapp/games.py` and `src/ffapp/games_export.py` (live state, WPA), `src/ffapp/export.py` (live odds, last refresh time), `site/index.html`, `site/app.js`, `site/games.js`, `site/styles.css`, new `relay/` (Worker code, tests, setup guide), `config/site.json` or an export setting for the Worker address.
- Data: `data/odds/<league>/<season>/live.json`; schedule files gain clock and score.
- External: a Cloudflare Worker and a fine-grained GitHub token, set up by the user following the guide; until then the button stays hidden.
- Out of scope: in-game injuries and benchings (backlog: test whether Sleeper's projections update in-game), live score push between scheduled runs.
