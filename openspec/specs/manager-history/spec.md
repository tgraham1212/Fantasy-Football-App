# manager-history Specification

## Purpose

The per-Manager figures behind the Managers sub-tab: identity across seasons, finishes and honours, head to head, records, luck, rivals, best Players, Player move windows, moves from transactions and waiver overpay, computed from stored league data and exported for the site. It serves need 4, Manager History, through `manager-pages`; the formulas are in `Calculations.txt`, sections 19 and 21.

## Requirements

### Requirement: 4.5 Manager identity
A Manager SHALL be identified by Sleeper user id across seasons, a vacant roster counting as the Manager who held it before, and shown under their latest display name.

**Rationale:** Calculations.txt section 19.
**Traces to:** 4; 4.4
**Verified by:** Test: `tests/test_vacant_owner.py::test_owner_quit_before_the_year_ended`; Inspection: `src/ffapp/managers.py`, the name comes from the latest season's users

#### Scenario: Renamed account
- **WHEN** the account shown as SpookyCast in 2021 is shown as Jdeguire from 2022
- **THEN** it is one Manager, listed as Jdeguire, with seasons from 2021

### Requirement: 4.5.1 Current and retired
A Manager SHALL be current when they hold a roster in the current season and retired otherwise, with their first and last seasons recorded.

**Traces to:** 4.5
**Verified by:** Test: `tests/test_managers.py::test_dynasty_retired_managers`

#### Scenario: Manager who left
- **WHEN** Hildebrand009 held a dynasty roster in 2022 and none since
- **THEN** Hildebrand009 is listed as retired with seasons 2022–2022

### Requirement: 4.5.2 Final places
Each completed season's final places SHALL come from the stored winners and losers brackets.

**Traces to:** 4.5
**Verified by:** Test: `tests/test_managers.py::test_dynasty_champions_and_runners_up_match_league_history`; Test: `tests/test_managers.py::test_incomplete_brackets_give_no_places`

#### Scenario: 2025 dynasty
- **WHEN** the 2025 dynasty brackets are stored
- **THEN** corygraham12 finishes 1st and Z28kid86 2nd

### Requirement: 4.5.2.1 Toilet bowl place
In a toilet-bowl league, the toilet bowl champion, the team that loses its final, SHALL finish last, and a consolation league's consolation winner 7th.

**Traces to:** 4.5.2
**Verified by:** Test: `tests/test_managers.py::test_toilet_bowl_winner_is_last_place`; Test: `tests/test_managers.py::test_consolation_winner_is_seventh`

#### Scenario: Toilet bowl champion
- **WHEN** a redraft team loses the toilet bowl final
- **THEN** its finish is last

### Requirement: 4.5.3 Honours
Honours SHALL list the years a Manager was champion, runner-up, first after the regular season, top in points for, in the playoffs, and, in a toilet-bowl league, toilet bowl champion.

**Traces to:** 4.5; 4.5.2; 4.4.7.1
**Verified by:** Test: `tests/test_managers.py::test_dynasty_champions_and_runners_up_match_league_history`; Inspection: each dynasty Manager's Honours against Sleeper's league history

#### Scenario: Dynasty
- **WHEN** the league's losers bracket is a consolation bracket
- **THEN** no toilet bowl honour is shown

### Requirement: 4.5.4 Head to head
For each opponent, head to head SHALL give regular-season and playoff wins, losses and ties, points for and against, and the most recent result, over every season both Managers played.

**Traces to:** 4.5; 4.4.7.2
**Verified by:** Test: `tests/test_managers.py::test_head_to_head_counts_regular_and_playoff_games`

#### Scenario: Last meeting
- **WHEN** tg1212 last beat djernberg 114.9 to 98.2 in week 10
- **THEN** the djernberg row shows that result

### Requirement: 4.5.5 Records
Each Manager's records SHALL come from regular-season and playoff games: highest and lowest score, biggest win and loss, closest loss, longest winning and losing streaks, most points in a season, and the rivalry-week record.

