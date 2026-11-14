# Proposal

## Why

The site publishes playoff odds, but nothing checks whether a team shown at 30% actually gets there about 30% of the time. The store already holds every completed season's schedules, lineups, scores and projections (dynasty 2022–2025, redraft 2021–2025: nine league-seasons), and the simulation can already run as of any stored week, so the model can be replayed against history to measure how well calibrated it is before any further tuning (ELO, lineup corrections) builds on it.

## What Changes

- A new `ffapp calibrate` command replays every completed league-season week by week with the production simulation and stores the replay odds in the odds history (`data/odds/<league>/<season>/asof_NN.json`), using residual pools that leave the replayed season out.
- The replay is scored at three levels against what really happened: team scores (is the noise the right width?), head-to-head games (are next-week win chances calibrated?), and season outcomes (are playoff / bye / title / last-place chances calibrated, and better than a naive standings baseline?).
- The lineup bias is measured from stored starters: how many points the best-projected lineup gives up to the lineup each manager actually started.
- Results are written as a machine-readable report plus a Markdown summary under `data/calibration/`, both committed to the repo.
- An optional residual scale factor (`simulation.residual_scale` in `config/leagues.yaml`, default 1.0) widens or narrows the sampled score noise. It is off unless set; `calibrate --residual-scale` lets a candidate value be evaluated without changing the configuration. The report records the scale it was produced with.
- The website gains a calibration page ("How good are these odds?") that shows reliability per outcome, interval coverage, Brier skill against the baseline, the lineup gap, sample sizes and the known caveats. The export copies the report into `site/data/`; when no report exists the page says so instead of failing.
- `calibrate` is not part of the daily `refresh`; it runs on demand (minutes at the default replay run count) and its outputs are committed like any other data.

## Capabilities

### New Capabilities
- `odds-calibration`: replaying completed seasons through the simulation, scoring the predictions against real outcomes at score, game and season level, measuring lineup bias, and producing the calibration report.

### Modified Capabilities
- `playoff-odds-simulation`: "Score noise from past results" gains the optional residual scale factor; "Odds history" explicitly covers past seasons produced by replay, not only the current season.
- `league-odds-site`: a new calibration page requirement, and the export includes the calibration report.
- `sleeper-league-sync`: "Configured leagues" accepts an optional `simulation` section (`residual_scale`) in the configuration file.

## Impact

- New module `src/ffapp/calibrate.py` (replay driver, outcome extraction, metrics, report writers) and `cmd_calibrate` in `src/ffapp/cli.py`.
- `src/ffapp/noise.py`: a scaling wrapper or `scale` field on the residual pools; `src/ffapp/odds.py`: `build_pools`/`run_as_of` pass the configured scale through and record it in the odds payload.
- `src/ffapp/config.py`: `simulation.residual_scale` parsing and validation (positive number, default 1.0).
- `src/ffapp/export.py`: copies `data/calibration/report.json` to `site/data/calibration.json` when present.
- `site/`: new `calibration.html` page sharing `styles.css` and Chart.js, linked from the header; small additions to `styles.css`.
- Data: nine seasons × 17 as-of weeks of replay odds (~1.5 MB of JSON) plus `data/calibration/`. No network access; no change to the daily workflow beyond the export picking up the report.
- Tests: config parsing, residual scaling, outcome extraction from fixture seasons, metric arithmetic on hand-built inputs, an end-to-end replay of the fixture's completed 2025 season at a small run count, and export of the report.
