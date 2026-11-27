# league-records Specification

## Purpose

The league-wide league records behind the League sub-tab's Records page: champions, all-time standings, weekly and season league records, and Player league records, computed from stored league data with their ranking, tie and eligibility rules, and exported for the site. It serves need 4, Manager History, and need 3, Player Value, through `league-records-page`; the formulas are in `Calculations.txt`.

## Requirements

### Requirement: 4.8 League records export
The export SHALL write one league records file per league, holding every league record the Records page draws, computed from stored league data.

**Traces to:** 4
**Verified by:** Test: `tests/test_league_records.py::test_export_writes_league_records`

#### Scenario: Build
- **WHEN** `python -m ffapp build` runs
- **THEN** each configured league has a league records file in the site data

### Requirement: 4.8.1 Meaningful Games
League records built from games SHALL count only Meaningful Games: regular-season games, winners-bracket games on the path to the championship, the championship, the 3rd place game and, in a toilet-bowl league, the toilet bowl games on the path to its final and that final.

**Rationale:** Consolation and other placement games decide nothing, and lineups in them are often weaker.
**Traces to:** 4.8
**Verified by:** Test: `tests/test_league_records.py::test_only_meaningful_games_count`

#### Scenario: Placement game
- **WHEN** two teams play the 5th place game with a 190-point score
- **THEN** the score is in no league record

#### Scenario: Toilet bowl final
- **WHEN** the redraft toilet bowl final ends 147.00 to 62.40
- **THEN** its 84.60 margin counts for Biggest Blowout

### Requirement: 4.8.2 Ranking and ties
Each league record SHALL list its top 25 entries, equal values sharing a rank and listed oldest first, so that the oldest holds the league record.

**Traces to:** 4.8
**Verified by:** Test: `tests/test_league_records.py::test_ties_share_a_rank_oldest_first`

#### Scenario: Equal scores
- **WHEN** a 2024 and a 2025 game both have a 49.90 Player score in 4th place
- **THEN** both rank 4, the 2024 game first

### Requirement: 4.8.3 Champions
For each finished season, the export SHALL give the champion, runner-up and toilet bowl champion (in a league without a toilet bowl, the team last in the regular-season standings), the champion's regular-season record and points, and the champion's best Player by WAR in his weeks on that roster.

**Traces to:** 4.8; 4.5.2
**Verified by:** Test: `tests/test_league_records.py::test_champions_list_finished_seasons`

#### Scenario: Dynasty season
- **WHEN** the dynasty league's 2024 season is final
- **THEN** its entry gives the champion, runner-up and last place, the champion's 12-2 record and points, and its best Player by WAR

#### Scenario: Last place won consolation games
- **WHEN** a dynasty team went 2-12, last in the standings, and won two consolation games
- **THEN** it is that season's last place

### Requirement: 4.8.3.1 Finished seasons only
A season SHALL appear in Champions once its final has been played.

**Traces to:** 4.8.3
**Verified by:** Test: `tests/test_league_records.py::test_champions_list_finished_seasons`

#### Scenario: Season under way
- **WHEN** the current season is in week 12
- **THEN** Champions has no entry for it

### Requirement: 4.8.4 All-time standings
For each Manager, the export SHALL give regular-season wins, losses, ties, win % and point differential, playoff appearances and playoff record, and finishes in 1st, 2nd and 3rd and as toilet bowl champion or last place.

**Traces to:** 4.8; 4.5.2
**Verified by:** Test: `tests/test_league_records.py::test_all_time_standings_example`

#### Scenario: Six seasons
- **WHEN** a Manager went 56-24 in six regular seasons, scoring 861.7 more points than they allowed
- **THEN** their entry gives 56-24, .700 and +861.7

### Requirement: 4.8.4.1 Playoff record
A Manager's playoff record SHALL count their winners-bracket Meaningful Games, the 3rd place game included.

**Traces to:** 4.8.4; 4.8.1
**Verified by:** Test: `tests/test_league_records.py::test_all_time_standings_example`

