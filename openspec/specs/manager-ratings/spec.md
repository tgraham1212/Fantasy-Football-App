# manager-ratings Specification

## Purpose

Rates every Manager's skill across the whole life of a league from their weekly points, so Managers can see who has been consistently good or bad over the years rather than how one season is going. It serves need 4, Manager History, through the ELO columns and rating chart (`league-odds-site` 4.1 to 4.3); the formulas are in `Calculations.txt`, section 15.

## Requirements

### Requirement: 4.6 Weekly rating
The system SHALL keep an Openskill-style rating, a mean and an uncertainty, per Manager, updated once per regular-season week by ranking every team in the league by points scored that week, highest first.

**Rationale:** Calculations.txt section 15; ranking by points alone rewards consistency, not luck of the schedule.
**Traces to:** 4; 4.1
**Verified by:** Test: `tests/test_ratings.py::test_higher_score_raises_mu`; Test: `tests/test_ratings.py::test_margin_does_not_matter`

#### Scenario: Blowout and squeaker rank the same
- **WHEN** in one week team A scores 150, team B 120 and team C 119
- **THEN** the week is rated with A first, B second and C third, and the margins play no part

### Requirement: 4.6.1 Rated weeks
Only regular-season weeks in which some team scored points SHALL change ratings.

**Traces to:** 4.6
**Verified by:** Test: `tests/test_ratings.py::test_weekly_results_cover_regular_season_scored_weeks_only`

#### Scenario: Playoff week
- **WHEN** week 15 is a playoff week in a league whose regular season ends in week 14
- **THEN** no rating changes for week 15

#### Scenario: Unplayed week
- **WHEN** the current week's games have not been played and every team shows 0 points
- **THEN** that week is not rated

### Requirement: 4.6.2 Starting rating
Every Manager SHALL start at a rating of 1000 with the full starting uncertainty, in their first stored season or when they join later, without moving the other Managers' ratings.

**Traces to:** 4.6
**Verified by:** Test: `tests/test_ratings.py::test_newcomer_starts_at_1000_and_does_not_move_the_others`

#### Scenario: Newcomer
- **WHEN** a Manager first appears in a league's third stored season
- **THEN** their rating entering their first week is 1000 and the others' ratings are unchanged by their arrival

### Requirement: 4.6.2.1 Displayed rating
The displayed rating SHALL be the rating mean, not a conservative estimate.

**Traces to:** 4.6.2; 4.1
**Verified by:** Test: `tests/test_export.py::test_export_carries_ratings_when_present`

#### Scenario: ELO column
- **WHEN** a Manager's rating mean is 1675.6
- **THEN** the ELO column shows 1676

### Requirement: 4.6.3 Preseason reversion
Entering every season after a Manager's first, the system SHALL move their rating mean a configured fraction of the way toward the fixed value 1000, one third by default, leaving their uncertainty unchanged.

**Rationale:** The fixed anchor keeps the scale from drifting with the league's mean.
**Traces to:** 4.6
**Verified by:** Test: `tests/test_ratings.py::test_revert_moves_a_third_toward_the_anchor`; Test: `tests/test_ratings.py::test_preseason_reversion_and_fresh_start`

#### Scenario: One third back
- **WHEN** a Manager ends a season at 1300 and the reversion fraction is one third
- **THEN** they enter the next season at 1200

#### Scenario: Fixed anchor
- **WHEN** the league's mean rating has drifted to 1060 by the end of a season
- **THEN** every Manager is still pulled toward 1000

### Requirement: 4.6.4 Early-season multiplier
The system SHALL multiply each Manager's rating-mean change in a season's first rated weeks by a configured non-increasing schedule, 2, 1.75, 1.5 and 1.25 for weeks one to four by default and 1 afterwards, leaving the uncertainty update as the model computes it.

**Traces to:** 4.6
**Verified by:** Test: `tests/test_ratings.py::test_first_week_doubles_the_model_delta_and_week_five_does_not`; Test: `tests/test_ratings.py::test_multiplier_scales_only_the_mean_change`

