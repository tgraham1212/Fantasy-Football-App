## MODIFIED Requirements

### Requirement: 2.8 Lineup choices
For each team in a finished or live game, the system SHALL compute lineup choices to 0.1 point: its starters' points minus those of the best legal lineup of its rostered Players at their pre-kickoff Sleeper Projections.

**Rationale:** Following the projections scores 0. Calculations.txt section 11.
**Traces to:** 2; 2.1.14
**Verified by:** Test: `tests/test_views.py::test_lineup_choices_examples_and_live_rule`; Test: `tests/test_views.py::test_default_lineup_is_roster_only`

#### Scenario: Better choice
- **WHEN** the Manager's starters scored 104.3 and the default lineup's Players scored 96.9
- **THEN** the team's lineup choices are +7.4

#### Scenario: Benched the better Player
- **WHEN** the default lineup would have scored 12 more points
- **THEN** the team's lineup choices are -12.0

#### Scenario: Started the other quarterback, who scored more
- **WHEN** the default lineup starts QB A, the Manager starts QB B from the same roster, QB A scores 10 and QB B scores 15, and every other slot matches
- **THEN** the team's lineup choices are +5.0

#### Scenario: Started the other quarterback, who scored less
- **WHEN** the same swap is made, QB A scores 15 and QB B scores 10
- **THEN** the team's lineup choices are -5.0

#### Scenario: Followed the default
- **WHEN** the Manager starts exactly the default lineup
- **THEN** the team's lineup choices are 0.0

#### Scenario: A free agent projected higher
- **WHEN** an unrostered kicker projects higher than the team's only kicker, whom the Manager starts
- **THEN** the default lineup starts the team's kicker and the kicker slot adds nothing to lineup choices

#### Scenario: Empty starting slot
- **WHEN** the Manager leaves the defence slot empty and the default lineup starts a defence that scores 8.2
- **THEN** the empty slot counts 0 and the team's lineup choices include -8.2 for that slot

#### Scenario: Starter with no stored Projection
- **WHEN** the Manager starts a quarterback who has no stored Projection that week and he scores 27.2
- **THEN** he counts the same on both sides and adds 0 to the team's lineup choices

#### Scenario: Nobody to start
- **WHEN** the team's only kicker is on bye and the Manager leaves the kicker slot empty
- **THEN** both sides count 0 for the kicker slot

### Requirement: 2.8.1 Lineup choices while live
During the live week, lineup choices SHALL count only Players whose games have kicked off, on both sides.

**Traces to:** 2.8
**Verified by:** Test: `tests/test_views.py::test_lineup_choices_examples_and_live_rule`

#### Scenario: Sunday afternoon
- **WHEN** a team's default pick plays Sunday night and its actual starter played Thursday
- **THEN** only the Thursday starter counts until the Sunday night game kicks off

### Requirement: 2.8.2 Lineup choices for past seasons
For every finished week of a past season, the system SHALL compute each team's lineup choices from the stored weekly Projections and the stored matchup rosters and starters.

**Rationale:** The game log behind lineup choices began in 2026; the season league records for lineup choices cover every season.
**Traces to:** 2.8; 4.8.6
**Verified by:** Test: `tests/test_views.py::test_past_season_lineup_choices`

#### Scenario: 2023 week 5
- **WHEN** the build runs after this change
- **THEN** every team in 2023 week 5 has lineup choices computed from that week's stored Projections and its rostered Players only
