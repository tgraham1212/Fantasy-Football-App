# Proposal

## Why

Lineup Choices should say how a Manager's own decisions fared against the easy default: starting the
rostered Players with the highest Sleeper Projections. Today it is measured against the simulation's
model lineup, which swaps in imaginary free agents wherever one projects higher (most often kickers,
defences and backup quarterbacks). Those fills make up 58% of the redraft figure and 30% of the dynasty
figure, so it mostly measures streaming, not lineup choices. An empty starting slot is also credited at
the free-agent level instead of 0 (1 to 3 times a season). The League tab's season records now rank these
numbers across every season, so the figures need to be right.

## What Changes

- Lineup Choices compares the Manager's starters with the **default lineup**: the best legal lineup from
  that week's rostered Players at their last Sleeper Projection before kickoff, with no free-agent fills.
  Following the default scores 0. Starting QB B over the default's QB A scores B's points minus A's.
- An empty starting slot scores 0 on either side, and a slot no rostered Player can fill scores 0 in the
  default.
- The live rule stays: only Players whose games have kicked off count on both sides.
- The Games page Model view and the simulation keep the replacement floor; only Lineup Choices changes.
- Stored 2026 Lineup Choices values are recalculated once, and the League records that use them follow
  on the next build.
- The game-card hover and the League tab's two lineup records say the figure is against starting the
  highest Sleeper Projections on the roster.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `game-predictions`: 2.8 Lineup choices measures against the default lineup (roster only, empty slots
  0); 2.8.1 drops its replacement-fill clause; 2.8.2 drops the realised replacement level from past
  seasons.
- `games-page`: 2.1.14 Lineup choices shown explains the figure as points against the default lineup.
- `league-records-page`: adds 4.9.2.1.3.4, the lineup-choices records explained on hover and in their
  pop-ups.

## Impact

- `src/ffapp/views.py`: a default-lineup helper and the Lineup Choices total; past-season rebuild.
- `src/ffapp/games.py`: recalculates stored Lineup Choices once when they predate this change.
- `site/games.js` (GAME-09 hover text), `site/league.js` and `site/index.html` (lineup records
  explanation), `site-copy.txt`.
- `Calculations.txt` sections 11 and 23; `docs/league-records.md`; `docs/simulation.md` mention.
- Tests: `tests/test_views.py`, `tests/layout/test_league_records_page.py`, layout controls if the
  explanation adds a hover target.
- Data: `data/games-derived/` values change on the next build or cold run; no committed records change.
