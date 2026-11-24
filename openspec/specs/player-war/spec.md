# player-war Specification

## Purpose

How a Player's season is valued in wins above replacement (WAR) for a league: consensus lineups and a replacement cut drawn from start percentages, season-wide constants, weekly win probabilities, and the stored result per league-season. It delivers need 3, Player Value; the formula, its assumptions and the reasons for the merged cut are in `Calculations.txt`, section 16.

## Requirements

### Requirement: 3.3 Wins above replacement
A Player's WAR for a league-season SHALL be his expected wins over the regular-season weeks he was active, minus the expected wins of a Player scoring the position's replacement level in those weeks, both with the same season constants.

**Rationale:** Calculations.txt section 16.
**Traces to:** 3; 3.2
**Verified by:** Test: `tests/test_war.py::test_replacement_season_has_zero_war_and_spec_example_gives_154`

#### Scenario: Replacement season
- **WHEN** a Player's score equals the replacement level in every week
- **THEN** his WAR is 0

#### Scenario: Above replacement
- **WHEN** a Player's weekly win probabilities sum to 7.70 and the replacement baseline is 6.16
- **THEN** his WAR is 1.54

### Requirement: 3.3.1 Expected wins
A Player's expected wins SHALL be the sum of his weekly win probabilities over the regular-season weeks he was active.

**Traces to:** 3.3
**Verified by:** Test: `tests/test_war.py::test_player_weeks_count_only_active_weeks_and_keep_zero_when_played`

#### Scenario: Thirteen active weeks
- **WHEN** a Player was active in 13 weeks
- **THEN** his expected wins are the sum of those 13 weekly win probabilities

### Requirement: 3.3.2 Weekly win probability
A Player's weekly win probability SHALL be the share of a normal distribution, with the opponent mean and spread, lying below the opponent mean plus his score minus his position's slot mean.

**Traces to:** 3.3; 3.3.1
**Verified by:** Test: `tests/test_war.py::test_win_probability_matches_spec_example`

#### Scenario: Big week
- **WHEN** a tight end scores 31.3 against a TE slot mean of 9.2 with an opponent spread of 20.7
- **THEN** the week's win probability is 0.86 (±0.01)

### Requirement: 3.3.2.1 Active weeks only
Only the weeks a Player was active SHALL count, a bye or a week he was ruled out adding nothing to his expected wins or his replacement baseline.

**Traces to:** 3.3.2
**Verified by:** Test: `tests/test_war.py::test_player_weeks_count_only_active_weeks_and_keep_zero_when_played`; Test: `tests/test_war.py::test_active_weeks_war_equals_the_old_replacement_fill_definition`

#### Scenario: Missed week
- **WHEN** a Player has no game in week 5
- **THEN** week 5 does not change his WAR

### Requirement: 3.3.2.2 Zero-point games
A week in which the Player played and scored zero SHALL count with a score of zero.

**Traces to:** 3.3.2
**Verified by:** Test: `tests/test_war.py::test_player_weeks_count_only_active_weeks_and_keep_zero_when_played`

#### Scenario: Injured on the first snap
- **WHEN** a Player appears in the week's stat lines with zero points
- **THEN** the week counts as played with the win probability of a zero score

### Requirement: 3.3.3 Consensus lineup
For each league-season and regular-season week, the system SHALL build a consensus lineup: each position's starting slots, 12 teams times the slots, filled by its most-started Players with a game that week, then the flex slots by the most-started remaining RB, WR and TE.

**Traces to:** 3.3
**Verified by:** Test: `tests/test_war.py::test_consensus_lineup_skips_unavailable_and_flex_moves_the_cut`; Test: `tests/test_war.py::test_consensus_lineup_without_flex_keeps_three_past_the_cut`

#### Scenario: Bye week skipped
- **WHEN** the third most-started quarterback is on bye in week 7
- **THEN** week 7's QB slots are filled from the other most-started quarterbacks with a game

### Requirement: 3.3.3.1 Positions from the roster slots
The consensus lineup's positions SHALL follow the league-season's roster slots, so that a position without a slot has no lineup, cut or WAR.

**Traces to:** 3.3.3
**Verified by:** Test: `tests/test_war.py::test_build_war_on_a_synthetic_season`

#### Scenario: No kicker slot
- **WHEN** the league's roster slots have no K
- **THEN** no kicker lineup, cut or WAR exists for that league-season

