# Spec Delta

## MODIFIED Requirements

### Requirement: Lineup selection
For each simulated week, the simulation SHALL start, for each team, the legal lineup with the highest total projected points under the league's roster slots. FLEX may hold an RB, WR or TE. Every slot SHALL be worth at least that week's projected replacement level for its position (FLEX: the best of RB, WR and TE), standing in for the free agent a manager would pick up; a replacement fill SHALL draw score noise like a player with that projection and position.

#### Scenario: Flex choice
- **WHEN** a team's third-best RB projects 9.1 and its third-best WR projects 11.4
- **THEN** the WR fills the FLEX slot

#### Scenario: Bye week
- **WHEN** a team's starting TE is on a bye and a bench TE projects 5.0
- **THEN** the bench TE starts at TE

#### Scenario: Hole filled at replacement level
- **WHEN** a team has no TE with a positive projection in week 12 and the week-12 TE replacement level is 6.8
- **THEN** the team's TE slot is worth 6.8 projected points that week

#### Scenario: Weak starter floored
- **WHEN** a team's best available RB2 projects 3.1 and the RB replacement level is 7.5
- **THEN** the RB2 slot is worth 7.5 projected points

#### Scenario: Strong starter unaffected
- **WHEN** a team's starter projects 14.0 and the replacement level is 7.5
- **THEN** the slot is worth 14.0

## ADDED Requirements

### Requirement: Roster drift
For each league the simulation SHALL estimate, from stored completed seasons, how a team's replacement-floored projected strength relative to the league mean reverts toward the mean by number of weeks ahead, and how much extra drift noise accumulates. For each simulated week it SHALL shrink each team's strength by the reversion factor for that horizon and add a drift drawn once per simulation run per team that persists from week to week. The factors SHALL be recorded with every stored result.

#### Scenario: Far weeks are less certain
- **WHEN** the redraft reversion factor is 0.89 at two weeks and 0.73 at twelve weeks
- **THEN** a team 20 points above the league mean is simulated at +17.8 two weeks out and +14.6 twelve weeks out, before drift noise

#### Scenario: Drift persists within a run
- **WHEN** a simulation run draws a positive drift for a team in week 10
- **THEN** that team's week-11 drift in the same run starts from the week-10 value rather than from zero

#### Scenario: Recorded in results
- **WHEN** a simulation result is stored
- **THEN** it records the reversion factors and drift noise by horizon, the seasons they were estimated from, and whether the floor and the drift were on
