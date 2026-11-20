# Spec Delta

## MODIFIED Requirements

### Requirement: Weekly win probability
A player's win probability for a week SHALL be the share of a normal distribution with the opponent mean and spread that lies below a team score equal to the opponent mean plus the player's score for the week minus their position's slot mean. Only weeks in which the player was active SHALL count: a bye or a week he was ruled out adds nothing. A week in which the player played and scored zero SHALL use zero.

#### Scenario: Big week
- **WHEN** a tight end scores 31.3 against a TE slot mean of 9.2 with an opponent spread of 20.7
- **THEN** the week's win probability is about 0.86

#### Scenario: Missed week
- **WHEN** a player has no game in week 5
- **THEN** week 5 adds nothing to his expected wins or to his replacement baseline, so it does not change his WAR

#### Scenario: Injured on the first snap
- **WHEN** a player appears in the week's stat lines with zero points
- **THEN** the week counts as played and contributes the win probability of a zero score

### Requirement: Wins above replacement
A player's expected wins SHALL be the sum of their weekly win probabilities over the regular-season weeks in which they were active, and their WAR SHALL be their expected wins minus the expected wins of a player scoring the position's replacement level in those same weeks. Both SHALL use the same constants, so a season at exactly replacement level gives a WAR of zero. These values SHALL equal the earlier definition (missed weeks counted at replacement level), which gave every missed week a contribution of zero.

#### Scenario: Replacement season
- **WHEN** a player's score equals the replacement level in every week
- **THEN** their WAR is 0

#### Scenario: Above replacement
- **WHEN** a player's weekly win probabilities sum to 7.70 and the replacement baseline is 6.16
- **THEN** their WAR is 1.54

#### Scenario: Values unchanged
- **WHEN** WAR is rebuilt with the active-weeks sum
- **THEN** every player's WAR matches the previous build to four decimal places
