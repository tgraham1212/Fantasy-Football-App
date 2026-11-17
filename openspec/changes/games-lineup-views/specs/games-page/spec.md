# Spec Delta

## ADDED Requirements

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
Each player row SHALL show the slot or position, the name with any live status beside it, the points or projection, and a right-hand column holding the win probability added for scored starters in the actual view or the kickoff time for players yet to play; the right-hand column SHALL take no width when a card has nothing to put there.

#### Scenario: Upcoming player
- **WHEN** a player's game is on Sunday at 1:00
- **THEN** "Sun 1:00" shows in the right-hand column and his name uses the middle width

## MODIFIED Requirements

### Requirement: Key players
Below each card, each team SHALL list four key players from the lineup of the view shown: the quarterback, the highest-projected running back, the highest-projected wide receiver, and the highest-projected remaining RB, WR or TE, each with projected points; a slot the model fills at replacement level is listed as a free agent. An expand control labelled "Full Lineup" SHALL show the full lineup of the view shown, with free-agent fills labelled as replacement level.

#### Scenario: Key four
- **WHEN** a team's model lineup has RBs projected 18 and 11, WRs 16 and 13, and a TE at 9
- **THEN** its key players are the QB, the 18-point RB, the 16-point WR and the 13-point WR

#### Scenario: Full lineup
- **WHEN** the visitor expands a team's lineup
- **THEN** every lineup slot is listed with its player and projected points, and a replacement fill reads as a free agent at replacement level

### Requirement: Finished weeks
For a finished week, each card SHALL show the selected view's forecast, a check mark in the winner's win probability cell, and a vertical line on each team's distribution at its actual score in the team's colour. A pre-week forecast used for a week before the log existed SHALL be labelled as such.

#### Scenario: Week 10 look-back
- **WHEN** a visitor selects week 10 after it is final
- **THEN** each card shows the record's probabilities, a check on the winner, and both actual scores as lines on the chart

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
