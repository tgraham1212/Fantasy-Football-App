# team-news Specification

## Purpose

Team News: short stories about each Manager's season, generated from stored data with editable sentence templates, for the Managers sub-tab's news card (`manager-pages` 4.4.8). It serves need 4, Manager History; the story rules are in `Calculations.txt`, section 20.

## Requirements

### Requirement: 4.7 Team News stories
The system SHALL generate each Manager's news stories from stored data for the current season.

**Rationale:** Calculations.txt section 20.
**Traces to:** 4; 4.4.8
**Verified by:** Test: `tests/test_news.py::test_result_and_streak_stories`; Inspection: `src/ffapp/news.py`, stories are built for the current season only

#### Scenario: Week 11
- **WHEN** the export runs during week 11 of 2026
- **THEN** each current Manager's stories cover 2026 only

### Requirement: 4.7.1 Result and streak stories
Each played week SHALL give a result story naming the top scorer, plus a streak story once a team wins or loses three or more in a row.

**Traces to:** 4.7
**Verified by:** Test: `tests/test_news.py::test_result_and_streak_stories`

#### Scenario: Third straight win
- **WHEN** a team wins its third game in a row
- **THEN** its result story and a three-game winning streak story appear

### Requirement: 4.7.2 Record stories
A story SHALL appear when a team breaks one of its records, or enters the league's all-time top 3, with the league rank.

**Traces to:** 4.7; 4.5.5.1
**Verified by:** Test: `tests/test_news.py::test_new_team_high_is_a_record_with_its_league_rank`

#### Scenario: New team high
- **WHEN** a team scores its highest total ever, the league's second highest
- **THEN** a record story names the score and its league rank of 2

### Requirement: 4.7.3 Forecast move stories
A story SHALL appear when a team's playoff Forecast changes by at least 10 points in a week.

**Traces to:** 4.7; 1.2
**Verified by:** Test: `tests/test_news.py::test_forecast_move_needs_ten_points`

#### Scenario: Forecast jump
- **WHEN** a team's playoff Forecast rises from 53% to 71% after a week
- **THEN** a story says it is up 18 to 71%

### Requirement: 4.7.4 Rivalry stories
Rivalry week SHALL give a preview story before the game and a result story after it.

**Traces to:** 4.7; 4.5.7
**Verified by:** Test: `tests/test_news.py::test_rivalry_preview_and_result`

#### Scenario: Rivalry week
- **WHEN** a Manager plays their rival in rivalry week
- **THEN** a preview story appears before the game and a result story after it

### Requirement: 4.7.5 Injury stories
A story SHALL appear when a rostered Player is newly given an out status, naming the body part.

**Traces to:** 4.7
**Verified by:** Test: `tests/test_news.py::test_injury_story_only_when_newly_out`

#### Scenario: Ruled out
- **WHEN** a rostered receiver goes from Questionable to Out with a hamstring injury
- **THEN** an injury story names him and his hamstring

### Requirement: 4.7.6 Practice and depth chart stories
A story SHALL appear when a rostered starter is limited or not practising, or a rostered Player's depth-chart order changes.

**Traces to:** 4.7
**Verified by:** Test: `tests/test_news.py::test_practice_report_for_starters_and_depth_chart_moves`

#### Scenario: Practice report
- **WHEN** a rostered starter is listed as not practising on Thursday
- **THEN** a practice report story names him and the day

### Requirement: 4.7.7 Trending add stories
A story SHALL appear when a rostered Player is among Sleeper's 10 most-added Players.

**Traces to:** 4.7
**Verified by:** Test: `tests/test_news.py::test_trending_add_in_the_top_ten`

#### Scenario: Hot pickup
- **WHEN** a Manager's backup running back is Sleeper's third most-added Player
- **THEN** a trending story names him

### Requirement: 4.7.8 WAR milestone stories
A story SHALL appear each time a rostered Player's WAR for the team passes a whole number.

**Traces to:** 4.7; 3.3
**Verified by:** Test: `tests/test_news.py::test_war_milestone_counts_only_weeks_on_the_team`

#### Scenario: Two wins
- **WHEN** a Player's WAR in weeks on the team passes 2.0
- **THEN** a milestone story appears

### Requirement: 4.7.9 Team of the Week
A Team of the Week story, the league's best lineup that week, SHALL appear only for a Manager with one of their Players in it.

**Traces to:** 4.7
**Verified by:** Test: `tests/test_news.py::test_team_of_the_week_only_with_their_player`; Test: `tests/test_news.py::test_team_of_the_week_picks_the_best_lineup`

#### Scenario: Without their Players
- **WHEN** none of a Manager's Players is in that week's Team of the Week
- **THEN** no Team of the Week story appears on their page

### Requirement: 4.7.10 Trade stories
Every trade SHALL give a story naming what each side got.

**Traces to:** 4.7; 4.5.10.2
**Verified by:** Test: `tests/test_news.py::test_trade_story_names_both_sides`

#### Scenario: Trade
- **WHEN** a Manager trades T. Etienne Jr. for J. Smith-Njigba
- **THEN** a trade story names both Players and both sides

### Requirement: 4.7.11 Big bid stories
A won bid of at least 25% of the season budget, or the team's biggest of the season, SHALL give a story with the next bid.

