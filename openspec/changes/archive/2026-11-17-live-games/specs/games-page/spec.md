# Spec Delta

## ADDED Requirements

### Requirement: Live cards
During the live week, each card SHALL show a "LIVE" badge (a signal icon whose arcs are neon green with a moving gradient, held still for visitors who prefer reduced motion), each team's points so far beside its projected final, and how many of its starters have not yet kicked off.

#### Scenario: Saturday of week 11
- **WHEN** a visitor opens week 11 on Saturday after Thursday's game
- **THEN** every week-11 card shows the LIVE badge, each team's points so far and projected final, and the count of starters still to play

#### Scenario: Reduced motion
- **WHEN** the visitor's system asks for reduced motion
- **THEN** the badge shows without animation

### Requirement: Player game status
In every lineup list on a live or finished week, each starter SHALL show his game status: in progress in green with a dot and the game clock, final in bold dark text with an "F" tag, not yet started in grey with the kickoff time, each with his points so far when he has any.

#### Scenario: Mixed slate
- **WHEN** a team has a Thursday starter (final), a starter in the 3rd quarter and one playing Sunday night
- **THEN** they show "F", "Q3 4:12" in green and the Sunday night kickoff time in grey

### Requirement: Win probability added shown
Every starter with an actual score, live or final, SHALL show his win probability added beside his points, in green when positive and red when negative, on live weeks and past weeks; starters whose games have not kicked off SHALL show none. The page SHALL note that the values show the size of each swing and do not add up to the team's change.

#### Scenario: Past week
- **WHEN** a visitor opens finished week 9
- **THEN** each starter shows his win probability added, a +22 in green and a -9 in red

#### Scenario: Not kicked off
- **WHEN** a starter's game has not started
- **THEN** no win probability added is shown for him
