## MODIFIED Requirements

### Requirement: Key players
In states F1, F2, C and P2, each team SHALL list four key players from the lineup of the view shown: the quarterback, the highest-projected running back, the highest-projected wide receiver, and the highest-projected remaining RB, WR or TE, with projected points; a replacement fill is listed as a free agent. A "Full Lineup" control SHALL show the full lineup, with free-agent fills labelled as replacement level.

#### Scenario: Key four
- **WHEN** a team's model lineup has RBs projected 18 and 11, WRs 16 and 13, and a TE at 9
- **THEN** its key players are the QB, the 18-point RB, the 16-point WR and the 13-point WR

#### Scenario: Full lineup
- **WHEN** the visitor expands a team's lineup
- **THEN** every lineup slot is listed with its player and projected points, and a replacement fill reads as a free agent at replacement level

### Requirement: Finished weeks
For a finished week (PW), and for a game whose starters have all finished (O1 to O3), each card SHALL show the selected view's forecast, a check mark in the winner's win probability cell, and a vertical line on each team's distribution at its actual score in the team's colour. A pre-week forecast used for a week before the log existed SHALL be labelled as such.

#### Scenario: Week 10 look-back
- **WHEN** a visitor selects week 10 after it is final
- **THEN** each card shows the record's probabilities, a check on the winner, and both actual scores as lines on the chart

#### Scenario: Unofficial winner
- **WHEN** every player in a game has finished on Monday night but Sleeper has not scored the week
- **THEN** the card shows a check on the leading team alongside the Unofficial chip

### Requirement: Live cards
During the live week, only a card in state L1 SHALL show the "LIVE" badge and border (a signal icon with neon green arcs and a moving gradient, still for reduced motion). Once either team has a starter whose game has kicked off, both teams SHALL show their points so far as the large number (0.0 if none) with the projected final beneath labelled "forecasted", and how many of their starters have not yet kicked off.

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

#### Scenario: Only the bench is playing
- **WHEN** a card is in L2 because only a bench player is playing
- **THEN** it shows no LIVE badge

### Requirement: Lineup view toggle
Cards in states P2, L1, L2, P1, O1, O2, O3 and PW SHALL offer a "Model | Actual" toggle that switches the card's lineups, key players, means, win probabilities and chart between the two stored views, opening on Actual. Actual scores SHALL be drawn in both views. Cards in F1, F2 and C SHALL show the model view without a toggle. A rebuilt actual view SHALL be labelled as rebuilt.

#### Scenario: Look-back on Actual
- **WHEN** a visitor opens finished week 10
- **THEN** each card shows the lineups the managers started, labelled rebuilt, with the Actual button selected

#### Scenario: Switch to Model
- **WHEN** the visitor clicks "Model" on a card
- **THEN** that card shows the model's lineups, probabilities and chart, and the actual-score lines stay

#### Scenario: Upcoming week
- **WHEN** a visitor opens week 13 before it starts
- **THEN** the cards show the model view and no toggle

#### Scenario: Untouched card in the live week
- **WHEN** some NFL games of the current week have started but no player in a card has kicked off (state C)
- **THEN** that card shows no toggle

### Requirement: Linked full lineups
Where a card shows the "Full Lineup" control, it SHALL open and close both teams' full lineups in that card together.

#### Scenario: Expand one side
- **WHEN** a visitor expands one team's Full Lineup
- **THEN** the opponent's Full Lineup opens too

## ADDED Requirements

### Requirement: Full lineups while games are on
In states L1, L2 and P1, in both views, each team SHALL show its full lineup in place of the key players, with no "Full Lineup" control, so every starter's game clock, final tag and points are visible.

#### Scenario: Playing starter at FLEX
- **WHEN** a team's only playing starter is its FLEX in the 1st quarter
- **THEN** his row and green clock show without expanding anything

### Requirement: Impact-ranked key players
In the Actual view of states O1, O2, O3 and PW, each team's key players SHALL be its four starters with the largest win probability added in either direction, largest first. Ties on the whole percentage shown SHALL be broken by position: QB, RB, WR, TE, DEF, K. The Model view of these states SHALL show the full lineup, since win probability added exists only for the managers' real starters.

#### Scenario: Ranking with a tie
- **WHEN** a team's starters have win probability added of +31%, +23%, −15%, +13% and +13% for a QB and a WR
- **THEN** its key players are the +31%, +23% and −15% starters and then the QB

### Requirement: Card chips
Cards SHALL show these chips in the card header:
- a grey **Bench playing** chip with a dot in L2 and O2;
- a **Bench to play** chip in O1;
- an **Unofficial** chip, explained on hover as not yet scored by Sleeper, in O1, O2 and O3.

PW cards SHALL show none of them.

#### Scenario: Starters done, bench playing
- **WHEN** a card is in O2
- **THEN** its header shows the Unofficial and Bench playing chips, and no LIVE badge
