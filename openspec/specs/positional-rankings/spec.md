# positional-rankings Specification

## Purpose

Per league and season, each Manager's rostered Players by position, with a regular-season points-per-game figure that blends what they have scored with what they are projected to score, plus the roster flags, replacement level and axis the Positions sub-tab draws. It serves need 3, Player Value, through `positional-rankings-page`; the formula is in `Calculations.txt`, section 17.

## Requirements

### Requirement: 3.4 Points per game
A Player's points per game SHALL be his actual points in the regular-season weeks he played plus his projected points for the regular-season weeks not yet final, divided by the number of those played and projected weeks.

**Rationale:** Calculations.txt section 17.
**Traces to:** 3; 3.1
**Verified by:** Test: `tests/test_positions.py::test_points_per_game_blends_actual_and_projected`

#### Scenario: Mid-season blend
- **WHEN** a receiver has 120 points in 8 played weeks after week 10, and projections of 14, 12, 0 (bye) and 13 for weeks 11 to 14
- **THEN** his points per game is (120 + 14 + 12 + 13) / (8 + 3) = 14.45

### Requirement: 3.4.1 League scoring and weeks
Points SHALL be scored under the league's rules for that season, over the weeks before the league's playoffs.

**Traces to:** 3.4
**Verified by:** Test: `tests/test_positions.py::test_points_per_game_blends_actual_and_projected`

#### Scenario: Playoff weeks left out
- **WHEN** a league's playoffs start in week 15
- **THEN** weeks 15 to 17 add nothing to points per game

### Requirement: 3.4.2 Played weeks
A week SHALL count as played when the Player's team played and he has a stat line.

**Traces to:** 3.4
**Verified by:** Test: `tests/test_positions.py::test_points_per_game_blends_actual_and_projected`

#### Scenario: Completed season
- **WHEN** rankings are built for a completed season
- **THEN** every week is final and points per game uses actual points only

### Requirement: 3.4.3 Projected weeks
A week SHALL count as projected while it is not final and the Player's projection for it is above zero, including a week whose games are in progress.

**Traces to:** 3.4
**Verified by:** Test: `tests/test_positions.py::test_points_per_game_blends_actual_and_projected`

#### Scenario: Not yet played
- **WHEN** a rookie has no stat line in weeks 1 to 10 and is projected for 6 points in each of weeks 11 to 14
- **THEN** his points per game is 6.0 from 4 projected weeks

#### Scenario: Live week
- **WHEN** week 11 games are in progress and a quarterback has 12 points so far against a 19-point projection
- **THEN** week 11 counts as a projected week worth 19 points until it is final

### Requirement: 3.4.4 Who is rated
A Player whose played and projected weeks total more than zero points SHALL be rated.

**Traces to:** 3.4
**Verified by:** Test: `tests/test_positions.py::test_points_per_game_blends_actual_and_projected`

#### Scenario: Nothing scored or projected
- **WHEN** a Player has played no week and every remaining projection is zero
- **THEN** he is left out

### Requirement: 3.4.5 Points for any team
A Player's points SHALL count from every game he played, for any team or as a free agent.

**Rationale:** The figure rates the Player, not the Manager's results.
**Traces to:** 3.4
**Verified by:** Inspection: `src/ffapp/positions.py`, points per game reads each Player's own stat lines, not matchup points

#### Scenario: Traded in
- **WHEN** a running back scored 60 points in 5 weeks for another Manager before being traded
- **THEN** those 5 weeks and 60 points count on his new Manager's row

### Requirement: 3.4.6 Roster used
Each team's Players SHALL be its final roster for a completed season and its current roster for the season in progress.

**Traces to:** 3.4; 3.1
**Verified by:** Test: `tests/test_positions.py::test_completed_season_uses_actual_points_and_no_injury_flags`; Test: `tests/test_positions.py::test_roster_flags_and_owners`

#### Scenario: Completed season
- **WHEN** positional rankings are built for redraft 2025
- **THEN** each team lists its end-of-season 2025 roster, including anyone added during the playoffs

### Requirement: 3.4.6.1 Taxi and reserve marked
Players on the taxi squad and on reserve SHALL be included and marked as taxi or reserve.

**Traces to:** 3.4.6; 3.1.6
**Verified by:** Test: `tests/test_positions.py::test_roster_flags_and_owners`

