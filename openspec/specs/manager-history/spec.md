# manager-history Specification

## Purpose

The per-manager figures behind the Managers page (finishes, honours, head to head, records, luck, rivals, best players and player move windows), computed from stored league data and exported for the site.

## Requirements

### Requirement: Manager identity across seasons
A manager SHALL be identified by Sleeper user id across seasons, using the vacant-roster fallback to the last owner, and shown under their latest display name. A manager is current when they hold a roster in the current season and retired otherwise.

#### Scenario: Manager who left
- **WHEN** Hildebrand009 held a dynasty roster in 2022 and none since
- **THEN** Hildebrand009 is listed as retired with seasons 2022–2022

#### Scenario: Renamed account
- **WHEN** the account shown as SpookyCast in 2021 is shown as Jdeguire from 2022
- **THEN** it is one manager, listed as Jdeguire, with seasons from 2021

### Requirement: Finishes and honours
Each completed season's final place SHALL come from the stored winners and losers brackets. Honours SHALL list the years of:
- champion and runner-up;
- regular-season first;
- most points for;
- playoff appearances;
- toilet bowl, in leagues whose losers bracket is a toilet bowl. The toilet bowl champion is the team that "wins" by losing the final, which is last place.

#### Scenario: Toilet bowl champion
- **WHEN** a redraft team loses the toilet bowl final
- **THEN** that season is listed under Toilet bowl and the team's finish is last

#### Scenario: Dynasty
- **WHEN** the league's losers bracket is a consolation bracket
- **THEN** no toilet bowl honour is shown

### Requirement: Head to head
For each opponent, head to head SHALL give regular-season and playoff wins, losses and ties, points for and against, and the most recent result, counting every season both managers played.

#### Scenario: Last meeting
- **WHEN** tg1212 last beat djernberg 114.9 to 98.2 in week 10
- **THEN** the djernberg row shows that result

### Requirement: Records and all-time ranks
Each manager's records SHALL be computed from regular-season and playoff games:
- highest and lowest score;
- biggest win and biggest loss;
- closest loss;
- longest winning and losing streaks;
- most points in a season;
- rivalry-week record.

Each record SHALL be ranked against every manager's equivalent across league history, and ranks 1 to 3 exported.

#### Scenario: Second-best ever
- **WHEN** a manager's biggest win is the league's second biggest ever
- **THEN** the record is exported with rank 2

### Requirement: Luck figures
For each manager the export SHALL give:
- **all-play record:** each week's record against every other team's score that week;
- **wins above all-play pace:** actual wins minus the all-play win share times games;
- **points against:** per game, compared with the league average;
- **points left on bench:** the sum over seasons of Sleeper's potential points minus actual points.

#### Scenario: Bench points
- **WHEN** a team's 2025 potential points are 1,610.46 and its points are 1,497.00
- **THEN** 2025 adds 113.46 to points left on bench

### Requirement: Rivals
Redraft rivals SHALL be read from the league config as pairs of rosters, so a rivalry follows the team when its manager changes, with each season's rivalry week (or none). In leagues without a rivals table the rival SHALL be the nemesis: the opponent with the worst head-to-head record against the manager over at least 4 games, ties broken by the larger points deficit; with no opponent at 4 games the rival is shown as "–".

#### Scenario: Rival follows the team
- **WHEN** roster 8's manager changes between seasons
- **THEN** roster 8's new manager inherits its rival, khar432

#### Scenario: Dynasty nemesis
- **WHEN** a dynasty manager is 1-5 against one opponent and no worse against any other with 4 or more games
- **THEN** that opponent is the rival

### Requirement: Player move windows
A player's time with a team SHALL be read from the weekly matchup rosters.
- **Added window:** from the week he joins the team until the week he leaves.
- **Departed window:** from the week he leaves until the week he is back on the team, or the latest week if he never returns.

Each window SHALL sum the player's WAR over its weeks, whichever roster he was on, if any. A later departure SHALL open a new window. In redraft, windows end with their season; in dynasty they carry across seasons.

#### Scenario: Dropped twice
- **WHEN** a player is dropped in week 3, picked up again in week 7 and dropped again in week 12
- **THEN** there are two departed windows (weeks 3–6 and 12 onward) and one added window (weeks 7–11)

### Requirement: Best players
Best Player All-Time SHALL be the player with the most WAR in weeks on the manager's team across all seasons, with his WAR and seasons on the team. "Most seasons on this team" SHALL count seasons with at least one week on the roster. "The one that got away" SHALL be the player with the most WAR in a single departed window.

#### Scenario: Got away
- **WHEN** a player produced +4.1 WAR elsewhere after the manager dropped him and never returned
- **THEN** he is the one that got away if no departed window is larger

### Requirement: Manager file exported
The export SHALL write one manager file per league containing every manager's identity (name, team names by season, crest source, colour), banners, form, facts, season tiles, roster rows, history, head to head, records with ranks, luck, FAAB used by season, players block and news stories, so the page needs no other data to render.

#### Scenario: File present
- **WHEN** the site is exported
- **THEN** `site/data/<league>/managers.json` exists and lists every current and retired manager