#### Scenario: Week one
- **WHEN** the model's update would raise a Manager's mean by 40 in the first rated week of a season
- **THEN** their mean rises by 80

### Requirement: 4.6.4.1 By rated week
The multiplier schedule SHALL follow the order of rated weeks, not calendar weeks.

**Traces to:** 4.6.4
**Verified by:** Test: `tests/test_ratings.py::test_schedule_follows_rated_week_order_not_calendar_week`

#### Scenario: Late start
- **WHEN** a league's regular season starts in week 2
- **THEN** week 2 is the first rated week and takes the first multiplier

### Requirement: 4.6.5 Ratings follow the Manager
Ratings SHALL be keyed by the Sleeper user id of the Manager holding the roster that season, so that a Manager keeps one rating across roster changes and former Managers keep their last rating.

**Traces to:** 4.6; 4.5
**Verified by:** Test: `tests/test_ratings.py::test_managers_keyed_by_user_and_flagged_current`

#### Scenario: Roster slot changes hands
- **WHEN** roster 4 is held by one user in 2023 and another in 2024
- **THEN** each user's rating covers only the seasons they held a roster

### Requirement: 4.6.5.1 Inherited rosters
A roster without a Manager on record SHALL be rated under the one it inherits: the most recent earlier holder of that roster, else the first later one.

**Traces to:** 4.6.5
**Verified by:** Test: `tests/test_ratings.py::test_ownerless_roster_is_rated_under_its_inherited_owner`; Test: `tests/test_vacant_owner.py::test_vacant_in_the_first_stored_season_takes_the_later_owner`

#### Scenario: Vacant roster with an earlier holder
- **WHEN** dynasty roster 11 had no Manager in 2023 and was DeekBurg's in 2022
- **THEN** its 2023 weeks are rated as DeekBurg's

### Requirement: 4.6.5.2 Vacant rosters
A roster without a Manager in any stored season SHALL be rated as a distinct vacant entry for that season, marked as not a Manager, so that the week's ranking stays complete.

**Traces to:** 4.6.5
**Verified by:** Test: `tests/test_ratings.py::test_roster_never_owned_becomes_a_vacant_manager`

#### Scenario: Vacant roster
- **WHEN** a 2023 roster had no Manager in any stored season
- **THEN** its weekly points still rank against the other teams, under a vacant entry for that season

### Requirement: 4.6.6 Weekly z-score
For every rated week, each team's z-score SHALL be its points minus the mean of all teams' points that week, divided by the sample standard deviation of those points.

**Traces to:** 4.6
**Verified by:** Test: `tests/test_ratings.py::test_z_scores_use_sample_sd`

#### Scenario: Weekly z
- **WHEN** a team scores 130 in a week whose 12 scores have a mean of 110 and a sample standard deviation of 20
- **THEN** its z-score for the week is 1.0

### Requirement: 4.6.6.1 Career mean z-score
Each Manager's career mean z-score SHALL be the mean of their weekly z-scores over every rated week they have played, never reset.

**Traces to:** 4.6.6; 4.2.1
**Verified by:** Test: `tests/test_ratings.py::test_career_z_is_the_mean_of_weekly_z`; Test: `tests/test_ratings.py::test_career_z_spans_seasons_and_season_z_resets`

#### Scenario: Career mean spans seasons
- **WHEN** a Manager has z-scores of 1.0 and 0.0 in one season and −0.5 in the next
- **THEN** their career mean z after those three weeks is 0.17 (±0.01)

### Requirement: 4.6.7 Background rating variants
The system SHALL also store, per Manager and week, a season-to-date mean z-score reset each season, an exponentially weighted z-score with a configured weight, and a fresh-start rating reset to 1000 each preseason without the early-season multiplier.

**Traces to:** 4.6
**Verified by:** Test: `tests/test_ratings.py::test_career_z_spans_seasons_and_season_z_resets`; Test: `tests/test_ratings.py::test_preseason_reversion_and_fresh_start`