#### Scenario: Lost the semi-final
- **WHEN** a Manager won a quarter-final, lost the semi-final and won the 3rd place game
- **THEN** that season adds 2-1 to their playoff record

### Requirement: 4.8.4.2 Standings order
All-time standings SHALL put current Managers before former Managers, each group ordered by win %, a tie going to the larger point differential.

**Traces to:** 4.8.4
**Verified by:** Test: `tests/test_league_records.py::test_standings_order`

#### Scenario: Three Managers on .513
- **WHEN** three current Managers have a .513 win % with point differentials of +320.9, +83.6 and -55.2
- **THEN** they are listed in that order

### Requirement: 4.8.5 Weekly records
The export SHALL give eight weekly league records: highest and lowest team score, highest and lowest matchup score, biggest blowout, closest game, highest score in a loss and lowest score in a win.

**Traces to:** 4.8; 4.8.1
**Verified by:** Test: `tests/test_league_records.py::test_weekly_records_example`

#### Scenario: Highest team score
- **WHEN** a team scored 202.42 in 2023 week 3, the league's highest score in a game that matters
- **THEN** it is first in Highest Team Score

### Requirement: 4.8.5.1 Margin records credit the winner
Biggest blowout and closest game SHALL list each game once, under its winner.

**Traces to:** 4.8.5
**Verified by:** Test: `tests/test_league_records.py::test_weekly_records_example`

#### Scenario: One entry per game
- **WHEN** a game ends 193.74 to 88.28
- **THEN** Biggest Blowout has one 105.46 entry, held by the winner

### Requirement: 4.8.5.2 Game kind
Each weekly entry SHALL carry its game's kind (regular season, Playoffs, Championship, 3rd Place, Toilet Bowl or Toilet Bowl Final) and whether it is from the current season.

**Traces to:** 4.8.5; 4.8.1
**Verified by:** Test: `tests/test_league_records.py::test_weekly_records_example`

#### Scenario: Toilet bowl final
- **WHEN** an entry comes from the 2022 toilet bowl final
- **THEN** its kind is Toilet Bowl Final

### Requirement: 4.8.6 Season records
The export SHALL give fourteen season league records over every Manager-season: most and fewest points, most points against, best and worst record, best team to miss and worst team to make the playoffs, luckiest and unluckiest season, longest winning and losing streak, most bench points, and most points gained and lost by lineup choices.

**Traces to:** 4.8
**Verified by:** Test: `tests/test_league_records.py::test_season_records_example`

#### Scenario: Most points
- **WHEN** a Manager scored 1,821.24 regular-season points in 2021, the most in league history
- **THEN** they hold Most Points

### Requirement: 4.8.6.1 Regular season basis
Season league records other than streaks SHALL use regular-season games only.

**Traces to:** 4.8.6
**Verified by:** Test: `tests/test_league_records.py::test_season_records_example`

#### Scenario: Playoff points
- **WHEN** a Manager scores 150 points in a playoff game
- **THEN** their Most Points total is unchanged

### Requirement: 4.8.6.2 Streaks
A streak SHALL count consecutive wins or consecutive losses in Meaningful Games within one season.

**Traces to:** 4.8.6; 4.8.1
**Verified by:** Test: `tests/test_league_records.py::test_streaks_count_meaningful_games`

#### Scenario: Toilet bowl losses
- **WHEN** a team ends the regular season on 9 losses and loses its two toilet bowl games
- **THEN** its losing streak is 11

### Requirement: 4.8.6.3 Luck
A Manager-season's luck SHALL be its actual wins minus its all-play wins, where each week's score earns the share of the other teams it beat, a tie counting half.

**Rationale:** The same all-play measure as Managers > History; Calculations.txt section 19.
**Traces to:** 4.8.6; 4.5.6
**Verified by:** Test: `tests/test_league_records.py::test_luck_example`

#### Scenario: Eight of eleven
- **WHEN** a team's score beats 8 of the 11 other teams in a week it won
- **THEN** that week adds 1 - 8/11 to its luck

