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
The export SHALL write one manager file per league containing every manager's identity (name, team names by season, crest source, colour), banners, form, facts, season tiles, roster rows, history, head to head, records with ranks, luck, FAAB by season (spent, budget, biggest bid, overpaid total), moves by season (added, dropped, trades), players block and news stories, so the page needs no other data to render.

#### Scenario: File present
- **WHEN** the site is exported
- **THEN** `site/data/<league>/managers.json` exists and lists every current and retired manager

#### Scenario: Moves exported
- **WHEN** the site is exported after the transactions sync
- **THEN** each manager's entry lists their added, dropped and trade moves for every season they played, with each move's WAR or no-games mark

### Requirement: Moves from transactions
Each completed transaction SHALL become moves for the managers involved. Waiver, free-agent and commissioner moves SHALL give one added or dropped row per player, with how it happened (waiver with its bid, free agent, commissioner, or claimed by another manager after a drop) and its week. Drafted players SHALL not appear in moves.

#### Scenario: Add and drop in one move
- **WHEN** a manager picks up Tyler Bass and drops Kenny Coleman in one free-agent move in week 2
- **THEN** Bass is an added row and Coleman a dropped row, both "Free agent" in week 2

### Requirement: Trades in moves
A trade SHALL give one trade entry per side, naming the other manager and the week, and listing the players, picks (season and round) and FAAB each side got and gave. Players moved in a trade SHALL appear only in the trade, never as added or dropped rows.

#### Scenario: Trade with a pick and FAAB
- **WHEN** a manager trades T. Etienne Jr. and $5 FAAB to KingDso for J. Smith-Njigba and KingDso's 2027 2nd-round pick
- **THEN** the trade lists Got: J. Smith-Njigba and "2027 2nd"; Gave: T. Etienne Jr. and "$5 FAAB", and neither player is an added or dropped row

### Requirement: WAR of a move
Each added row and each player got in a trade SHALL carry the WAR of the added window that starts in the move's week. Each dropped row and each player given in a trade SHALL carry the WAR of the departed window that starts in the move's week. An offseason move SHALL count from week 1 of the next season. A player who never played a game inside the window SHALL be marked as having no games instead of a WAR, or as pending when no week after the move has been scored yet. Picks SHALL carry no WAR.

#### Scenario: Picked up and dropped before playing
- **WHEN** a player is added in week 5 and dropped in week 6 before his next game
- **THEN** his added row is marked as having no games

#### Scenario: Picked up this week
- **WHEN** a player is added in week 11 before any week-11 game has been scored
- **THEN** his row is marked pending ("no games yet"), not "no games"

#### Scenario: Dynasty trade
- **WHEN** a dynasty player got in a 2024 trade stays on the team through 2026
- **THEN** the trade's WAR for him covers every week from the trade through 2026

### Requirement: Waiver overpay
A won waiver claim's overpay SHALL be its bid minus the highest failed bid for the same player in the same waiver run. When no other claim was made, the whole bid SHALL count as overpay. When the highest failed bid equals the winning bid, the claim SHALL be marked as tied (won on waiver priority) with no overpay. Failed bids from other waiver runs SHALL not count. Each season SHALL total a manager's overpay, and give their biggest winning bid with the player and week.

#### Scenario: Contested claim
- **WHEN** a manager wins Rico Dowdle for $41 and the next bid in that run was $12
- **THEN** the row shows an overpay of $29

#### Scenario: Uncontested claim
- **WHEN** a manager wins a player for $12 and nobody else bid
- **THEN** the row shows an overpay of $12

#### Scenario: Tie
- **WHEN** two managers bid $22 and the winner had the better waiver priority
- **THEN** the row reads "tied" with no overpay
