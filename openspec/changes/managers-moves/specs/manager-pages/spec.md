## ADDED Requirements

### Requirement: Moves card
The Moves card SHALL show, for the chosen season or all seasons, a FAAB meter (spent of budget, biggest bid, overpaid total), then Added, Dropped and Trades lists, then the Players block (most seasons on this team, the one that got away). A season picker with arrows SHALL offer each season and "All seasons". A filter SHALL offer All moves, Waivers, Free agents and Trades.

#### Scenario: Season shown
- **WHEN** a manager's 2026 moves are shown
- **THEN** the FAAB meter, the Added, Dropped and Trades lists and the Players block show that season's figures

#### Scenario: Filter
- **WHEN** the visitor chooses Trades
- **THEN** only the Trades list shows

### Requirement: Move rows
Each added or dropped row SHALL show the player's name (following the player name standard), how the move happened and its week on a second line, and a WAR chip in the roster card's colours, or "no games" ("no games yet" while nothing after the move is scored). A won waiver row SHALL show its bid and its overpay as a red "+$29" tag, whose tooltip says whether it was against the next bid or no other bids; a tie SHALL read "tied".

#### Scenario: Overpay tag
- **WHEN** Rico Dowdle was won for $41 against a next bid of $12
- **THEN** his row reads "Waiver · $41 +$29 · week 3" with the tag in red

#### Scenario: Never played
- **WHEN** a dropped player had no game while away from the team
- **THEN** his chip reads "no games"

### Requirement: Moves list headers
Each Moves list header SHALL give its count; Added SHALL also give its FAAB spent and total WAR, and Dropped its WAR elsewhere.

#### Scenario: Added header
- **WHEN** a manager added five players for $75 worth +1.5 WAR in total
- **THEN** the header reads "Added (5)" with "$75 · +1.5 WAR"

### Requirement: Moves text never cut
On the Moves card, a row's second line SHALL wrap rather than be cut, and a player name too wide for its space even when shortened SHALL wrap to a second line, at every tested width and with wide system fonts.

#### Scenario: All seasons on a narrow card
- **WHEN** "Claimed by Gixxersean1 · week 17, 2024" is wider than the desktop card
- **THEN** it wraps onto a second line

#### Scenario: Long name in a trade
- **WHEN** "C. Edwards-Helaire" is still wider than its trade column
- **THEN** the name wraps instead of ending in an ellipsis

### Requirement: Trade blocks
Each trade SHALL be one block naming the other manager (linked to their page) and the week, with Got and Gave sides. Players SHALL show with their WAR chips; picks SHALL show as season and round ("2027 2nd") and FAAB as "$5 FAAB", without WAR.

#### Scenario: Trade with a pick
- **WHEN** a trade sent T. Etienne Jr. for J. Smith-Njigba and a 2027 2nd
- **THEN** the block shows Got: J. Smith-Njigba with his chip and "2027 2nd"; Gave: T. Etienne Jr. with his chip

## REMOVED Requirements

### Requirement: Moves card placeholder
**Reason**: transactions are now synced, so the Moves card shows real lists instead of skeleton rows.
**Migration**: replaced by "Moves card", "Move rows" and "Trade blocks".