**Traces to:** 4.7; 4.5.11
**Verified by:** Test: `tests/test_news.py::test_big_bid_by_share_of_budget_or_the_seasons_biggest`

#### Scenario: Big bid
- **WHEN** a Manager wins a Player for $41 of a $100 budget against a next bid of $12
- **THEN** a big-bid story names both bids

### Requirement: 4.7.12 Pickup pays off
A story SHALL appear once when a pickup's added window passes +1.0 WAR for the team.

**Traces to:** 4.7; 4.5.8.1
**Verified by:** Test: `tests/test_news.py::test_pickup_pays_off_once_when_passing_one_war`

#### Scenario: Pickup pays off
- **WHEN** Rico Dowdle, picked up in week 3, passes +1.0 WAR for the team in week 7
- **THEN** a pickup-pays-off story appears in week 7, and not again when he passes +2.0

### Requirement: 4.7.13 Got away stories
A story SHALL appear once when a dropped Player's departed window passes +1.0 WAR, naming the team he plays for.

**Traces to:** 4.7; 4.5.8.1
**Verified by:** Test: `tests/test_news.py::test_got_away_names_the_team_he_plays_for`

#### Scenario: Got away
- **WHEN** a dropped receiver passes +1.0 WAR for KingDso
- **THEN** a got-away story names him and KingDso

### Requirement: 4.7.14 Outbid stories
An outbid story SHALL appear for a lost waiver bid of at least 20% of the season budget, or of at least 5% lost by $3 or less or on waiver priority, naming the Player, the winner and both bids.

**Traces to:** 4.7; 4.5.11
**Verified by:** Test: `tests/test_news.py::test_outbid_big_close_tied_and_small`

#### Scenario: Big outbid
- **WHEN** a Manager's $40 bid on Bucky Irving loses to KingDso's $55 in a $100 league
- **THEN** an outbid story says the $40 lost to KingDso's $55

#### Scenario: Small loss
- **WHEN** a Manager's $2 bid loses to a $4 bid in a $100 league
- **THEN** no outbid story appears

### Requirement: 4.7.15 Moves stories per week
At most three Moves stories per week per team SHALL be kept, counted apart from the Player stories.

**Rationale:** A busy trade week cannot push out injury news.
**Traces to:** 4.7
**Verified by:** Test: `tests/test_news.py::test_moves_stories_have_their_own_cap`

#### Scenario: Busy trade week
- **WHEN** a dynasty Manager makes four trades in one week and a starter is ruled out
- **THEN** three trade stories and the injury story appear

### Requirement: 4.7.16 Editable templates
Every headline and story sentence SHALL come from a template with a copy ID in `site-copy.txt` and named placeholders for the data, so that the maintainer can reword any story type through the site-copy workflow.

**Traces to:** 4.7; 10
**Verified by:** Test: `tests/test_site_copy.py::test_real_site_text_is_all_covered`

#### Scenario: Reworded template
- **WHEN** the maintainer edits the result headline template and applies it
- **THEN** every result story uses the new wording at the next export

### Requirement: 4.7.17 Story order
Stories SHALL be ordered newest first, each carrying its time, category and a link to the page its data comes from.

**Traces to:** 4.7; 4.4.8
**Verified by:** Test: `tests/test_news.py::test_week_dates_follow_labor_day`; Test: `tests/test_news.py::test_record_beats_result_for_the_feature_and_player_stories_are_capped`

#### Scenario: Two weeks of stories
- **WHEN** a Manager has stories from weeks 10 and 11
- **THEN** the week-11 stories come first

### Requirement: 4.7.17.1 Feature story
The feature story SHALL be the latest week's result unless a record, or a forecast move of 20 points or more, outranks it.

**Traces to:** 4.7.17
**Verified by:** Test: `tests/test_news.py::test_record_beats_result_for_the_feature_and_player_stories_are_capped`

#### Scenario: Record beats result
- **WHEN** the latest week has a result and a new league-high score
- **THEN** the feature story is the record

### Requirement: 4.7.18 Retired Managers' news
A retired Manager's news SHALL show their last season's stories, ending with a final-season story.

**Traces to:** 4.7
**Verified by:** Test: `tests/test_news.py::test_retired_manager_ends_with_the_final_season`

#### Scenario: Retired
- **WHEN** TateFM's dynasty page is shown
- **THEN** the news card shows his 2023 stories

### Requirement: 4.7.19 Trending adds saved
Each cold run SHALL save Sleeper's trending adds, the most-added Players over the last 24 hours, with the time saved.

**Traces to:** 4.7; 4.7.7; 6
**Verified by:** Test: `tests/test_player_details.py::test_trending_saved_with_the_time`

#### Scenario: Cold run
- **WHEN** a cold run happens
- **THEN** the trending adds are saved with the time

### Requirement: 4.7.19.1 Trending failure
A failed trending fetch SHALL skip that step with a warning while the rest of the cold run completes.

**Traces to:** 4.7.19; 5
**Verified by:** Test: `tests/test_refresh.py::test_refresh_continues_past_a_trending_failure_with_a_warning`

#### Scenario: Sleeper unreachable
- **WHEN** the trending request fails during a cold run
- **THEN** the run completes, logs a warning, and no trending stories are added for that run
