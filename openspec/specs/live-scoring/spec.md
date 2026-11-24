# live-scoring Specification

## Purpose

How the simulation treats a week that is under way: who holds each lineup slot once games start, how finished and in-progress Players score, and how much uncertainty is left. It serves the live season Forecast (need 1) and the live game Forecasts (need 2); the formula is in `Calculations.txt`, section 12. Live Forecasts are kept out of the Forecast history by `playoff-odds-simulation` 1.2.3.

## Requirements

### Requirement: 1.1.12 Live week
The live week SHALL be the first week after the as-of week once any of its NFL games has kicked off.

**Traces to:** 1.1; 2.3
**Verified by:** Test: `tests/test_live.py::test_live_week_only_after_the_first_kickoff`

#### Scenario: After Thursday's kickoff
- **WHEN** a run happens on Saturday of week 11
- **THEN** week 11 is the live week

### Requirement: 1.1.12.1 Before the first kickoff
Until a week's first kickoff, that week SHALL be simulated wholly from projections.

**Traces to:** 1.1.12
**Verified by:** Test: `tests/test_live.py::test_live_week_only_after_the_first_kickoff`; Test: `tests/test_live_scoring.py::test_defaults_reproduce_the_pre_live_formula_exactly`

#### Scenario: Before Thursday's kickoff
- **WHEN** a run happens on Wednesday of week 11
- **THEN** week 11 is simulated wholly from projections and there is no live week

### Requirement: 1.1.12.2 Locked slots
In the live week, a starting slot whose Player's NFL game has kicked off SHALL hold the Player the Manager started there, read from Sleeper's lineup for the week.

**Traces to:** 1.1.12
**Verified by:** Test: `tests/test_live.py::test_locked_starters_hold_their_slots_and_score_their_points`

#### Scenario: Thursday starter locked
- **WHEN** a Manager started a Thursday receiver at FLEX
- **THEN** that receiver holds FLEX in every later run of the week, whatever the model would pick

### Requirement: 1.1.12.2.1 Bench points left out
Of the Players whose games have kicked off, only those the Manager started SHALL count for the team.

**Traces to:** 1.1.12.2
**Verified by:** Test: `tests/test_live.py::test_locked_starters_hold_their_slots_and_score_their_points`

#### Scenario: Benched Thursday player
- **WHEN** a Thursday Player scored 25 points on the Manager's bench
- **THEN** he does not count for the team

### Requirement: 1.1.12.3 Open slots
In the live week, the slots not yet locked SHALL be filled with the model's best legal lineup from rostered Players whose games have not kicked off, with the replacement-level floor.

**Traces to:** 1.1.12; 1.1.4
**Verified by:** Test: `tests/test_live.py::test_open_slot_repicked_after_a_ruling_out`

#### Scenario: Sunday slots stay open
- **WHEN** a Manager's Sunday running back is ruled out on Saturday
- **THEN** the model's lineup for that slot picks from the Players not yet locked

### Requirement: 1.1.12.4 Final scoring
A locked Player whose game is final SHALL score his actual points under the league's scoring, with no simulated error.

**Traces to:** 1.1.12; 1.1.12.2
**Verified by:** Test: `tests/test_live_scoring.py::test_final_starter_scores_his_points_with_no_noise`

#### Scenario: Final game
- **WHEN** a starter's game is final with 18.4 points
- **THEN** he scores exactly 18.4 in every simulated run

### Requirement: 1.1.12.5 In-progress scoring
A locked Player whose game is in progress SHALL score his points so far plus the share of his game left times his projection and his error pool's mean miss, with the scatter around that scaled by the square root of the share left.

**Rationale:** Calculations.txt section 12.
**Traces to:** 1.1.12; 1.1.5
**Verified by:** Test: `tests/test_live_scoring.py::test_half_time_matches_the_spec_example`; Test: `tests/test_live_scoring.py::test_bias_scales_with_time_left_and_scatter_with_its_square_root`

#### Scenario: At half time
- **WHEN** a starter projected for 10 with no mean miss has 11 points at half time
- **THEN** his simulated scores average 16.0 (±0.05) with 70.7% (±2%) of a full game's spread

### Requirement: 1.1.12.5.1 Share of the game left
The share of a game left SHALL come from its quarter and clock out of 60 minutes, with overtime and a game without a clock counting as no time left.

**Traces to:** 1.1.12.5
**Verified by:** Test: `tests/test_schedule.py::test_share_left`; Test: `tests/test_live.py::test_in_progress_starter_keeps_the_share_left`

#### Scenario: Overtime
- **WHEN** a starter's game is in overtime
- **THEN** he scores his points so far with no simulated error
