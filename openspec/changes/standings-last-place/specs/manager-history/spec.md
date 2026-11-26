## MODIFIED Requirements

### Requirement: 4.5.2 Final places
Each completed season's final places SHALL come from the stored winners bracket for the playoff teams and, for the other teams, from the toilet bowl or the regular-season standings, by the league's losers-bracket type.

**Traces to:** 4.5
**Verified by:** Test: `tests/test_managers.py::test_dynasty_champions_and_runners_up_match_league_history`; Test: `tests/test_managers.py::test_incomplete_brackets_give_no_places`

#### Scenario: 2025 dynasty
- **WHEN** the 2025 dynasty brackets are stored
- **THEN** corygraham12 finishes 1st and Z28kid86 2nd

### Requirement: 4.5.2.1 Toilet bowl place
In a toilet-bowl league, the toilet bowl champion, the team that loses its final, SHALL finish last.

**Traces to:** 4.5.2
**Verified by:** Test: `tests/test_managers.py::test_toilet_bowl_winner_is_last_place`

#### Scenario: Toilet bowl champion
- **WHEN** a redraft team loses the toilet bowl final
- **THEN** its finish is last

## ADDED Requirements

### Requirement: 4.5.2.2 Consolation games ignored
In a league without a toilet bowl, the teams outside the playoffs SHALL finish in regular-season standings order, by wins and then points for, whatever their consolation games.

**Rationale:** Consolation games decide nothing; Managers pay little attention to them and often leave lineups unset, so the standings are the fairer order.
**Traces to:** 4.5.2
**Verified by:** Test: `tests/test_managers.py::test_consolation_bracket_is_ignored`

#### Scenario: 2-12 team wins two consolation games
- **WHEN** a dynasty team goes 2-12, the worst record, and wins two consolation games
- **THEN** it finishes 12th, last

#### Scenario: Two 5-9 teams
- **WHEN** two teams outside the playoffs both go 5-9, one with 1,410 points and one with 1,380
- **THEN** the one with 1,410 points finishes ahead