#### Scenario: Season in progress
- **WHEN** positional rankings are built for dynasty 2026 in week 11
- **THEN** taxi Players are listed and marked as taxi

### Requirement: 3.4.6.2 Started positions only
Only Players at a position the league starts SHALL be included.

**Traces to:** 3.4.6
**Verified by:** Test: `tests/test_positions.py::test_points_per_game_blends_actual_and_projected`; Test: `tests/test_positions.py::test_roster_flags_and_owners`

#### Scenario: No kicker slot
- **WHEN** a dynasty roster holds a kicker and the dynasty league has no K slot
- **THEN** the kicker is not listed

### Requirement: 3.4.7 Injury flag
For the season in progress, a Player whose latest stored status is on the shared out-status list SHALL be flagged as injured, with that status recorded.

**Traces to:** 3.4; 3.1.6
**Verified by:** Test: `tests/test_positions.py::test_roster_flags_and_owners`

#### Scenario: Doubtful
- **WHEN** a tight end's latest stored status is Doubtful
- **THEN** he is flagged as injured with status Doubtful

#### Scenario: Questionable
- **WHEN** a receiver's latest stored status is Questionable
- **THEN** he is not flagged and carries no status

### Requirement: 3.4.7.1 No flags in past seasons
Completed seasons SHALL carry no injury flags or statuses.

**Traces to:** 3.4.7
**Verified by:** Test: `tests/test_positions.py::test_completed_season_uses_actual_points_and_no_injury_flags`

#### Scenario: Past season
- **WHEN** rankings are built for 2024
- **THEN** no Player is flagged as injured

### Requirement: 3.4.8 Replacement level carried
Each league-season's rankings SHALL carry, per position, the replacement level from that league-season's WAR file, or none when the file is missing.

**Traces to:** 3.4; 3.1.4; 3.3.4.1
**Verified by:** Test: `tests/test_positions.py::test_replacement_level_from_war_or_none`

#### Scenario: WAR present
- **WHEN** the redraft 2025 WAR file gives an RB replacement level of 7.94
- **THEN** the rankings carry 7.94 for RB

#### Scenario: WAR missing
- **WHEN** a league-season has no WAR file
- **THEN** the rankings are written without replacement levels and nothing fails

### Requirement: 3.4.9 Fixed axis range
A position's axis range SHALL be the same in every season of a league, covering about 99% of all its seasons' points-per-game values, rounded outward to multiples of 5, and including zero and the highest replacement level.

**Traces to:** 3.4; 3.1.2.4
**Verified by:** Test: `tests/test_positions.py::test_axis_is_shared_across_seasons_and_ignores_outliers`

#### Scenario: Outlier outside the range
- **WHEN** one kicker averaged 31 points from a single game and nearly every other kicker season is under 15
- **THEN** the K axis is 0 to 15

### Requirement: 3.4.10 Positional rankings exported
The export SHALL write, per league, one positional rankings file per stored season and an index listing the seasons and the current one.

**Traces to:** 3.4; 3.1.1.1
**Verified by:** Test: `tests/test_export.py::test_export_writes_positional_rankings`; Test: `tests/test_positions.py::test_export_payload_has_axis_in_every_season_and_an_index`

#### Scenario: Files per season
- **WHEN** the export runs with redraft data stored for 2021 to 2026
- **THEN** six redraft files and one index are written, the index naming 2026 as current

### Requirement: 3.4.10.1 File contents
Each season file SHALL hold the weeks covered, the last final week, each position's replacement level and axis, and each Manager's name, ids and Players, each Player with his id, name, position, NFL team, points per game, game counts, flags and out status.

**Traces to:** 3.4.10
**Verified by:** Test: `tests/test_positions.py::test_export_payload_has_axis_in_every_season_and_an_index`; Test: `tests/test_positions.py::test_roster_flags_and_owners`

#### Scenario: Player entry
- **WHEN** the dynasty 2026 file is read
- **THEN** each Player carries his points per game with the played and projected game counts behind it, and his flags and out status

### Requirement: 3.4.10.2 Repeatable files
Re-running the export on unchanged data SHALL write the same files apart from their timestamps.

**Traces to:** 3.4.10
**Verified by:** Test: `tests/test_export.py::test_export_writes_positional_rankings`

#### Scenario: Re-run
- **WHEN** the export runs twice on the same data
- **THEN** the positional rankings files match
