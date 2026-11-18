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
A league-season SHALL use one of three cuts, and the stored file SHALL say which was used:

- **weekly**: every scored regular-season week has a weekly snapshot. Each week's consensus lineup and replacement players come from that week's snapshot.
- **yearly**: no scored regular-season week has a weekly snapshot. Every week comes from the season snapshot.
- **merged**: some, but not all, scored regular-season weeks have a weekly snapshot. A scored week with a weekly snapshot uses that snapshot. Every other week ranks players by a merged start percentage, and the season snapshot is not used for ranking.

A player's merged start percentage SHALL be the highest percent started he has in any trusted weekly snapshot. A weekly snapshot of a scored week SHALL be trusted for a player only if he played that week. A weekly snapshot of a week not yet scored SHALL always be trusted.

A player SHALL use the higher of that figure and his percent owned only when both of these hold:
- he played in no scored week that has a weekly snapshot;
- his latest stored injury status for the season is IR, Out, PUP, Sus, NA or DNR.

His percent owned SHALL come from the most recent weekly snapshot holding him, or else from the season snapshot. Ties SHALL break by ESPN id, as in every other ranking.

Rationale, kept with the requirement so it can be referenced later:

- **The in-season season snapshot is one week's view.** While a season is in progress, ESPN's public feed reports its season-level start percentage as the current week's figure. The stored season snapshot is therefore one week's view, rewritten on every run. In 2026 it matched the week 11 snapshot for every player.
- **That week's absences distort every week.** Ranking every week by that one view treats a player who is on a bye or hurt in the snapshot week as a bench player all season (Josh Jacobs in week 11: owned 91.5%, started 8.6%). The consensus starter cut moves deeper and the replacement players become genuine backups. The 2026 RB replacement level came out at 5.0 points against 8 to 11 in every completed season.
- **Why the highest figure, and why the current week counts.** Byes and injuries only ever lower a start percentage, never raise it, so the highest trusted figure is the closest to a player's role while active.
  - A scored week is trusted only if he played, which removes byes and injuries that week.
  - The current, unscored week is always trusted. A low figure from a bye or injury there cannot win the maximum, and a player whose team had a bye in the only scored captured week gets his real figure from it.
- **Why ownership only for injured players.** A player hurt for the season before weekly capture began, such as Jacobs if his absence is an injury, shows near 0% started in every snapshot. Percent owned barely moves during an injured-reserve stint, so it is a fair proxy for how often he was started while healthy.
  - Ownership is limited to players with an injury status that keeps them out.
  - For a healthy backup, ownership far exceeds start rate (owned 50%, started 15%). Using it for every player not seen active wrongly lifted week-10-bye backups into the replacement zone: an earlier version of this rule gave 2026 WR 6.5 and RB 6.4.
- **Measured on 2026.** With these rules, 2026 redraft levels moved from QB 18.0, RB 5.0, WR 8.2 to QB 15.6, RB 9.6, WR 8.8, inside the 2021 to 2025 range at every position. Each captured week adds evidence, so the merged figure improves as the season goes on.
- **Which seasons are affected.** Past seasons were captured after they ended, so their season snapshot is the genuine season-long figure and they keep the yearly cut. Once every week of a season has its own snapshot (2027 onward), that season uses the weekly cut and the merged rule no longer applies.

#### Scenario: Past season
- **WHEN** the WAR command runs for 2023
- **THEN** 2023 uses the yearly cut and the file is marked yearly

#### Scenario: Season with every week captured
- **WHEN** every scored week of a season has a weekly snapshot
- **THEN** that season uses the weekly cut and the file is marked weekly

#### Scenario: Partly captured season
- **WHEN** a season has weekly snapshots for weeks 10 and 11 only, and weeks 1 to 10 are scored
- **THEN** week 10 uses its own snapshot, weeks 1 to 9 use the merged start percentage, and the file is marked merged

#### Scenario: Bye in the captured scored week
- **WHEN** a healthy receiver's team had a bye in week 10, the only scored captured week, and the unscored week 11 snapshot shows him 80% started and 95% owned
- **THEN** his merged start percentage is 80, from week 11, and his ownership is not used

#### Scenario: Bye in the current week
- **WHEN** a running back played in week 10 and was 85% started then, and shows 8% started in the unscored week 11 snapshot because of a week 11 bye
- **THEN** his merged start percentage is 85

#### Scenario: Injured before weekly capture began
- **WHEN** a running back played weeks 1 to 5, missed every week from week 6, is on IR, and is 70% owned and 0% started in every weekly snapshot
- **THEN** his merged start percentage is his 70% ownership, and he is ranked by it for weeks 1 to 5

#### Scenario: Healthy backup not seen active
- **WHEN** a healthy receiver did not play in the only scored captured week, shows 15% started in the unscored week, and is 50% owned
- **THEN** his merged start percentage is 15

### Requirement: WAR stored
The system SHALL write, per league and season, a file holding the cut mode, the week it runs through, the season constants and replacement levels per position, and per qualifying player: Sleeper id, name, position, NFL team of their last game, games played, points scored, position stat totals, weekly scores and win probabilities, expected wins and WAR. Re-running on unchanged data SHALL give the same file apart from its timestamp.

#### Scenario: All seasons written
- **WHEN** the WAR command runs
- **THEN** every stored season of every configured league gets a file

#### Scenario: Missing snapshot
- **WHEN** a season has no season snapshot
- **THEN** no file is written for it and the command reports which season is missing