### Requirement: 3.3.4 Replacement cut
For each week and position, the replacement Players SHALL be the three most-started Players with a game that week who were left out of the consensus lineup at their position and at flex.

**Traces to:** 3.3; 3.3.3
**Verified by:** Test: `tests/test_war.py::test_consensus_lineup_skips_unavailable_and_flex_moves_the_cut`

#### Scenario: Tight end cut
- **WHEN** 12 tight ends fill the TE slots and none of the rest make the flex
- **THEN** the 13th to 15th most-started tight ends with a game are the week's replacement tight ends

#### Scenario: Flex moves the running back cut
- **WHEN** the 25th to 30th most-started running backs are taken by the flex slots
- **THEN** the replacement running backs are the next three past them

### Requirement: 3.3.4.1 Season replacement level
A position's replacement level for the season SHALL be the mean of its replacement Players' actual points, under the league's scoring, across the regular-season weeks.

**Traces to:** 3.3.4
**Verified by:** Test: `tests/test_war.py::test_build_war_on_a_synthetic_season`

#### Scenario: Two weeks
- **WHEN** the replacement running backs average 2.0 points in week 1 and 1.0 in week 2
- **THEN** the RB replacement level is 1.5

### Requirement: 3.3.5 Season constants
For each league-season, the slot mean per position SHALL be the consensus starters' mean actual points, the opponent mean the slot-count-weighted sum of slot means, and the opponent spread the square root of the slot-count-weighted sum of slot variances.

**Traces to:** 3.3; 3.3.2
**Verified by:** Test: `tests/test_war.py::test_season_constants_pool_slots_and_weight_by_slots_per_team`

#### Scenario: Completed season
- **WHEN** the WAR command runs for redraft 2024
- **THEN** the constants are computed over weeks 1 to 14

### Requirement: 3.3.5.1 Weeks covered
The season constants SHALL cover every regular-season week scored so far, the stored file recording the last one.

**Traces to:** 3.3.5
**Verified by:** Test: `tests/test_war.py::test_build_war_on_a_synthetic_season`

#### Scenario: Season in progress
- **WHEN** the WAR command runs with week 9 the last scored week
- **THEN** the constants cover weeks 1 to 9 and the file records week 9

### Requirement: 3.3.6 Who gets a WAR
Every Player at a lineup position with at least one regular-season game that season SHALL get a WAR for each league, whether or not a team in the league rostered him.

**Traces to:** 3.3
**Verified by:** Test: `tests/test_war.py::test_build_war_on_a_synthetic_season`

#### Scenario: Unrostered producer
- **WHEN** a wide receiver on no roster in the league plays 13 games
- **THEN** he has a WAR for that league-season

#### Scenario: Retired but listed
- **WHEN** a Player is in the player database but has no stat line in any week of the season
- **THEN** he has no WAR entry

### Requirement: 3.3.7 Replacement cut mode
Each league-season SHALL use the weekly cut when every scored regular-season week has a weekly snapshot, the yearly cut when none does, and the merged cut when some do, naming the cut in its file.

**Traces to:** 3.3; 3.3.4
**Verified by:** Test: `tests/test_war.py::test_cut_mode`

#### Scenario: Past season
- **WHEN** the WAR command runs for 2023
- **THEN** 2023 uses the yearly cut and the file is marked yearly

### Requirement: 3.3.7.1 Weekly cut
In the weekly cut, each week's consensus lineup and replacement Players SHALL come from that week's snapshot.

**Traces to:** 3.3.7
**Verified by:** Test: `tests/test_war.py::test_build_war_weekly_cut_and_in_progress_owner`

#### Scenario: Season with every week captured
- **WHEN** every scored week of a season has a weekly snapshot
- **THEN** that season uses the weekly cut and each week ranks by its own snapshot

### Requirement: 3.3.7.2 Yearly cut
In the yearly cut, every week SHALL rank Players by the season snapshot.

**Rationale:** Past seasons were captured after they ended, so their season snapshot is season-long.
**Traces to:** 3.3.7
**Verified by:** Test: `tests/test_war.py::test_build_war_on_a_synthetic_season`

#### Scenario: Completed season
- **WHEN** 2024 has only a season snapshot
- **THEN** every 2024 week ranks Players by it

### Requirement: 3.3.7.3 Merged cut
In the merged cut, a scored week with a weekly snapshot SHALL use that snapshot, while every other week ranks Players by their merged start percentage and never by the season snapshot.

