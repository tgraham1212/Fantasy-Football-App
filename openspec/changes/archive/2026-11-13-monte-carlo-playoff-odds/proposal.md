# Proposal

## Why

Sleeper shows standings, but not each manager's real chance of making the playoffs. In fantasy football, luck and the remaining schedule swing those chances a lot. Our two leagues want 538-style odds that update every week, and a picture of how those odds have moved. The 2026 season is in week 10 now. The sooner this starts, the more of the season's odds history gets saved as it actually happened.

## What Changes

- Pull league history from Sleeper's public API for both leagues: dynasty "Taco Tuesdays" and redraft "Chris Carter's Fall Guys". Each league's chain of past seasons is followed back to its first Sleeper season. Pulled data covers settings per season, users, rosters, matchups and playoff brackets.
- Store scoring, roster and playoff settings separately for each season. Manual override rows, effective from a given week, cover changes Sleeper doesn't record.
- Pull player projections from Sleeper's undocumented projections endpoint for every week of every season in scope, past and future. Store the raw projected stat lines and keep only the latest version per season, week and player. Rows are never deleted after a game is played.
- Score projections with whichever league's settings were in force that week.
- Add a Monte Carlo simulation of the rest of the season plus playoffs for each league. It uses the real schedule, current rosters, a best lineup chosen by projection, and score noise learned from past projected-vs-actual results. For each team it produces: projected wins and losses, and chances of making the playoffs, a first-round bye, reaching the final, winning the title, landing in the losers bracket, and finishing last.
- Save every simulation's results by league, season and as-of week to build an odds history. Fill in the current season's earlier weeks.
- Add a static website for both leagues with a current odds table and a line chart of odds over time.
- Add a scheduled GitHub Actions job that refreshes data, re-runs the simulation, commits the stored data and publishes the site.

## Capabilities

### New Capabilities
- `sleeper-league-sync`: Pulls and stores each configured league's full Sleeper history: league settings per season (with manual overrides), owners, rosters, matchups and playoff brackets.
- `player-projections`: Pulls and stores projected stat lines (latest version per season, week and player), and scores them into points under the settings that applied to a given league and week.
- `playoff-odds-simulation`: Simulates the rest of the regular season and playoffs to produce per-team odds. Saves results by as-of week as an odds history, and checks its playoff logic against past brackets.
- `league-odds-site`: Public static website showing each league's current playoff odds and how they've changed over time, rebuilt on a schedule.

### Modified Capabilities
- None. The project has no existing specs.

## Impact

- **New code:** a Python package (data pulling, scoring, simulation, export) with tests, a static site, and a GitHub Actions workflow. The repo has no application code yet.
- **External dependencies:** Sleeper's public v1 API (documented, no login) and Sleeper's undocumented projections endpoint. The undocumented endpoint can change or disappear without notice. It's used anyway for now; the design keeps it swappable.
- **Repository:** stored data (league history, projections, odds history) is committed to the repo by the scheduled job, so the repo grows a little each week of the season.
- **Hosting:** GitHub Pages (free) for the site. The scheduled job runs on GitHub Actions minutes.
- **Out of scope for this change:** ELO, owner and league stats pages, trade trees and lopsided trades, modeling waiver pickups and trades in the sim, and modeling teammates' scores moving together.
