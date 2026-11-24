# win-probability-added Specification

## Purpose

How much one Player's performance swung his team's probability of winning a game, measured against the Forecast made before kickoff. It serves need 2, Game Forecasts, and is shown on the Games sub-tab (`games-page` 2.1.12); the formula is in `Calculations.txt`, section 13.

## Requirements

### Requirement: 2.9 Win probability added
For each starter with an actual score, the system SHALL compute his win probability added: his team's probability of winning with his projection replaced by his score, minus that probability with his projection, every other Player at his projection.

**Traces to:** 2; 2.1.12
**Verified by:** Test: `tests/test_wpa.py::test_spec_example_big_game`; Test: `tests/test_wpa.py::test_dud_is_negative_and_a_projection_hit_is_near_zero`

#### Scenario: Big game
- **WHEN** a team's pre-kickoff margin is +4 with a spread of 24 and a starter projected for 10 scores 25
- **THEN** his win probability added is +22 points (±2)

#### Scenario: Dud
- **WHEN** the same starter scores 2
- **THEN** his win probability added is below -10 points

### Requirement: 2.9.1 Margin distribution
Both probabilities SHALL come from a normal distribution of the margin with the mean and spread of the game's pre-kickoff simulation, with the Player's own share of the spread removed once his score is known.

**Traces to:** 2.9
**Verified by:** Test: `tests/test_wpa.py::test_margin_stats_from_stored_fields_or_histograms`; Test: `tests/test_wpa.py::test_dud_is_negative_and_a_projection_hit_is_near_zero`

#### Scenario: Projection hit
- **WHEN** a starter scores exactly his projection
- **THEN** his win probability added is within 1 point of zero, moved only by the narrower spread

### Requirement: 2.9.1.1 Each side from its own margin
Each team's starters SHALL be measured from that team's own margin, the opponent's margin being its negative.

**Traces to:** 2.9.1
**Verified by:** Test: `tests/test_wpa.py::test_opponent_side_reads_from_its_own_margin`

#### Scenario: Underdog's star
- **WHEN** a team's margin is -4 with a spread of 24 and its starter projected for 10 scores 25
- **THEN** his win probability added is above +20 points

### Requirement: 2.9.2 Finished Player
A Player whose game is final SHALL use his actual points as his score.

**Traces to:** 2.9
**Verified by:** Test: `tests/test_wpa.py::test_live_wpa_uses_the_pre_kickoff_baseline_and_skips_players_not_started`

#### Scenario: Thursday starter
- **WHEN** a Thursday starter finished with 31 points
- **THEN** his win probability added uses 31

### Requirement: 2.9.3 Player in progress
A Player whose game is in progress SHALL use his projected final, his points so far plus the share left times his projection, keeping the remaining share of his spread.

**Traces to:** 2.9; 1.1.12.5
**Verified by:** Test: `tests/test_wpa.py::test_in_progress_keeps_the_remaining_variance`; Test: `tests/test_wpa.py::test_live_wpa_uses_the_pre_kickoff_baseline_and_skips_players_not_started`

#### Scenario: Same projected final
- **WHEN** two starters have the same projected final, one finished and one at half time
- **THEN** the one at half time has the smaller win probability added, with more uncertainty left

### Requirement: 2.9.4 Not kicked off
Only Players whose games have kicked off SHALL have a win probability added.

**Traces to:** 2.9
**Verified by:** Test: `tests/test_wpa.py::test_live_wpa_uses_the_pre_kickoff_baseline_and_skips_players_not_started`

#### Scenario: Not kicked off
- **WHEN** a starter's game starts Sunday night and it is Sunday afternoon
- **THEN** he has no win probability added

### Requirement: 2.9.5 Pre-kickoff baseline
Win probability added SHALL use the lineups and projections of the game's pre-kickoff Forecast, the Forecast of record or a provisional one during the live week, never live or final results.

**Rationale:** A Player's number then does not depend on how his teammates are doing.
**Traces to:** 2.9; 2.5
**Verified by:** Test: `tests/test_wpa.py::test_a_teammates_score_does_not_change_a_players_wpa`; Test: `tests/test_wpa.py::test_live_wpa_uses_the_pre_kickoff_baseline_and_skips_players_not_started`

#### Scenario: Teammate scores
- **WHEN** a teammate's touchdown changes the live win probability
- **THEN** this Player's win probability added is unchanged

### Requirement: 2.9.5.1 Weeks before the log
For a week finished before the Forecast log existed, win probability added SHALL use the pre-week Forecast's margin and the stored projections.

**Traces to:** 2.9.5; 2.5.3
**Verified by:** Test: `tests/test_wpa.py::test_records_carry_margins_and_wpa`

#### Scenario: Early 2026 week
- **WHEN** week 6 of 2026 finished before the log existed
- **THEN** its starters' win probability added uses the as-of-week-5 margin and their stored week-6 projections

### Requirement: 2.9.6 Stored with the record
Each Forecast of record SHALL carry the margin's mean and spread and each starter's win probability added.

**Traces to:** 2.9; 2.6
**Verified by:** Test: `tests/test_wpa.py::test_records_carry_margins_and_wpa`

#### Scenario: Final week
- **WHEN** week 10's records are stored
- **THEN** each team's record holds the margin mean and spread and every starter's win probability added
