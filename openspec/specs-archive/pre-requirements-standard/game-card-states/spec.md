# game-card-states Specification

## Purpose

Defines the states one Games page card can be in, how it moves between them, the rules that decide them, and the documentation that shows each one, so data and format are decided by one named state instead of inferred piece by piece.

## Requirements

### Requirement: Card states
Every game card SHALL be in exactly one of 11 states, computed by the exporter and stored with the card:
- F1 future, projected pairing;
- F2 future, scheduled;
- C current week, not started;
- L1 points being scored;
- L2 no points being scored;
- P1 paused, scoring started;
- P2 paused, no points yet;
- O1 starters done, bench to play;
- O2 starters done, bench playing;
- O3 all done, unofficial;
- PW past week.

#### Scenario: Saturday of the live week
- **WHEN** a starter played Thursday, nobody is playing, and starters still play Sunday
- **THEN** the card's state is P1

#### Scenario: One state per card
- **WHEN** the week is exported
- **THEN** every card carries exactly one of the 11 states

### Requirement: Live and paused definitions
A state SHALL describe both fantasy teams together:
- **L1:** a starter is in a game in progress.
- **L2:** no starter is playing, a bench player is, and a starter still has a game to play.
- **P1:** nobody is playing, some starters have played and some still have a game.
- **P2:** nobody is playing, no starter has played and a bench player has.

#### Scenario: Only a bench player playing
- **WHEN** no starter is playing, a bench player is in the 2nd quarter, and both teams have starters playing Sunday night
- **THEN** the card's state is L2

### Requirement: Games-over and past definitions
Once every starter on both teams is finished, the card SHALL be:
- **O1** while a bench player still has a game and nobody is playing;
- **O2** while a bench player is playing;
- **O3** when every player on both rosters is finished.

It SHALL become PW only when Sleeper has scored the week; until then a finished game stays O1 to O3.

#### Scenario: Monday night is over
- **WHEN** every player's game has ended but Sleeper has not scored the week
- **THEN** the card's state is O3, not PW

### Requirement: Real lineups decide
States SHALL be computed from the managers' real starters and bench, never the Model lineup, so switching between the Model and Actual views never changes a card's state.

#### Scenario: Model pick playing
- **WHEN** a player in the Model lineup but on the manager's bench is the only one playing
- **THEN** the card is in L2, not L1, in both views

### Requirement: Players with no game
A starter or bench player whose NFL team has no game that week (bye), or an empty starter slot, SHALL count as finished from the start of the week. A player ruled out SHALL count as finished only when his team's game is over. A player whose game is postponed SHALL stay unfinished until it is played; one whose game is cancelled SHALL be finished with 0 points.

#### Scenario: Starter on bye
- **WHEN** a team starts a player whose team is on bye and every other starter has finished
- **THEN** the card is in a games-over state

#### Scenario: Starter ruled out
- **WHEN** a team's only unfinished starter is ruled out and his team plays Sunday night
- **THEN** the card stays out of the games-over states until that Sunday night game ends

### Requirement: Transitions
The state documentation SHALL list the 21 real transitions between states, each with its trigger, such as "a starter kicks off" or "Sleeper scores the week". It SHALL list separately the snapshot-only transitions, which happen only because the site sees the world at each refresh. Any state SHALL be allowed to move forward to any later state between two refreshes.

#### Scenario: Thursday skip
- **WHEN** the first refresh after Thursday's kickoff runs after the game has ended
- **THEN** a card goes from C straight to P1, a snapshot-only transition

### Requirement: State documentation
The repository SHALL hold the Games page state document at `docs/games-page-states.md`, linked from the README's Games section. It SHALL contain:
- the state diagram;
- the state, real-transition and snapshot-only-transition tables;
- the rules;
- a gallery image of every state's card.

The gallery images SHALL live in `docs/images/games-states/` and SHALL be generated from fixture weeks by a script that uses the layout harness, so they can be regenerated whenever the page changes.

#### Scenario: Regenerating the gallery
- **WHEN** the gallery script is run after a change to the cards
- **THEN** every state's image is redrawn from its fixture week

### Requirement: Every state checked
Tests SHALL compute the state of fixture cards for every state, including the edge rules and a snapshot skip. The layout check SHALL render a fixture card for every state and confirm its look: badge, chips, winner check, toggle, and key players or full lineup.

#### Scenario: A state's look regresses
- **WHEN** a change makes an L2 card show the LIVE badge
- **THEN** the layout check fails naming L2
