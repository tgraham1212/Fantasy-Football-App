# playoff-odds-simulation Specification

## Purpose

Estimates each team's chances for regular-season and playoff outcomes by simulating the rest of a league's season many times, and keeps a history of those estimates week by week.

## Requirements

### Requirement: As-of point
Each simulation SHALL run as of a given number of completed weeks: the regular-season weeks whose results are final in Sleeper. Results of completed weeks SHALL be taken from stored matchups. Every later week SHALL be simulated.

#### Scenario: Mid-season run
- **WHEN** a simulation runs for the 2026 season with weeks 1-9 complete
- **THEN** the actual results of weeks 1-9 are fixed and weeks 10-14 plus the playoffs are simulated

#### Scenario: Week partly played
- **WHEN** a simulation runs on a Friday after the week-10 Thursday game
- **THEN** week 10 is still treated as fully unplayed

### Requirement: Real schedule
The simulation SHALL use the league's actual matchup pairings for each remaining regular-season week.

#### Scenario: Remaining matchups
- **WHEN** week 12 pairs roster 3 against roster 8 in Sleeper
- **THEN** every simulation run plays roster 3 against roster 8 in week 12

### Requirement: Rosters used
The simulation SHALL keep each team's roster fixed as of the as-of point for all remaining weeks. Players on injured reserve or the taxi squad SHALL NOT be eligible to start.

#### Scenario: Current run
- **WHEN** the simulation runs for the current as-of point
- **THEN** each team's roster is its current Sleeper roster, minus reserve and taxi players

#### Scenario: Backfilled run
- **WHEN** the simulation is re-run as of week 5 of the current season
- **THEN** each team's roster is the roster it used in week 5's matchup

### Requirement: Lineup selection
For each simulated week, the simulation SHALL start, for each team, the legal lineup with the highest total projected points under the league's roster slots. FLEX may hold an RB, WR or TE. Players with 0 projected points (byes, players ruled Out) SHALL only start when no player with positive projected points can fill the slot.

#### Scenario: Flex choice
- **WHEN** a team's third-best RB projects 9.1 and its third-best WR projects 11.4
- **THEN** the WR fills the FLEX slot

#### Scenario: Bye week
- **WHEN** a team's starting TE is on a bye and a bench TE projects 5.0
- **THEN** the bench TE starts at TE

### Requirement: Score noise from past results
A player's simulated score SHALL be the player's projected points plus a random error. Errors SHALL be drawn from stored past differences between projected and actual points for players at the same position with similar projections. Actual points SHALL come from stored matchups.

#### Scenario: Error pool
- **WHEN** a WR projected for 14 points is simulated
- **THEN** the error is drawn from past actual-minus-projected differences for WRs with projections near 14 points

#### Scenario: Few past results
- **WHEN** a position and projection range has fewer past results than the minimum pool size
- **THEN** errors are drawn from that position's results across all projection ranges

### Requirement: Regular-season standings and seeding
Simulated standings SHALL rank teams by wins, with ties counted as half a win, then by total points scored. The top six teams SHALL make the playoffs. Seeds 1 and 2 SHALL get first-round byes.

#### Scenario: Tied records
- **WHEN** two teams both finish 8-6 and one has more points scored
- **THEN** the team with more points scored gets the higher seed

### Requirement: Playoff and losers bracket simulation
The simulation SHALL play out the winners bracket for seeds 1-6 and the losers bracket for the other teams, following each league's Sleeper bracket structure, including whether seeds are re-ordered after round 1. Playoff games SHALL use the same score model as regular-season weeks.

#### Scenario: First round
- **WHEN** simulated seeding is complete
- **THEN** round 1 (week 15) plays seed 3 vs 6 and seed 4 vs 5 while seeds 1 and 2 sit out

#### Scenario: Playoffs in progress
- **WHEN** a simulation runs after week 15 is complete
- **THEN** week-15 bracket results are taken from Sleeper's stored bracket and only later rounds are simulated

### Requirement: Bracket logic matches history
For every completed league-season, the system SHALL check that seeding real final standings with its playoff logic produces the same week-15 pairings as Sleeper's stored winners and losers brackets. Replaying the real game results through its bracket logic SHALL produce the same later-round pairings.

#### Scenario: Historical check passes
- **WHEN** the bracket check runs against the 2025 dynasty season
- **THEN** every pairing produced matches Sleeper's stored 2025 brackets

#### Scenario: Historical check fails
- **WHEN** any produced pairing doesn't match Sleeper's stored bracket
- **THEN** the check fails and reports the league-season and the mismatched pairing

### Requirement: Per-team results
For each team, a simulation SHALL report: average projected wins and losses, and the percentage of runs in which the team made the playoffs, got a first-round bye, reached the final, won the title, landed in the losers bracket, and finished last. Last means the lowest regular-season seed.

#### Scenario: Results add up
- **WHEN** a simulation completes for a 12-team league
- **THEN** across teams, playoff chances sum to 600%, bye chances to 200%, final chances to 200%, title chances to 100%, losers-bracket chances to 600%, and last-place chances to 100%, allowing for rounding

#### Scenario: Clinched team
- **WHEN** a team has clinched a playoff spot under the stored results
- **THEN** its playoff chance is 100%

### Requirement: Simulation count and repeatability
Each simulation SHALL use at least 10,000 runs. Given the same inputs and random seed, it SHALL produce identical results.

#### Scenario: Re-run with same seed
- **WHEN** the simulation is run twice with the same stored data and seed
- **THEN** both runs report identical per-team results

### Requirement: Odds history
The system SHALL save each simulation's per-team results, keyed by league, season and as-of week. Saving a result for a key that already has one SHALL replace it. Results for other as-of weeks SHALL be kept.

#### Scenario: Weekly accumulation
- **WHEN** simulations have run as of weeks 0 through 10 of 2026
- **THEN** eleven sets of results are stored for each league's 2026 season

#### Scenario: Same week re-run
- **WHEN** a second simulation runs as of week 10 after a projection refresh
- **THEN** the as-of-week-10 results are replaced and the other weeks' results are unchanged

### Requirement: Current-season backfill
The system SHALL be able to produce odds-history results for every earlier as-of week of the current season, from week 0 (preseason) up to the current as-of week, using stored data.

#### Scenario: 2026 backfill
- **WHEN** the backfill runs during 2026 week 10
- **THEN** results for as-of weeks 0 through 9 are produced and saved for both leagues