#### Scenario: Fresh-start rating
- **WHEN** a Manager ended the previous season rated 1300 under the fresh-start variant
- **THEN** they enter the next season at 1000 under that variant

### Requirement: 4.6.7.1 Variants kept off the site
The site data SHALL carry only the rating mean and career mean z-score of each rated week, leaving the background variants out.

**Traces to:** 4.6.7; 4.3
**Verified by:** Inspection: `src/ffapp/export.py`, the exported rating history holds only the mean and career mean z

#### Scenario: Exported history
- **WHEN** the site is exported
- **THEN** no league file holds a season-to-date, exponential or fresh-start value

### Requirement: 4.6.8 Preseason entry after the draft
For every stored season whose draft is done, the system SHALL store a week-0 entry for each of that season's Managers holding their rating entering the season, with their uncertainty unchanged, no weekly z-score, and their career mean z carried over.

**Traces to:** 4.6; 4.1.1
**Verified by:** Test: `tests/test_ratings.py::test_preseason_entries_after_the_draft`

#### Scenario: Returning Manager after the draft
- **WHEN** a Manager ended 2025 at 1300 and the 2026 league is in season with no week scored yet
- **THEN** their latest entry is 2026 week 0 with a rating mean of 1200 and no z-score

#### Scenario: Newcomer after the draft
- **WHEN** a Manager first holds a roster in 2026 and the 2026 draft is done
- **THEN** their first entry is 2026 week 0 with a rating mean of 1000

### Requirement: 4.6.8.1 No entry before the draft
A season whose draft is not done SHALL have no week-0 entries.

**Traces to:** 4.6.8
**Verified by:** Test: `tests/test_ratings.py::test_no_preseason_entries_before_the_draft`

#### Scenario: Before the draft
- **WHEN** the 2026 league is stored with status pre_draft
- **THEN** no 2026 entries exist and every Manager's latest entry is from 2025

### Requirement: 4.6.9 Ratings file
The `ratings` command SHALL write one file per configured league holding, for every Manager, their identity, display name and current or former status, and a per-week history of rating mean, uncertainty, z-score, career mean z and the background variants, in season and week order.

**Traces to:** 4.6; 6
**Verified by:** Test: `tests/test_ratings.py::test_ratings_file_written_for_every_week_and_manager`; Test: `tests/test_ratings.py::test_managers_keyed_by_user_and_flagged_current`

#### Scenario: Full history written
- **WHEN** the command runs on a league with five stored seasons
- **THEN** the file holds a history entry for every rated week of all five seasons for every Manager who played that week

### Requirement: 4.6.9.1 Repeatable ratings file
Running the `ratings` command again on unchanged data SHALL write the same file apart from its generation time.

**Traces to:** 4.6.9
**Verified by:** Test: `tests/test_ratings.py::test_ratings_deterministic`

#### Scenario: Deterministic
- **WHEN** the command runs twice on the same stored data
- **THEN** the two files are identical apart from the generation time

### Requirement: 4.6.10 Rating settings
The reversion fraction, the early-season multipliers, the starting rating and uncertainty, and the exponential weight SHALL be optional configuration values, with defaults of one third, 2, 1.75, 1.5 and 1.25, 1000 with an uncertainty of 333.3, and 0.2, applied to every league alike.

**Traces to:** 4.6
**Verified by:** Test: `tests/test_config.py::test_ratings_defaults_without_section`; Test: `tests/test_config.py::test_ratings_parsed`

#### Scenario: Defaults
- **WHEN** the configuration has no ratings block
- **THEN** every league uses the default values

### Requirement: 4.6.10.1 Invalid settings rejected
Loading the configuration SHALL fail on an invalid rating setting, naming the field.

**Traces to:** 4.6.10
**Verified by:** Test: `tests/test_config.py::test_invalid_ratings_rejected`; Test: `tests/test_config.py::test_unknown_ratings_key_rejected`

#### Scenario: Rejected value
- **WHEN** the configuration sets the reversion fraction to 1.5
- **THEN** loading the configuration fails with a message naming the field
