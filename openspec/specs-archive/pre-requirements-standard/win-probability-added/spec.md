# win-probability-added Specification

## Purpose

Shows how much one player's performance swung his team's chance of winning a game, measured against the forecast made before kickoff.

## Requirements

### Requirement: Win probability added
For each starter with an actual score, the system SHALL compute his win probability added: his team's chance of beating the opponent with his projection replaced by his score, minus the chance with his projection, every other player as projected. Both chances SHALL come from a normal distribution of the margin with the mean and spread of the game's prediction-of-record simulation, the player's own share of the spread removed when his score is known.

#### Scenario: Big game
- **WHEN** a team's pre-kickoff margin is +4 with a spread of 24 and a starter projected for 10 scores 25
- **THEN** his win probability added is about +22 points

#### Scenario: Dud
- **WHEN** the same starter scores 2
- **THEN** his win probability added is negative

### Requirement: Which scores count
A finished player SHALL use his actual points. A player in progress SHALL use his projected final (points so far plus projection times the share left) and keep the remaining spread. A player whose game has not kicked off SHALL have no win probability added.

#### Scenario: Not kicked off
- **WHEN** a starter's game starts Sunday night and it is Sunday afternoon
- **THEN** he has no win probability added

### Requirement: Baseline is the pre-kickoff forecast
Win probability added SHALL use the lineups and projections of the game's prediction of record (each starter at his last projection before kickoff), never live or final results, so a player's number does not depend on how his teammates are doing.

#### Scenario: Teammate scores
- **WHEN** a teammate's touchdown changes the live win probability
- **THEN** this player's win probability added is unchanged