### Requirement: 4.8.6.4 Current season eligibility
Until it ends, the current season SHALL be left out of Fewest Points, Worst Record, Best Team to Miss Playoffs and Worst Team to Make Playoffs, its entries in the other season league records marked as the current season.

**Rationale:** A part-season would otherwise hold the fewest and worst records, and its playoff line is not yet drawn.
**Traces to:** 4.8.6
**Verified by:** Test: `tests/test_league_records.py::test_current_season_eligibility`

#### Scenario: Fewest points in week 12
- **WHEN** a team has 1,100 points after 11 weeks of the current season
- **THEN** it is not in Fewest Points

### Requirement: 4.8.6.5 Season result
Each season entry SHALL give the season's result: 1st, 2nd, 3rd, Playoffs, Missed Playoffs, Toilet Bowl Champ (or Last in a league without a toilet bowl), or In progress for the current season.

**Traces to:** 4.8.6; 4.5.2
**Verified by:** Test: `tests/test_league_records.py::test_season_records_example`

#### Scenario: Missed the playoffs and won the toilet bowl
- **WHEN** a redraft team missed the playoffs and lost the toilet bowl final
- **THEN** its result is Toilet Bowl Champ

#### Scenario: Worst record in a consolation league
- **WHEN** a dynasty team went 2-12, last in the standings, and won two consolation games
- **THEN** its result is Last

### Requirement: 3.6 Player league records
The export SHALL give four Player league records per league (best games, best bench games, career scoring and championships), each available for every position and for all positions together.

**Traces to:** 3; 4.8
**Verified by:** Test: `tests/test_league_records.py::test_player_records_example`

#### Scenario: Running backs
- **WHEN** the Records page asks for RB best games
- **THEN** the export has the 25 best RB games

### Requirement: 3.6.1 Any roster status
Best games and career scoring SHALL count every Player's league-scored points in each week of the league's seasons, whether he started, sat on a bench or was a free agent.

**Traces to:** 3.6
**Verified by:** Test: `tests/test_league_records.py::test_player_records_example`

#### Scenario: Free agent
- **WHEN** an unrostered Player scores 49.30 in 2023 week 3
- **THEN** the game is in Best Games, its Manager shown as free agent

### Requirement: 3.6.2 Bench games
Best bench games SHALL count only weeks in which the Player was on a Manager's roster and not among its starters.

**Traces to:** 3.6
**Verified by:** Test: `tests/test_league_records.py::test_player_records_example`

#### Scenario: Benched
- **WHEN** a Player scores 36.00 on a Manager's bench
- **THEN** the game is in Best Bench Games under that Manager

### Requirement: 3.6.3 Championships
A Player SHALL earn one championship for each title game in which he was on the champion's roster, bench, IR and taxi squad included.

**Traces to:** 3.6; 4.8.3
**Verified by:** Test: `tests/test_league_records.py::test_championships_count_the_whole_roster`

#### Scenario: On the bench
- **WHEN** a Player sat on the champion's bench in the title game
- **THEN** he earns that championship

### Requirement: 3.6.3.1 Championship order
Players with equal championships SHALL be ordered by their WAR in their title seasons, highest first.

**Traces to:** 3.6.3
**Verified by:** Test: `tests/test_league_records.py::test_championships_count_the_whole_roster`

#### Scenario: Two titles each
- **WHEN** two Players have two championships, with 4.31 and 3.67 WAR in their title seasons
- **THEN** the Player with 4.31 is listed first

### Requirement: 3.6.4 NFL team at the time
A Player league record entry SHALL give the NFL team the Player played for in that week or season, from the stored weekly stats.

**Traces to:** 3.6; 6.4
**Verified by:** Test: `tests/test_league_records.py::test_player_records_example`

#### Scenario: Traded Player
- **WHEN** a Player's best game came in 2022 for Cincinnati and he now plays for Houston
- **THEN** the entry gives CIN