**Traces to:** 4.5; 4.4.7.3
**Verified by:** Test: `tests/test_managers.py::test_records_rank_against_every_game_in_league_history`; Test: `tests/test_managers.py::test_rivalry_week_record_follows_the_roster`

#### Scenario: Highest score
- **WHEN** a Manager's best week was 182.4
- **THEN** their highest-score record is 182.4 with its season and week

### Requirement: 4.5.5.1 All-time ranks
Each record SHALL be ranked against every Manager's equivalent across league history, ties sharing the better rank, with ranks 1 to 3 exported.

**Traces to:** 4.5.5; 4.4.7.3.1
**Verified by:** Test: `tests/test_managers.py::test_records_rank_against_every_game_in_league_history`; Test: `tests/test_managers.py::test_ties_share_the_better_rank`

#### Scenario: Second-best ever
- **WHEN** a Manager's biggest win is the league's second biggest ever
- **THEN** the record is exported with rank 2

### Requirement: 4.5.6 Luck figures
For each Manager, the export SHALL give the all-play record, wins above all-play pace, points against per game against the league average, and points left on the bench.

**Traces to:** 4.5; 4.4.7.1
**Verified by:** Test: `tests/test_managers.py::test_all_play_and_luck`; Inspection: `src/ffapp/managers.py`, points against per game beside the league average

#### Scenario: All-play pace
- **WHEN** a Manager won 2 of 3 regular-season games against an all-play pace of 7/9 × 3 = 2.33
- **THEN** their wins above pace are -0.33

### Requirement: 4.5.6.1 Points left on the bench
Points left on the bench SHALL be the sum over seasons of Sleeper's potential points minus actual points.

**Traces to:** 4.5.6
**Verified by:** Test: `tests/test_managers.py::test_bench_points_example`

#### Scenario: Bench points
- **WHEN** a team's 2025 potential points are 1,610.46 and its points are 1,497.00
- **THEN** 2025 adds 113.46 to points left on the bench

### Requirement: 4.5.7 Rivals from the configuration
Redraft rivals SHALL be read from the league configuration as pairs of rosters with each season's rivalry week, so that a rivalry follows the team when its Manager changes.

**Traces to:** 4.5; 4.4.4.1
**Verified by:** Test: `tests/test_config.py::test_repo_redraft_rivals_follow_the_team`; Test: `tests/test_managers.py::test_rivalry_week_record_follows_the_roster`

#### Scenario: Rival follows the team
- **WHEN** roster 8's Manager changes between seasons
- **THEN** roster 8's new Manager inherits its rival, khar432

### Requirement: 4.5.7.1 Nemesis as rival
In a league without a rivals table, the rival SHALL be the nemesis: the opponent with the worst head-to-head record against the Manager over at least 4 games, ties broken by the larger points deficit, or "–" when none has 4 games.

**Traces to:** 4.5.7
**Verified by:** Test: `tests/test_managers.py::test_nemesis_needs_four_games_and_breaks_ties_by_deficit`

#### Scenario: Dynasty nemesis
- **WHEN** a dynasty Manager is 1-5 against one opponent and no worse against any other with 4 or more games
- **THEN** that opponent is the rival

### Requirement: 4.5.8 Player move windows
A Player's time with a team SHALL be read from the weekly matchup rosters as windows: an added window from the week he joins until he leaves, and a departed window from the week he leaves until he returns or the latest week.

**Rationale:** Calculations.txt section 21.
**Traces to:** 4.5; 3.3
**Verified by:** Test: `tests/test_managers.py::test_dropped_twice_gives_two_departed_windows_and_one_added`

#### Scenario: Dropped twice
- **WHEN** a Player is dropped in week 3, picked up again in week 7 and dropped again in week 12
- **THEN** there are two departed windows (weeks 3–6 and 12 on) and one added window (weeks 7–11)

### Requirement: 4.5.8.1 Window WAR
Each window SHALL sum the Player's WAR over its weeks, whichever roster he was on, if any.

