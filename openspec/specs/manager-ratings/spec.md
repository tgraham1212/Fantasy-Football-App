# manager-ratings Specification

## Purpose

Rates every manager's skill across the whole life of a league from their weekly points, so members can see who has been consistently good or bad over the years rather than how one season is going.

## Requirements

### Requirement: Weekly free-for-all rating
The system SHALL keep an Openskill-style rating (a mean and an uncertainty) per manager and update it once per regular-season week by ranking every team in the league by points scored that week, highest first. Playoff and consolation weeks SHALL NOT change ratings. A week with no points scored by any team SHALL NOT be rated.

#### Scenario: Blowout and squeaker rank the same
- **WHEN** in one week team A scores 150, team B 120 and team C 119
- **THEN** the week is rated with A first, B second and C third, and the margins play no part

#### Scenario: Playoff week
- **WHEN** week 15 is a playoff week in a league whose regular season ends in week 14
- **THEN** no rating changes for week 15

#### Scenario: Unplayed week
- **WHEN** the current week's games have not been played and every team shows 0 points
- **THEN** that week is not rated and ratings stay at their last value

### Requirement: Rating scale and start
Every manager SHALL start at a rating of 1000 with the full starting uncertainty, in their first stored season and when they join later. The displayed rating SHALL be the rating mean, not a conservative estimate.

#### Scenario: Newcomer
- **WHEN** a manager first appears in a league's third stored season
- **THEN** their rating entering their first week is 1000 and the other managers' ratings are unchanged by their arrival

#### Scenario: Scale
- **WHEN** ratings are read after several seasons
- **THEN** the league's ratings are centred near 1000 and a typical manager lies within a few hundred points of it

### Requirement: Preseason reversion
Entering every season after a manager's first, the system SHALL move their rating mean a configured fraction of the way toward 1000 (default one third) and leave their uncertainty unchanged. The reversion target SHALL be the fixed value 1000, not the league's mean rating.

#### Scenario: One third back
- **WHEN** a manager ends a season at 1300 and the reversion fraction is one third
- **THEN** they enter the next season at 1200

#### Scenario: Below the anchor
- **WHEN** a manager ends a season at 700
- **THEN** they enter the next season at 800

#### Scenario: Fixed anchor
- **WHEN** the league's mean rating has drifted to 1060 by the end of a season
- **THEN** every manager is still pulled toward 1000, not toward 1060

### Requirement: Early-season multiplier
The system SHALL multiply each manager's rating-mean change in the first weeks of every season by a configured, non-increasing schedule of multipliers (default 2, 1.75, 1.5, 1.25 for weeks one to four), leaving the uncertainty update as the model computes it. Later weeks SHALL use a multiplier of 1.

#### Scenario: Week one
- **WHEN** the model's update would raise a manager's mean by 40 in the first rated week of a season
- **THEN** their mean rises by 80

#### Scenario: Week five
- **WHEN** the model's update would raise a manager's mean by 40 in the fifth rated week
- **THEN** their mean rises by 40

#### Scenario: Schedule applies by rated week, not calendar week
- **WHEN** a league's regular season starts in week 2
- **THEN** week 2 is the first rated week and takes the first multiplier

### Requirement: Ratings follow the manager
Ratings SHALL be keyed by the roster owner's Sleeper user ID for that season, not by roster slot, so a manager keeps one rating across roster changes and former members keep their last rating. A roster with no owner on record SHALL be rated as a distinct vacant manager for that season so the week's ranking stays complete, and SHALL be marked as vacant.

#### Scenario: Roster slot changes hands
- **WHEN** roster 4 is owned by one user in 2023 and another in 2024
- **THEN** each user's rating covers only the seasons they owned a roster

#### Scenario: Former member
- **WHEN** a manager last played in 2023
- **THEN** their rating history ends at their last rated week and is still stored

#### Scenario: Vacant roster
- **WHEN** a 2023 roster has no owner on record
- **THEN** its weekly points still rank against the other teams, under a vacant entry for that season marked as not a manager

### Requirement: Weekly z-score and career mean
For every rated week the system SHALL compute each team's z-score: its points minus the mean of all teams' points that week, divided by the sample standard deviation of those points. Each manager SHALL have a career mean z-score: the mean of their weekly z-scores over every rated week they have played, never reset.

#### Scenario: Weekly z
- **WHEN** a team scores 130 in a week whose 12 scores have a mean of 110 and a sample standard deviation of 20
- **THEN** its z-score for the week is 1.0

#### Scenario: Career mean spans seasons
- **WHEN** a manager has z-scores of 1.0 and 0.0 in one season and −0.5 in the next
- **THEN** their career mean z after those three weeks is about 0.17

### Requirement: Background rating variants
The system SHALL also store, per manager and week, three variants for later evaluation: a season-to-date mean z-score that resets each season, an exponentially weighted z-score with a configured weight carried across seasons, and a fresh-start rating that resets every manager to 1000 each preseason with no early-season multiplier. These SHALL NOT be shown on the site.

#### Scenario: Season-to-date z resets
- **WHEN** a manager's first rated week of a new season ends
- **THEN** their season-to-date mean z equals that week's z-score alone

#### Scenario: Fresh-start rating
- **WHEN** a manager ended the previous season rated 1300 under the fresh-start variant
- **THEN** they enter the next season at exactly 1000 under that variant

### Requirement: Ratings command and stored file
A `ratings` command SHALL compute the ratings for every configured league from stored seasons and write one file per league holding, for every manager: their identity, display name, whether they are a current member, and a per-week history of rating mean, uncertainty, z-score, career mean z and the background variants, in season and week order. Running it again on unchanged data SHALL produce the same file.

#### Scenario: Full history written
- **WHEN** the command runs on a league with five stored seasons
- **THEN** the league's rating file holds a history entry for every rated week of all five seasons for every manager who played that week

#### Scenario: Current membership flagged
- **WHEN** a manager owns a roster in the latest stored season
- **THEN** their entry is marked current; a manager whose last season is earlier is marked former

#### Scenario: Deterministic
- **WHEN** the command runs twice on the same stored data
- **THEN** the two rating files are identical apart from the generation time

### Requirement: Rating parameters are configurable with fixed defaults
The reversion fraction, the early-season multiplier schedule, the starting rating and uncertainty, and the weight of the exponentially weighted z-score SHALL be optional config values with documented defaults applied to every league alike. Invalid values SHALL be rejected when the config loads.

#### Scenario: Defaults
- **WHEN** the config has no ratings block
- **THEN** reversion is one third, the multipliers are 2, 1.75, 1.5 and 1.25, the start is 1000 with an uncertainty of one third of that, and the exponential weight is 0.2

#### Scenario: Rejected value
- **WHEN** the config sets the reversion fraction to 1.5
- **THEN** loading the config fails with a message naming the field
