# Proposal

## Why

The calibration report (2026-11-14) shows the weekly score noise is right but season-long odds are over-confident, badly so in the redraft league: teams shown at 3% to make the playoffs made it 12% of the time, teams at 85% made it 69%. The cause is measured, not guessed: the simulation freezes each roster and scores future weeks with it, so bye-week and injury holes count as zeros that no manager would ever start. Under that assumption a redraft team's projected strength two weeks out predicts its true strength with a slope of 0.50; filling holes at replacement level lifts it to 0.89, and the remaining drift is genuine roster churn the sim does not model at all. Replacement level is also a building block the owner wants for later features (value over replacement, trade and waiver analysis), so it should be a first-class, stored concept rather than a private detail of the simulation.

## What Changes

- **Weekly player stats sync.** A new `ffapp stats` command (and a step in `refresh`) stores Sleeper's weekly actual stat lines for every projected player in `data/stats/<season>/week_NN.json`, mirroring the projections store, with `--backfill` for past seasons. Today actual points exist only for rostered players; this covers free agents too.
- **Replacement level as a stored concept.** Per league, season, week and position: the top-N free agents by that week's projection (N defaults to 3, configurable), with their average projection (**projected level**) and their average actual points (**realised level**, when stats exist). Free agents are the projected players not on any roster in that league that week: historically from the stored matchup rosters, for the present from current rosters. A season value per position is the running mean of the realised weekly levels shrunk toward the prior seasons' values with Bayesian shrinkage (`(n·season + k·prior)/(n+k)`, k = 4 weeks, prior = 50/30/20 weighted mean of the last three seasons with the same settings). Written by a new `ffapp replacement` command to `data/replacement/<league>/<season>.json` and refreshed daily.
- **Replacement-level floor in the simulation.** Every simulated lineup slot is worth at least that week's projected replacement level for the slot's position (FLEX takes the best of RB/WR/TE), with noise drawn for the fill like any player. Holes from byes, injuries and thin benches stop scoring zero.
- **Roster drift in the simulation.** Per league, estimated from stored seasons: how much a team's floored strength reverts toward the league mean by weeks ahead, and how much random drift accumulates. Applied in the simulation as a per-week shrink of each team's projected strength plus a per-run random walk, so far-off weeks are less certain than next week. Parameters are recorded in every odds result and written to `data/model/<league>.json`.
- **Calibration covers the new pieces.** Drift parameters are estimated leave-season-out in replays, the report gains a roster-drift diagnostic (slope and drift noise by horizon under the frozen and the floored roster, which is also the evidence for choosing N), and `calibrate` gains `--no-replacement-floor` and `--no-roster-drift` so each piece can be measured alone.
- **Explain it to league members.** The "How good are these odds?" page gains a plain-language section on how the odds are made (projections, noise from past seasons, best lineups with the replacement-level floor, roster drift), each league's current replacement levels by position, how much of a team's edge the model expects to survive weeks ahead, and which model switches the published calibration used. The league export carries the current replacement levels and drift model so those numbers are live.
- Configuration: `simulation.replacement_top_n` (default 3) and `simulation.prior_weeks` (default 4).
- README: new commands, data layout, simulation steps, calibration section.

Out of scope: using the new stats to enlarge the noise pools (a separate model change that should be measured on its own), position-specific N, and changes to the league pages beyond their existing data files.

## Capabilities

### New Capabilities
- `player-stats`: storing weekly actual player stat lines for every season in scope and scoring them under a league's rules.
- `replacement-level`: defining free agents and replacement level per league, season, week and position, the season value with shrinkage, and their storage.

### Modified Capabilities
- `playoff-odds-simulation`: "Lineup selection" gains the replacement-level floor; a new "Roster drift" requirement; results record the model parameters.
- `odds-calibration`: leave-season-out covers drift parameters; new roster-drift diagnostic; evaluation switches for the floor and the drift.
- `sleeper-league-sync`: "Configured leagues" accepts the two new simulation keys.
- `league-odds-site`: "Scheduled refresh" also refreshes stats and replacement levels; "Calibration page" explains the model with live replacement levels and drift factors; a new "Replacement levels exported" requirement.

## Impact

- New modules `src/ffapp/stats.py` (sync, sharing the validate/upsert pattern of `projections.py`), `src/ffapp/replacement.py` (free agents, weekly levels, season values, storage) and `src/ffapp/drift.py` (estimation and parameters); `SleeperClient.stats`; `Store` paths for stats, replacement and model files.
- `src/ffapp/odds.py` and `src/ffapp/simulate.py`: floored lineups, per-team per-week strength adjustment, per-run drift paths; payload fields `model: {replacement_top_n, roster_drift, drift_source_seasons}`.
- `src/ffapp/calibrate.py`: drift estimated per replayed season excluding it; diagnostic section; new flags. `src/ffapp/cli.py`: `stats`, `replacement`, refresh order `sync, projections, stats, replacement, simulate, export`.
- `src/ffapp/config.py`: two new keys under `simulation`.
- `src/ffapp/export.py`: `replacement` and `model` fields in each league file; `site/calibration.html` and `site/calibration.js`: a "How the odds are made" section with live numbers; small style additions.
- Data: about 35 MB of stats for 2021–2026 (one-off), small replacement and model files, daily stats refresh of the current season.
- Tests: a stats fixture for 2025 week 1 (cut down like the projections fixture), free-agent and level arithmetic, shrinkage, floor behaviour in the lineup, drift estimation on synthetic seasons, calibration flags, and a consistency check that our scoring of the stat lines reproduces Sleeper's `players_points`.
- Published odds will change: redraft odds compress toward the middle mid-season; dynasty changes little. The calibration page shows the effect after the next `calibrate` run.
