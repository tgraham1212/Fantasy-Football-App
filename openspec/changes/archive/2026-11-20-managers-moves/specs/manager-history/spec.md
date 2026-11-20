## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Manager file exported
The export SHALL write one manager file per league containing every manager's identity (name, team names by season, crest source, colour), banners, form, facts, season tiles, roster rows, history, head to head, records with ranks, luck, FAAB by season (spent, budget, biggest bid, overpaid total), moves by season (added, dropped, trades), players block and news stories, so the page needs no other data to render.

#### Scenario: File present
- **WHEN** the site is exported
- **THEN** `site/data/<league>/managers.json` exists and lists every current and retired manager

#### Scenario: Moves exported
- **WHEN** the site is exported after the transactions sync
- **THEN** each manager's entry lists their added, dropped and trade moves for every season they played, with each move's WAR or no-games mark