**Traces to:** 4.5.8
**Verified by:** Test: `tests/test_managers.py::test_dropped_twice_gives_two_departed_windows_and_one_added`

#### Scenario: Free agent weeks
- **WHEN** a dropped Player sat unrostered for two weeks and scored for another team after
- **THEN** his departed window sums his WAR over all those weeks

### Requirement: 4.5.8.2 Windows across seasons
Windows SHALL end with their season in redraft and carry across seasons in dynasty.

**Traces to:** 4.5.8
**Verified by:** Test: `tests/test_managers.py::test_redraft_windows_end_with_the_season`; Test: `tests/test_managers.py::test_dynasty_windows_carry_over`

#### Scenario: Dynasty keeper
- **WHEN** a dynasty Player added in 2024 stays on the team through 2026
- **THEN** his added window runs from 2024 through 2026

### Requirement: 4.5.9 Best players
Best Player All-Time SHALL be the Player with the most WAR in weeks on the Manager's team across all seasons, shown with his WAR and seasons on the team.

**Traces to:** 4.5; 4.4.4
**Verified by:** Inspection: `src/ffapp/managers.py`, the best-player and most-seasons picks in the Players block

#### Scenario: Long-time starter
- **WHEN** a quarterback earned 6.2 WAR over four seasons on a team, more than any other Player
- **THEN** he is that team's Best Player All-Time with 6.2 WAR and 4 seasons

### Requirement: 4.5.9.1 The one that got away
"The one that got away" SHALL be the Player with the most WAR in a single departed window, among windows starting in the latest season in redraft and across the whole team history in dynasty.

**Traces to:** 4.5.9; 4.4.9.4
**Verified by:** Test: `tests/test_managers.py::test_redraft_got_away_counts_only_the_latest_season`

#### Scenario: Got away
- **WHEN** a Player produced +4.1 WAR elsewhere after the Manager dropped him and never returned
- **THEN** he is the one that got away if no departed window is larger

### Requirement: 4.5.9.2 Most seasons on the team
"Most seasons on this team" SHALL name the Player with the most seasons having at least one week on the Manager's roster.

**Traces to:** 4.5.9; 4.4.9.4
**Verified by:** Inspection: `src/ffapp/managers.py`, the most-seasons pick counts seasons with a week on the roster

#### Scenario: Long-time backup
- **WHEN** a kicker spent at least one week on a team in each of five seasons
- **THEN** he is named with 5 seasons unless another Player has more

### Requirement: 4.5.10 Moves from transactions
Each completed waiver, free-agent and commissioner transaction SHALL give one added or dropped row per Player for the Managers involved, with how it happened and its week.

**Traces to:** 4.5; 4.4.10
**Verified by:** Test: `tests/test_moves.py::test_add_and_drop_in_one_move_and_claimed_by`

#### Scenario: Add and drop in one move
- **WHEN** a Manager picks up Tyler Bass and drops Kenny Coleman in one free-agent move in week 2
- **THEN** Bass is an added row and Coleman a dropped row, both "Free agent" in week 2

### Requirement: 4.5.10.1 Drafted Players
Moves SHALL come only from transactions, so that drafted Players have no move rows.

**Traces to:** 4.5.10
**Verified by:** Inspection: `src/ffapp/moves.py`, moves are built only from stored transactions

#### Scenario: First-round pick
- **WHEN** a Manager drafts a running back
- **THEN** he has no added row

### Requirement: 4.5.10.2 Trades in moves
A trade SHALL give one trade entry per side, naming the other Manager and the week and listing the Players, picks (season and round) and FAAB each side got and gave, with its Players kept out of the added and dropped rows.

**Traces to:** 4.5.10; 4.4.10.4
**Verified by:** Test: `tests/test_moves.py::test_trade_with_pick_and_faab_never_repeats_as_rows`

