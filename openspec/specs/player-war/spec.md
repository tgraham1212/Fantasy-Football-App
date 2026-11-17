# player-war Specification

## Purpose

Defines how a player's season is valued in Wins Above Replacement for a league: consensus lineups and a replacement cut drawn by start percentage, season-wide averages, weekly win probabilities and the stored result per league-season.

## Requirements

### Requirement: Consensus lineup
For each league-season and regular-season week, the system SHALL build a consensus lineup from the start-percentage snapshot: for each lineup position, the most-started players who have a game that week fill that position's starting slots (12 teams times the slots), then the most-started remaining RB, WR and TE fill the flex slots. Players without a game that week SHALL be skipped. Positions SHALL follow the league-season's roster slots.

#### Scenario: Bye week skipped
- **WHEN** the third most-started QB is on bye in week 7
- **THEN** week 7's QB slots are filled from the other most-started QBs with a game

#### Scenario: No kicker slot
- **WHEN** the league's roster slots have no K
- **THEN** no kicker lineup, cut or WAR exists for that league-season

### Requirement: Replacement cut
For each week and position, the replacement players SHALL be the three most-started players, with a game that week, who were not placed in that week's consensus lineup at their position or at flex. The replacement level for the season SHALL be the mean of the replacement players' actual points under the league's scoring across all regular-season weeks.

#### Scenario: Tight end cut
- **WHEN** 12 tight ends fill the TE slots and none of the rest make the flex
- **THEN** the 13th to 15th most-started tight ends with a game are the week's replacement tight ends

#### Scenario: Flex moves the running back cut
- **WHEN** the 25th to 30th most-started running backs are taken by the flex slots
- **THEN** the replacement running backs are the next three past them

### Requirement: Season constants
For each league-season, the slot mean per position SHALL be the mean actual points of the consensus starters at that position across the regular season, pooled across that position's slots; the opponent mean SHALL be the sum of slot means weighted by slot count; and the opponent spread SHALL be the square root of the slot-count-weighted sum of the slot variances. The constants SHALL cover every regular-season week scored so far.

#### Scenario: Completed season
- **WHEN** the WAR command runs for redraft 2024
- **THEN** the constants are computed over weeks 1 to 14

#### Scenario: Season in progress
- **WHEN** the WAR command runs with week 9 the last scored week
- **THEN** the constants are computed over weeks 1 to 9 and the file records week 9 as the week it runs through

### Requirement: Weekly win probability
A player's win probability for a week SHALL be the share of a normal distribution with the opponent mean and spread that lies below a team score equal to the opponent mean plus the player's score for the week minus their position's slot mean. A week in which the player did not play SHALL use the position's replacement level as the score. A week in which the player played and scored zero SHALL use zero.

#### Scenario: Big week
- **WHEN** a tight end scores 31.3 against a TE slot mean of 9.2 with an opponent spread of 20.7
- **THEN** the week's win probability is about 0.86

#### Scenario: Missed week
- **WHEN** a player has no game in week 5 and the position's replacement level is 6.1
- **THEN** week 5 contributes the win probability of a 6.1-point score

#### Scenario: Injured on the first snap
- **WHEN** a player appears in the week's stat lines with zero points
- **THEN** the week counts as played and contributes the win probability of a zero score

### Requirement: Wins above replacement
A player's expected wins SHALL be the sum of their weekly win probabilities over the regular season, and their WAR SHALL be their expected wins minus the expected wins of a player scoring the position's replacement level every week. Both SHALL use the same constants, so a season at exactly replacement level gives a WAR of zero.

#### Scenario: Replacement season
- **WHEN** a player's score equals the replacement level in every week
- **THEN** their WAR is 0

#### Scenario: Above replacement
- **WHEN** a player's weekly win probabilities sum to 7.70 and the replacement baseline is 6.16
- **THEN** their WAR is 1.54

### Requirement: Who gets a WAR
Every player at a lineup position who played at least one regular-season game that season SHALL get a WAR for each league, whether or not any team in the league rostered them. Players with no game played SHALL be excluded.

#### Scenario: Unrostered producer
- **WHEN** a wide receiver on no roster in the league plays 13 games
- **THEN** he has a WAR for that league-season

#### Scenario: Retired but listed
- **WHEN** a player appears in the player database but has no stat line in any week of the season
- **THEN** he has no WAR entry

### Requirement: Yearly and weekly cut
A league-season SHALL use the weekly cut (each week's consensus lineup and replacement players from that week's snapshot) when every scored regular-season week has a weekly snapshot, and the yearly cut (every week from the season snapshot) otherwise. The stored file SHALL say which was used.

#### Scenario: Past season
- **WHEN** the WAR command runs for 2023
- **THEN** 2023 uses the yearly cut and the file is marked yearly

#### Scenario: Season with every week captured
- **WHEN** every scored week of a season has a weekly snapshot
- **THEN** that season uses the weekly cut and the file is marked weekly

#### Scenario: Partly captured season
- **WHEN** a season has weekly snapshots from week 10 onward only
- **THEN** the whole season uses the yearly cut

### Requirement: WAR stored
The system SHALL write, per league and season, a file holding the cut mode, the week it runs through, the season constants and replacement levels per position, and per qualifying player: Sleeper id, name, position, NFL team of their last game, games played, points scored, position stat totals, weekly scores and win probabilities, expected wins and WAR. Re-running on unchanged data SHALL give the same file apart from its timestamp.

#### Scenario: All seasons written
- **WHEN** the WAR command runs
- **THEN** every stored season of every configured league gets a file

#### Scenario: Missing snapshot
- **WHEN** a season has no season snapshot
- **THEN** no file is written for it and the command reports which season is missing
