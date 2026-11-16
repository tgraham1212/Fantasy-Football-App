# Proposal

## Why

The odds pages say how a season is likely to end but nothing about who has been good at this over the years. League members want a career skill rating per manager that survives the roster turnover of a redraft league and the slow drift of a dynasty one, and the odds table already carries two empty ELO columns waiting for it. A spike over the six stored seasons showed an Openskill rating of weekly points rank, pulled a third of the way back to 1000 each preseason, separates managers in both leagues without inflating when members leave or join.

## What Changes

- New `ffapp ratings` command that rates every manager in every stored season from regular-season weekly points: one Plackett-Luce (Openskill) free-for-all per week, scores ranked across all teams, ratings keyed by Sleeper user, 1000 start for everyone, preseason reversion toward 1000, and a tapering early-season multiplier so ratings settle quickly after the offseason.
- Weekly z-scores per manager (points against that week's league mean and spread) with a career running mean, plus background variants (season-to-date mean, exponentially weighted) and a fresh-start rating variant, stored for later use by the odds model but not charted.
- Rating files under `data/ratings/<league>.json` written per league, every season, every week; the refresh pipeline gains a `ratings` step after `stats`.
- Export populates the odds table's ELO and 1-week change columns and adds a rating history per manager, including former members, to each league's site file.
- The odds page gets a second line chart under the odds chart: Openskill rating or career z-score over every stored week since the league began, with a metric switch and a time-range switch, current members in their existing team colours and former members in distinct greys, and the two ELO columns become sortable.
- New dependency `openskill` (pure Python, no transitive dependencies).
- Config gains an optional `ratings` block (reversion fraction, early-season multipliers, start values) with documented defaults; defaults are chosen from the spike and are not tuned per league.

## Capabilities

### New Capabilities
- `manager-ratings`: how managers are rated across seasons from weekly results: the Openskill model and its parameters, the z-score tracks, reversion and early-season rules, how members, newcomers and vacant rosters are handled, and the stored rating file.

### Modified Capabilities
- `league-odds-site`: the odds table's ELO columns carry values and sort; a rating chart with metric and time-range switches joins the league page; the export carries rating history; the scheduled refresh runs the ratings step; the odds-over-time chart requirement is split so no requirement exceeds the validator's length warning.

## Impact

- Code: new `src/ffapp/ratings.py`; `src/ffapp/cli.py` (command and refresh step); `src/ffapp/config.py` (`ratings` block); `src/ffapp/export.py` (ELO fields, history); `site/index.html`, `site/app.js`, `site/styles.css` (chart, switches, sortable columns, grey tokens); `tools/team_palette.py` (greyscale set for former members); `pyproject.toml` and the workflow's install step for the new dependency.
- Data: `data/ratings/<league>.json` committed by the daily refresh; league site files grow by the rating history (about 70 weeks × up to 17 managers × 2 series per league).
- Specs: `openspec/specs/league-odds-site` gains and modifies requirements; new `openspec/specs/manager-ratings`.
- Out of scope: using ratings inside the playoff simulation. The background variants are stored so a later change can test a manager-skill term through the calibration tool.
