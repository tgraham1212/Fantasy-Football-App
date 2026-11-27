## RENAMED Requirements

- FROM: `### Requirement: 4.8.1 Games that matter`
- TO: `### Requirement: 4.8.1 Meaningful Games`

## MODIFIED Requirements

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

### Requirement: 4.8.4.1 Playoff record
A Manager's playoff record SHALL count their winners-bracket Meaningful Games, the 3rd place game included.

**Traces to:** 4.8.4; 4.8.1
**Verified by:** Test: `tests/test_league_records.py::test_all_time_standings_example`

#### Scenario: Lost the semi-final
- **WHEN** a Manager won a quarter-final, lost the semi-final and won the 3rd place game
- **THEN** that season adds 2-1 to their playoff record

### Requirement: 4.8.6.2 Streaks
A streak SHALL count consecutive wins or consecutive losses in Meaningful Games within one season.

**Traces to:** 4.8.6; 4.8.1
**Verified by:** Test: `tests/test_league_records.py::test_streaks_count_meaningful_games`

#### Scenario: Toilet bowl losses
- **WHEN** a team ends the regular season on 9 losses and loses its two toilet bowl games
- **THEN** its losing streak is 11

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