#### Scenario: Trade with a pick and FAAB
- **WHEN** a Manager trades T. Etienne Jr. and $5 FAAB to KingDso for J. Smith-Njigba and KingDso's 2027 2nd-round pick
- **THEN** the trade lists Got: J. Smith-Njigba and "2027 2nd"; Gave: T. Etienne Jr. and "$5 FAAB", and neither Player has an added or dropped row

### Requirement: 4.5.10.3 WAR of a move
Each added Player, and each Player got in a trade, SHALL carry the WAR of the added window starting in the move's week, and each dropped or traded-away Player that of the departed window starting then.

**Traces to:** 4.5.10; 4.5.8.1
**Verified by:** Test: `tests/test_moves.py::test_add_and_drop_in_one_move_and_claimed_by`; Test: `tests/test_moves.py::test_dynasty_trade_window_across_seasons`

#### Scenario: Dynasty trade
- **WHEN** a dynasty Player got in a 2024 trade stays on the team through 2026
- **THEN** the trade's WAR for him covers every week from the trade through 2026

### Requirement: 4.5.10.3.1 Offseason moves
An offseason move's window SHALL start in week 1 of the next season.

**Traces to:** 4.5.10.3
**Verified by:** Inspection: `src/ffapp/moves.py`, an offseason move's week maps to week 1 of the next season

#### Scenario: Offseason trade
- **WHEN** a dynasty trade happens in March
- **THEN** its window starts in week 1 of that autumn's season

### Requirement: 4.5.10.3.2 No games
A Player who played no game inside the window SHALL be marked as having no games in place of a WAR, or as pending while no week after the move has been scored.

**Traces to:** 4.5.10.3
**Verified by:** Test: `tests/test_moves.py::test_no_games_and_pending`

#### Scenario: Picked up and dropped before playing
- **WHEN** a Player is added in week 5 and dropped in week 6 before his next game
- **THEN** his added row is marked as having no games

#### Scenario: Picked up this week
- **WHEN** a Player is added in week 11 before any week-11 game has been scored
- **THEN** his row is marked pending ("no games yet")

### Requirement: 4.5.11 Waiver overpay
A won waiver claim's overpay SHALL be its bid minus the highest failed bid for the same Player in the same waiver run, the whole bid when no other claim was made, and none, marked as tied, when the highest failed bid equals it.

**Traces to:** 4.5; 4.5.10; 4.4.10.2
**Verified by:** Test: `tests/test_moves.py::test_overpay_contested_uncontested_tie_and_other_runs`; Test: `tests/test_moves.py::test_higher_failed_bid_lost_for_another_reason_is_ignored`

#### Scenario: Contested claim
- **WHEN** a Manager wins Rico Dowdle for $41 and the next bid in that run was $12
- **THEN** the row shows an overpay of $29

#### Scenario: Tie
- **WHEN** two Managers bid $22 and the winner had the better waiver priority
- **THEN** the row reads "tied" with no overpay

### Requirement: 4.5.11.1 Season FAAB figures
Each season SHALL total a Manager's FAAB spent and overpay, against the budget, and give their biggest winning bid with the Player and week.

**Traces to:** 4.5.11; 4.4.9.3
**Verified by:** Test: `tests/test_moves.py::test_faab_biggest_bid_and_overpaid_total`; Test: `tests/test_managers.py::test_faab_by_season_reads_budget_and_used`

#### Scenario: Season meter
- **WHEN** a Manager won bids of $41, $12 and $22 in 2026
- **THEN** 2026's biggest bid is the $41 with its Player and week

### Requirement: 4.5.12 Manager file exported
The export SHALL write one Managers file per league holding everything the Managers sub-tab draws for every current and retired Manager.

**Traces to:** 4.5; 4.4
**Verified by:** Test: `tests/test_export.py::test_export_writes_the_managers_file_with_every_manager`

#### Scenario: File present
- **WHEN** the site is exported
- **THEN** `site/data/<league>/managers.json` exists and lists every current and retired Manager, with their moves and WAR for every season they played