**Rationale:** Calculations.txt section 16: in season, ESPN's season figure is only the current week's.
**Traces to:** 3.3.7
**Verified by:** Test: `tests/test_war.py::test_build_war_partly_captured_uses_merged_cut`

#### Scenario: Partly captured season
- **WHEN** a season has weekly snapshots for weeks 10 and 11 only, and weeks 1 to 10 are scored
- **THEN** week 10 uses its own snapshot, weeks 1 to 9 use the merged start percentage, and the file is marked merged

### Requirement: 3.3.7.3.1 Merged start percentage
A Player's merged start percentage SHALL be his highest percent started in a trusted weekly snapshot: a scored week's snapshot only if he played that week, and the unscored current week's always.

**Rationale:** Byes and injuries only lower a start percentage (Calculations.txt section 16).
**Traces to:** 3.3.7.3
**Verified by:** Test: `tests/test_war.py::test_merged_start_percentage_rules`; Test: `tests/test_war.py::test_build_war_partly_captured_healthy_player_keeps_his_start_rate`

#### Scenario: Bye in the captured scored week
- **WHEN** a healthy receiver's team had a bye in week 10, the only scored captured week, and the unscored week 11 snapshot shows him 80% started and 95% owned
- **THEN** his merged start percentage is 80

#### Scenario: Bye in the current week
- **WHEN** a running back was 85% started in week 10, which he played, and 8% in the unscored week 11 because of a bye
- **THEN** his merged start percentage is 85

### Requirement: 3.3.7.3.2 Ownership for injured Players
A Player not seen active in any scored captured week whose latest stored status is on the shared out-status list SHALL take the higher of his merged start percentage and his percent owned.

**Rationale:** Calculations.txt section 16: ownership tracks a hurt starter's role, not a healthy backup's.
**Traces to:** 3.3.7.3; 3.3.7.3.1
**Verified by:** Test: `tests/test_war.py::test_doubtful_player_never_seen_active_uses_ownership`

#### Scenario: Injured before weekly capture began
- **WHEN** a running back played weeks 1 to 5, is on IR, and is 70% owned and 0% started in every weekly snapshot
- **THEN** his merged start percentage is 70, and he is ranked by it for weeks 1 to 5

#### Scenario: Healthy backup not seen active
- **WHEN** a healthy receiver did not play in the only scored captured week, shows 15% started in the unscored week, and is 50% owned
- **THEN** his merged start percentage is 15

### Requirement: 3.3.7.3.3 Ownership source and ties
A Player's percent owned SHALL come from the most recent weekly snapshot holding him, or else the season snapshot, with ties in every ranking broken by ESPN id.

**Traces to:** 3.3.7.3; 3.3.7.3.2
**Verified by:** Test: `tests/test_war.py::test_doubtful_player_never_seen_active_uses_ownership`

#### Scenario: Latest ownership
- **WHEN** a Player is 70% owned in week 10's snapshot and 68% in week 11's
- **THEN** his percent owned is 68

### Requirement: 3.3.8 WAR stored
The system SHALL write, per league and season, a file holding the cut, the week it runs through, the season constants and replacement levels, and per qualifying Player his Sleeper id, name, position, last NFL team, games, points, position stats, weekly scores and win probabilities, expected wins and WAR.

**Traces to:** 3.3; 6
**Verified by:** Test: `tests/test_war.py::test_write_war_writes_every_season_and_is_deterministic`; Test: `tests/test_war.py::test_build_war_on_a_synthetic_season`

#### Scenario: All seasons written
- **WHEN** the WAR command runs
- **THEN** every stored season of every configured league gets a file

### Requirement: 3.3.8.1 Repeatable WAR files
Re-running on unchanged data SHALL write the same file apart from its timestamp.

**Traces to:** 3.3.8
**Verified by:** Test: `tests/test_war.py::test_write_war_writes_every_season_and_is_deterministic`

#### Scenario: Re-run
- **WHEN** the WAR command runs twice on the same data
- **THEN** both files match apart from their timestamps

### Requirement: 3.3.8.2 Missing season snapshot
A season with no season snapshot SHALL be skipped, the command naming the season.

**Traces to:** 3.3.8
**Verified by:** Test: `tests/test_war.py::test_write_war_skips_and_reports_a_season_without_snapshot`

#### Scenario: Missing snapshot
- **WHEN** a season has no season snapshot
- **THEN** no file is written for it and the command reports which season is missing
