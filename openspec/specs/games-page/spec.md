# games-page Specification

## Purpose

The Games page of each league: this season's matchups week by week, with the model's forecast for each game, the players it is counting on and who is sitting out, and for finished weeks how the real scores compared with the forecast.

## Requirements

### Requirement: Week control
The Games page SHALL open on the current NFL week and offer a dropdown of every regular-season and playoff week of the current season, with previous and next arrows that step one week and are disabled at the first and last week.

#### Scenario: Default week
- **WHEN** a visitor opens the Games page on a Saturday during week 11
- **THEN** week 11 is shown and selected in the dropdown

#### Scenario: Step back
- **WHEN** the visitor clicks the previous arrow on week 11
- **THEN** week 10 is shown

### Requirement: Matchup cards
Each game SHALL be a card in a two-column layout (one column on phones, a lone last card centred), with the two teams stacked. Each team row SHALL show the owner's colour dot as on the Predictions table, the owner name with the team name beneath, the mean simulated points and the win probability. To the right of the rows, a chart SHALL overlay both teams' score distributions, each shaded in its owner colour.

#### Scenario: Card contents
- **WHEN** week 11's card for two teams is shown
- **THEN** each team row has its colour dot, owner and team name, mean points and win probability, and the chart overlays both distributions in the two owner colours

#### Scenario: Phone width
- **WHEN** the page is shown at 375px
- **THEN** cards stack in one column with no horizontal page scroll

### Requirement: Win probability fill
The win probability cell SHALL be filled on a diverging scale validated with the project's colour tool: neutral grey at 50%, a progressively stronger green toward 100% and red toward 0%, with text that keeps at least 4.5:1 contrast at every step, in both themes.

#### Scenario: Heavy favourite
- **WHEN** a team's win probability is 92%
- **THEN** its cell is a strong green and the other team's 8% cell a strong red

#### Scenario: Toss-up
- **WHEN** both teams are near 50%
- **THEN** both cells are close to the neutral grey

### Requirement: Key players
Below each card, each team SHALL list four key players from the lineup of the view shown: the quarterback, the highest-projected running back, the highest-projected wide receiver, and the highest-projected remaining RB, WR or TE, each with projected points; a slot the model fills at replacement level is listed as a free agent. An expand control labelled "Full Lineup" SHALL show the full lineup of the view shown, with free-agent fills labelled as replacement level.

#### Scenario: Key four
- **WHEN** a team's model lineup has RBs projected 18 and 11, WRs 16 and 13, and a TE at 9
- **THEN** its key players are the QB, the 18-point RB, the 16-point WR and the 13-point WR

#### Scenario: Full lineup
- **WHEN** the visitor expands a team's lineup
- **THEN** every lineup slot is listed with its player and projected points, and a replacement fill reads as a free agent at replacement level

### Requirement: Not playing
Below each card, each team SHALL list rostered players expected not to play that week (bye, Out, Doubtful, IR, or inferred out for weeks without saved statuses), each labelled with the reason.

#### Scenario: Injured starter
- **WHEN** a team's receiver is Out for week 11
- **THEN** he is listed under that team as Out

### Requirement: Finished weeks
For a finished week, each card SHALL show the selected view's forecast, a check mark in the winner's win probability cell, and a vertical line on each team's distribution at its actual score in the team's colour. A pre-week forecast used for a week before the log existed SHALL be labelled as such.

#### Scenario: Week 10 look-back
- **WHEN** a visitor selects week 10 after it is final
- **THEN** each card shows the record's probabilities, a check on the winner, and both actual scores as lines on the chart

### Requirement: Playoff weeks
Playoff weeks SHALL show the projected bracket until Sleeper sets real pairings: games ordered with the 1 seed's side at the top and the 2 seed's side at the bottom, each projected card labelled with how often that pairing happened in the simulations, a bye card for each team with a first-round bye, and toilet bowl games below the winners bracket where the league plays one.

#### Scenario: Projected first round
- **WHEN** a visitor selects week 15 before pairings are set
- **THEN** the 4 v 5 game appears above the 3 v 6 game, bye cards appear for seeds 1 and 2, and each projected game shows how often it occurred

