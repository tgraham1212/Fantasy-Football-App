# game-card-states Specification

## Purpose

The states one Games page card can be in, how it moves between them, the rules that decide them, and the document that shows each one, so a card's data and look follow one named state instead of being inferred piece by piece. It serves need 2, Game Forecasts, through the Games sub-tab (`games-page`); the rules are in `Calculations.txt`, section 22, and `docs/games-page-states.md`.

## Requirements

### Requirement: 2.10 Card states
Every game card SHALL be in exactly one of 11 states, F1, F2, C, L1, L2, P1, P2, O1, O2, O3 and PW, computed by the exporter and stored with the card.

**Rationale:** The glossary and `docs/games-page-states.md` name and define each state.
**Traces to:** 2; 2.1
**Verified by:** Test: `tests/test_card_states.py::test_every_state`; Test: `tests/test_games_export.py::test_export_card_states_and_impact_key_players`

#### Scenario: One state per card
- **WHEN** the week is exported
- **THEN** every card carries exactly one of the 11 states

### Requirement: 2.10.1 Live and paused states
The live and paused states SHALL describe both teams together:
- L1: a starter is in a game in progress;
- L2: no starter is playing, a bench Player is, and a starter still has a game to play;
- P1: nobody is playing, some starters have played and some still have a game;
- P2: nobody is playing, no starter has played, and a bench Player has.

**Traces to:** 2.10
**Verified by:** Test: `tests/test_card_states.py::test_every_state`

#### Scenario: Saturday of the live week
- **WHEN** a starter played Thursday, nobody is playing, and starters still play Sunday
- **THEN** the card's state is P1

#### Scenario: Only a bench Player playing
- **WHEN** no starter is playing, a bench Player is in the 2nd quarter, and both teams have starters playing Sunday night
- **THEN** the card's state is L2

### Requirement: 2.10.2 Games-over states
Once every starter on both teams is finished, the card SHALL be O1 while a bench Player still has a game and nobody is playing, O2 while a bench Player is playing, and O3 when every Player on both rosters is finished.

**Traces to:** 2.10
**Verified by:** Test: `tests/test_card_states.py::test_every_state`

#### Scenario: Monday night is over
- **WHEN** every Player's game has ended
- **THEN** the card's state is O3

### Requirement: 2.10.2.1 Past week once scored
A finished game SHALL become PW only when Sleeper has scored the week, staying in O1 to O3 until then.

**Traces to:** 2.10.2
**Verified by:** Test: `tests/test_card_states.py::test_real_transitions_land_on_the_right_state`

#### Scenario: Not yet scored
- **WHEN** every Player's game has ended but Sleeper has not scored the week
- **THEN** the card's state is O3, not PW

### Requirement: 2.10.3 Real lineups decide
States SHALL be computed from the Managers' real starters and bench, so switching between the Model and Actual views never changes a card's state.

**Traces to:** 2.10; 2.1.13
**Verified by:** Test: `tests/test_card_states.py::test_model_picks_play_no_part`

#### Scenario: Model pick playing
- **WHEN** a Player in the Model lineup but on the Manager's bench is the only one playing
- **THEN** the card is in L2, not L1, in both views

### Requirement: 2.10.4 Players with no game
A starter or bench Player whose NFL team has no game that week, and an empty starter slot, SHALL count as finished from the start of the week.

**Traces to:** 2.10
**Verified by:** Test: `tests/test_card_states.py::test_bye_and_empty_slot_count_as_finished`

#### Scenario: Starter on bye
- **WHEN** a team starts a Player whose team is on bye and every other starter has finished
- **THEN** the card is in a games-over state

### Requirement: 2.10.4.1 Ruled-out Players
A Player ruled out SHALL count as finished only when his team's game is over.

**Traces to:** 2.10.4
**Verified by:** Test: `tests/test_card_states.py::test_ruled_out_starter_finishes_only_when_his_game_ends`

#### Scenario: Starter ruled out
- **WHEN** a team's only unfinished starter is ruled out and his team plays Sunday night
- **THEN** the card stays out of the games-over states until that Sunday night game ends

### Requirement: 2.10.4.2 Postponed games
A Player whose game is postponed SHALL stay unfinished until it is played.

**Traces to:** 2.10.4
**Verified by:** Test: `tests/test_card_states.py::test_postponed_stays_open_and_cancelled_finishes`

#### Scenario: Postponed game
- **WHEN** a starter's game is postponed to Tuesday
- **THEN** he stays unfinished until it is played

### Requirement: 2.10.4.3 Cancelled games
A Player whose game is cancelled SHALL count as finished with 0 points.

**Traces to:** 2.10.4
**Verified by:** Test: `tests/test_card_states.py::test_postponed_stays_open_and_cancelled_finishes`

#### Scenario: Cancelled game
- **WHEN** a starter's game is cancelled
- **THEN** he counts as finished with 0 points

### Requirement: 2.10.5 Forward moves between refreshes
A card SHALL move from any state to any later state between two refreshes, as the transitions that only a refresh's snapshot sees allow.

**Rationale:** The site sees the world only at each refresh, so a card can skip states.
**Traces to:** 2.10
**Verified by:** Test: `tests/test_card_states.py::test_snapshot_skip_from_not_started_to_paused`

#### Scenario: Thursday skip
- **WHEN** the first refresh after Thursday's kickoff runs after the game has ended
- **THEN** a card goes from C straight to P1

### Requirement: 2.10.6 State document
`docs/games-page-states.md`, linked from the README's Games section, SHALL hold the state diagram, the table of states, the table of the 21 real transitions with their triggers, the separate table of snapshot-only transitions, the rules, and a gallery image of every state's card.

**Traces to:** 2.10; 10.13
**Verified by:** Test: `tests/test_feature_docs.py::test_doc_structure`; Test: `tests/test_card_states.py::test_real_transitions_land_on_the_right_state`

#### Scenario: Reading the states
- **WHEN** someone opens the state document
- **THEN** they find the diagram, the three tables, the rules and one card image per state

### Requirement: 2.10.6.1 Generated gallery
The gallery images SHALL be generated into `docs/images/games-states/` from fixture weeks by `tools/games_states_gallery.py`, using the layout harness.

**Traces to:** 2.10.6
**Verified by:** Inspection: `tools/games_states_gallery.py` writes every state's image to `docs/images/games-states/` from fixture weeks

#### Scenario: Regenerating the gallery
- **WHEN** the gallery script is run after a change to the cards
- **THEN** every state's image is redrawn from its fixture week
