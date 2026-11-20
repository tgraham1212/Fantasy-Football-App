## MODIFIED Requirements

### Requirement: Matchup cards
Each game SHALL be a card in a two-column layout (one column below 900 px, a lone last card centred), with the two teams stacked. Each team row SHALL show the manager's colour dot as on the Predictions table, the manager name with the team name beneath, a score block and the win probability. For a game not yet started, the score block SHALL show the mean simulated points labelled "forecast". For a finished or live game, it SHALL show the actual (or current) score as the large number and, beneath it in smaller type, the forecast labelled "forecasted". To the right of the rows, a chart SHALL overlay both teams' score distributions, each shaded in its manager colour. Below 600 px the chart SHALL move beneath the team rows so the rows use the card's full width, and the win probability box SHALL be smaller.

#### Scenario: Card contents
- **WHEN** week 11's card for two teams is shown
- **THEN** each team row has its colour dot, manager and team name, its forecast labelled "forecast" and win probability, and the chart overlays both distributions in the two manager colours

#### Scenario: Phone width
- **WHEN** the page is shown at 375px
- **THEN** cards stack in one column with no horizontal page scroll

#### Scenario: Finished game score
- **WHEN** a finished game's team scored 183.5 against a forecast of 113.4
- **THEN** its score block shows 183.5 as the large number and "113.4 forecasted" beneath it

#### Scenario: Large phone
- **WHEN** the page is shown at 440 px
- **THEN** each card shows its team rows across the full card width with the chart beneath them, and no manager name is cut short while the card has room for it

#### Scenario: Tablet width
- **WHEN** the page is shown at 768 px during a live week
- **THEN** cards stack in one column and no lineup's points, win probability added or game clock overlap

### Requirement: Live cards
During the live week, a card SHALL show a "LIVE" badge and border (a signal icon with neon green arcs and a moving gradient, still for reduced motion) only while a starter on either team, not a replacement fill, is in a game in progress. Once either team has a starter whose game has kicked off, both teams SHALL show their points so far as the large number (0.0 if none) with the projected final beneath labelled "forecasted", and how many of their starters have not yet kicked off.

#### Scenario: Saturday of week 11
- **WHEN** a visitor opens week 11 on Saturday after Thursday's game, with no game in progress
- **THEN** no week-11 card shows the LIVE badge, and cards where a starter played Thursday show each team's points so far large with its forecasted final beneath and the count of starters still to play

#### Scenario: Starter in progress
- **WHEN** one team in a game has a starter in the 3rd quarter of Thursday's game
- **THEN** that card shows the LIVE badge and border, and cards with no starter in that game do not

#### Scenario: Only one team has started
- **WHEN** one team has 14.2 points from Thursday and the other has no starter who has played
- **THEN** the other team shows 0.0 large, its forecasted final beneath and its count of starters to play, laid out the same as the first team

#### Scenario: Reduced motion
- **WHEN** the visitor's system asks for reduced motion
- **THEN** the badge shows without animation

### Requirement: Player game status
In every lineup list on a live or finished week, each starter SHALL show his game status: in progress in green with a dot and the game clock in the row's right-hand column; final in bold dark text, with an "F" tag on the live week only; not yet started in grey with the kickoff time in the right-hand column; each with his points so far when he has any.

#### Scenario: Mixed slate
- **WHEN** a team has a Thursday starter (final), a starter in the 3rd quarter and one playing Sunday night
- **THEN** they show "F", "Q3 4:12" in green and the Sunday night kickoff time in grey

#### Scenario: Clock beside a long name on desktop
- **WHEN** a starter with a long name is in the 3rd quarter at 1280 px
- **THEN** "Q3 4:12" shows in the right-hand column and his name keeps its full space

#### Scenario: Past week
- **WHEN** a visitor opens finished week 9
- **THEN** every starter's points are bold with no "F" tag

### Requirement: Player row layout
Each player row SHALL show the slot or position, the name with any final tag, the points or projection, the win probability added for scored starters in the actual view directly after the points, and a right-hand column holding the game clock for a player in progress or the kickoff time for one yet to play; the right-hand column SHALL take no width when a card has nothing to put there. Names SHALL follow the player name standard. Within each team's list, the points or projections SHALL form one aligned column placed just after the longest name, not at the far edge of the card. Below 560 px the two teams' lists SHALL stack, each under its team name, and a replacement fill SHALL read "Free agent".

#### Scenario: Upcoming player
- **WHEN** a player's game is on Sunday at 1:00
- **THEN** "Sun 1:00" shows in the right-hand column, his projection sits in the points column just after the list's longest name, and the projections of the list line up

#### Scenario: Phone
- **WHEN** a visitor opens a game card on a 375 px phone
- **THEN** the first team's lineup shows above the second team's and every name shows in full or, where it does not fit, as first initial and last name, never cut

#### Scenario: Free agent on a phone
- **WHEN** a lineup has a replacement fill on a 375 px phone
- **THEN** the row reads "Free agent" and fits on one line
