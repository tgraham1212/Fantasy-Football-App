# injury-history Specification

## Purpose

Each fantasy Player's injury status and details per NFL week, so game cards can say who was not expected to play and Team News can report injuries and practice; statuses are inferred for weeks played before they were saved. It delivers need 6, Durable Record; the shared out statuses are in `Calculations.txt`, section 3.

## Requirements

### Requirement: 6.6 Weekly status saved
Each run during the regular season or playoffs SHALL save, for the current NFL week, every fantasy-position Player with a Sleeper injury status and that status, replacing the week's earlier save.

**Rationale:** The last save before the week ends is the one kept.
**Traces to:** 6
**Verified by:** Test: `tests/test_injuries.py::test_save_overwrites_the_current_week_and_keeps_earlier_weeks`; Test: `tests/test_injuries.py::test_statuses_keep_fantasy_positions_with_a_status`

#### Scenario: Status changes during the week
- **WHEN** a Player is Questionable on Thursday's run and Out on Saturday's
- **THEN** the week's saved status for him is Out

### Requirement: 6.6.1 Earlier weeks kept
A saved week's statuses SHALL stay as they were once a later week is current, with nothing saved in the offseason.

**Traces to:** 6.6
**Verified by:** Test: `tests/test_injuries.py::test_save_overwrites_the_current_week_and_keeps_earlier_weeks`; Test: `tests/test_injuries.py::test_save_does_nothing_in_the_offseason`

#### Scenario: Week rolls over
- **WHEN** the current week moves from 11 to 12
- **THEN** week 11's saved statuses stay as they were and week 12 is saved

### Requirement: 6.6.2 Shared out statuses
The out statuses SHALL be one list shared by the whole system: Out, Doubtful, IR, PUP, Sus, NA and DNR, labelled Out, Doubtful, IR, PUP, Suspended, Not active and Did not report.

**Rationale:** Doubtful counts as out because such Players almost never play (Calculations.txt section 3).
**Traces to:** 6.6; 2.1.6.1
**Verified by:** Test: `tests/test_injuries.py::test_shared_out_statuses_and_labels`

#### Scenario: Not active
- **WHEN** week 11 has a saved status of NA for a rostered quarterback whose team plays
- **THEN** he is listed as Not active

### Requirement: 6.6.3 Not playing in a week
For a team in a week, the system SHALL list each rostered Player expected not to play: on bye when his NFL team has no game, otherwise when his saved status is an out status.

**Traces to:** 6.6; 2.1.6
**Verified by:** Test: `tests/test_injuries.py::test_saved_statuses_and_bye_take_precedence`; Test: `tests/test_injuries.py::test_defense_bye_by_team_key`

#### Scenario: Bye
- **WHEN** a rostered Player's team has no game in week 9
- **THEN** he is listed as on bye regardless of any status

### Requirement: 6.6.3.1 Future weeks
For a week after the latest saved week, the latest saved statuses SHALL be used.

**Traces to:** 6.6.3
**Verified by:** Test: `tests/test_injuries.py::test_future_weeks_use_the_latest_saved_statuses`

#### Scenario: Upcoming week
- **WHEN** week 11's statuses are the latest saved and a rostered Player is Out in them
- **THEN** he is listed as Out for week 15, and Players without week-15 Projections yet are not inferred out

### Requirement: 6.6.3.2 Inferred out
For a week before statuses were first saved, a Player SHALL be listed as inferred out when he was on the roster, had a Projection of 0 or none, and his NFL team played.

**Traces to:** 6.6.3
**Verified by:** Test: `tests/test_injuries.py::test_inferred_out_for_weeks_without_saved_statuses`

#### Scenario: Inferred for an early week
- **WHEN** week 5 has no saved statuses and a rostered running back had no Projection while his team played
- **THEN** he is listed as inferred out

### Requirement: 6.6.4 Weekly Player details saved
Alongside each week's statuses, each run SHALL save, for every fantasy-position Player on a league roster, Sleeper's injury body part, practice participation and depth-chart order when set, replacing the week's earlier save and keeping earlier weeks.

**Traces to:** 6.6; 4.7.6
**Verified by:** Test: `tests/test_player_details.py::test_details_keep_rostered_fantasy_players_with_something_set`; Test: `tests/test_player_details.py::test_last_save_of_the_week_wins_and_earlier_weeks_stay`

#### Scenario: Depth chart change
- **WHEN** a running back's depth-chart order moves from 2 to 1 between weeks 10 and 11
- **THEN** week 10's saved details keep 2 and week 11's record 1