### Requirement: Games data exported
Each league's site data SHALL include, per week of the current season, the cards' data: teams, owners, mean points, win probabilities, histograms, lineups, key players, not-playing lists, the forecast's run time and, for finished weeks, the record, actual scores and winner. The page SHALL load one week at a time. The export SHALL succeed without game data, and the page SHALL then say games are not yet available.

#### Scenario: No games yet
- **WHEN** the export runs on a store without game data
- **THEN** the site builds and the Games page says games are not yet available

### Requirement: Live cards
During the live week, each card SHALL show a "LIVE" badge (a signal icon whose arcs are neon green with a moving gradient, held still for visitors who prefer reduced motion), each team's points so far beside its projected final, and how many of its starters have not yet kicked off.

#### Scenario: Saturday of week 11
- **WHEN** a visitor opens week 11 on Saturday after Thursday's game
- **THEN** every week-11 card shows the LIVE badge, each team's points so far and projected final, and the count of starters still to play

#### Scenario: Reduced motion
- **WHEN** the visitor's system asks for reduced motion
- **THEN** the badge shows without animation

### Requirement: Player game status
In every lineup list on a live or finished week, each starter SHALL show his game status: in progress in green with a dot and the game clock; final in bold dark text, with an "F" tag on the live week only; not yet started in grey with the kickoff time; each with his points so far when he has any.

#### Scenario: Mixed slate
- **WHEN** a team has a Thursday starter (final), a starter in the 3rd quarter and one playing Sunday night
- **THEN** they show "F", "Q3 4:12" in green and the Sunday night kickoff time in grey

#### Scenario: Past week
- **WHEN** a visitor opens finished week 9
- **THEN** every starter's points are bold with no "F" tag

### Requirement: Win probability added shown
Every starter with an actual score, live or final, SHALL show his win probability added beside his points in the actual view, in green when positive and red when negative, on live weeks and past weeks; starters whose games have not kicked off SHALL show none. The page SHALL note that the values show the size of each swing and do not add up to the team's change.

#### Scenario: Past week
- **WHEN** a visitor opens finished week 9
- **THEN** each starter shows his win probability added, a +22 in green and a -9 in red

#### Scenario: Not kicked off
- **WHEN** a starter's game has not started
- **THEN** no win probability added is shown for him

### Requirement: Lineup view toggle
Finished and live game cards SHALL offer a "Model | Actual" toggle that switches the card's lineups, key players, means, win probabilities and chart between the two stored views, opening on Actual. Actual scores SHALL be drawn on the chart in both views. Upcoming weeks SHALL show the model view without a toggle. A rebuilt actual view SHALL be labelled as rebuilt.

#### Scenario: Look-back on Actual
- **WHEN** a visitor opens finished week 10
- **THEN** each card shows the lineups the managers started, labelled rebuilt, with the Actual button selected

#### Scenario: Switch to Model
- **WHEN** the visitor clicks "Model" on a card
- **THEN** that card shows the model's lineups, probabilities and chart, and the actual-score lines stay

#### Scenario: Upcoming week
- **WHEN** a visitor opens week 13 before it starts
- **THEN** the cards show the model view and no toggle

### Requirement: Lineup choices shown
On finished and live cards, each team SHALL show "Lineup choices: +N" (or minus), the points versus the model lineup, explained on hover, green when positive and red when negative, in both views.

#### Scenario: Positive choices
- **WHEN** a team's lineup choices are +7.4
- **THEN** its row shows "Lineup choices: +7.4" in green, and hovering it explains that this is points versus the model lineup

### Requirement: Bench tag
In the model view of a finished or live card, a model pick the manager did not start SHALL carry a "BN" tag, and no win probability added SHALL be shown in that view.

#### Scenario: Benched pick
- **WHEN** the model view lists Xavier Worthy, whom the manager benched
- **THEN** his row shows "BN" and his points, with no win probability added

### Requirement: Linked full lineups
The "Full Lineup" control SHALL open and close both teams' full lineups in a card together.

#### Scenario: Expand one side
- **WHEN** a visitor expands one team's Full Lineup
- **THEN** the opponent's Full Lineup opens too

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
