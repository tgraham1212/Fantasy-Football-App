# Spec Delta

## Purpose

How the simulation treats a week that is under way: who holds each lineup slot once games start, how finished and in-progress players score, and how much uncertainty is left.

## ADDED Requirements

### Requirement: Live week
The live week SHALL be the first week after the as-of point once any of its NFL games has kicked off. Before that, the week SHALL be simulated entirely from projections as before.

#### Scenario: Before Thursday's kickoff
- **WHEN** the refresh runs on Wednesday of week 11
- **THEN** week 11 is simulated entirely from projections and there is no live week

#### Scenario: After Thursday's kickoff
- **WHEN** the refresh runs on Saturday of week 11
- **THEN** week 11 is the live week

### Requirement: Locked slots
In the live week, a starting slot whose player's NFL game has kicked off SHALL hold the player the manager started there, read from Sleeper's lineup for the week. The remaining slots SHALL be filled with the model's best legal lineup from rostered players whose games have not kicked off, with the replacement-level floor as before. A player whose game has kicked off while on the bench SHALL NOT be used.

#### Scenario: Thursday starter locked
- **WHEN** a manager started a Thursday receiver at FLEX
- **THEN** that receiver holds FLEX in every later run of the week, whatever the model would pick

#### Scenario: Benched Thursday player
- **WHEN** a Thursday player scored 25 points on the manager's bench
- **THEN** he does not count for the team

#### Scenario: Sunday slots stay open
- **WHEN** a manager's Sunday running back is ruled out on Saturday
- **THEN** the model's lineup for that slot picks from the players not yet locked

### Requirement: Finished and in-progress scoring
A locked player whose game is final SHALL score his actual points under the league's scoring with no noise. A locked player whose game is in progress SHALL score his points so far plus his projection times the share of his game left, with noise scaled by the square root of that share. The share left SHALL come from the game's quarter and clock, 60 minutes for a full game; overtime and a game with no clock SHALL count as no time left.

#### Scenario: Final game
- **WHEN** a starter's game is final with 18.4 points
- **THEN** he scores exactly 18.4 in every simulation run

#### Scenario: At half time
- **WHEN** a starter projected for 10 has 11 points at half time
- **THEN** his simulated scores average about 16 with about 71% of a full game's spread

#### Scenario: Overtime
- **WHEN** a starter's game is in overtime
- **THEN** he scores his points so far with no noise

### Requirement: Live results are not stored as history
A simulation that uses live results SHALL NOT replace the stored as-of result for the completed weeks it starts from.

#### Scenario: Saturday run
- **WHEN** a refresh runs on Saturday of week 11
- **THEN** the stored as-of-week-10 result is the one from the last run before week 11's first kickoff
