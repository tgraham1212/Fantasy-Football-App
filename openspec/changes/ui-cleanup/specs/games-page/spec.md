## MODIFIED Requirements

### Requirement: Matchup cards
Each game SHALL be a card in a two-column layout (one column on phones, a lone last card centred), with the two teams stacked. Each team row SHALL show the manager's colour dot as on the Predictions table, the manager name with the team name beneath, a score block and the win probability. For a game not yet started, the score block SHALL show the mean simulated points labelled "forecast". For a finished or live game, it SHALL show the actual (or current) score as the large number and, beneath it in smaller type, the forecast labelled "forecasted". To the right of the rows, a chart SHALL overlay both teams' score distributions, each shaded in its manager colour. Below 600 px the chart SHALL move beneath the team rows so the rows use the card's full width, and the win probability box SHALL be smaller.

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

### Requirement: Live cards
During the live week, each card SHALL show a "LIVE" badge (a signal icon whose arcs are neon green with a moving gradient, held still for visitors who prefer reduced motion), each team's points so far as the large number with its projected final beneath it labelled "forecasted", as on a finished card, and how many of its starters have not yet kicked off.

#### Scenario: Saturday of week 11
- **WHEN** a visitor opens week 11 on Saturday after Thursday's game
- **THEN** every week-11 card shows the LIVE badge, each team's points so far large with its forecasted final beneath, and the count of starters still to play

#### Scenario: Reduced motion
- **WHEN** the visitor's system asks for reduced motion
- **THEN** the badge shows without animation

### Requirement: Lineup choices shown
On finished and live cards, each team SHALL show "Lineup choices: +N" (or minus) beneath the forecasted line of its score block, the points versus the model lineup, explained on hover, green when positive and red when negative, in both views.

#### Scenario: Positive choices
- **WHEN** a team's lineup choices are +7.4
- **THEN** "Lineup choices: +7.4" shows in green beneath its forecasted line, never over the scores, and hovering it explains that this is points versus the model lineup

### Requirement: Player row layout
Each player row SHALL show the slot or position, the name with any live status beside it, the points or projection, the win probability added for scored starters in the actual view directly after the points, and a right-hand column holding the kickoff time for players yet to play; the right-hand column SHALL take no width when a card has nothing to put there. Within each team's list, the points or projections SHALL form one aligned column placed just after the longest name, not at the far edge of the card. On screens narrower than 560 px the two teams' player lists SHALL stack, each under its team name, so names use the card's width, and a replacement fill SHALL read "Free agent".

#### Scenario: Upcoming player
- **WHEN** a player's game is on Sunday at 1:00
- **THEN** "Sun 1:00" shows in the right-hand column, his projection sits in the points column just after the list's longest name, and the projections of the list line up

#### Scenario: Phone
- **WHEN** a visitor opens a game card on a 375 px phone
- **THEN** the first team's lineup shows above the second team's and every name in the lineups shows in full

#### Scenario: Free agent on a phone
- **WHEN** a lineup has a replacement fill on a 375 px phone
- **THEN** the row reads "Free agent" and fits on one line

### Requirement: Not playing
Below each card, each team SHALL list rostered players expected not to play that week (bye, any status on the shared out-status list, or inferred out for weeks without saved statuses), each labelled with the reason using the shared status labels, the reason placed just after the name with slightly more space than between words.

#### Scenario: Injured starter
- **WHEN** a team's receiver is Out for week 11
- **THEN** he is listed under that team as Out

#### Scenario: Physically unable to perform
- **WHEN** a team's running back has a saved status of PUP for week 11
- **THEN** he is listed under that team as PUP
