# Spec Delta

## MODIFIED Requirements

### Requirement: Player row layout
Each player row SHALL show the slot or position, the name with any live status beside it, the points or projection, and a right-hand column holding the win probability added for scored starters in the actual view or the kickoff time for players yet to play; the right-hand column SHALL take no width when a card has nothing to put there. On screens narrower than 560 px the two teams' player lists SHALL stack, each under its team name, so names use the card's width, and a replacement fill SHALL read "Free agent".

#### Scenario: Upcoming player
- **WHEN** a player's game is on Sunday at 1:00
- **THEN** "Sun 1:00" shows in the right-hand column and his name uses the middle width

#### Scenario: Phone
- **WHEN** a visitor opens a game card on a 375 px phone
- **THEN** the first team's lineup shows above the second team's and every name in the lineups shows in full

#### Scenario: Free agent on a phone
- **WHEN** a lineup has a replacement fill on a 375 px phone
- **THEN** the row reads "Free agent" and fits on one line
