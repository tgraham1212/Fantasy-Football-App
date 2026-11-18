# positional-rankings Specification

## Purpose

Per league and season, each manager's rostered players by position with a regular-season points-per-game figure that blends what they have scored with what they are projected to score, plus the roster flags and replacement level the Positional Rankings page draws.

## Requirements

### Requirement: Roster used
For a completed season, each team's players SHALL be those on its final, end-of-season roster. For the season in progress, they SHALL be those on its current roster. Players on the taxi squad and on reserve SHALL be included and marked as taxi or reserve. Only players at a position the league starts SHALL be included.

#### Scenario: Completed season
- **WHEN** positional rankings are built for redraft 2025
- **THEN** each team lists the players on its roster at the end of the 2025 season, including anyone added during the playoffs

#### Scenario: Season in progress
- **WHEN** positional rankings are built for dynasty 2026 in week 11
- **THEN** each team lists its current roster, with taxi players marked as taxi

#### Scenario: No kicker slot
- **WHEN** a dynasty roster holds a kicker and the dynasty league has no K slot
- **THEN** the kicker is not listed

### Requirement: Points per game
A player's points per game SHALL be his actual points in the regular-season weeks he played, plus his projected points for the regular-season weeks not yet final, divided by the number of those played and projected weeks. Points SHALL be scored under the league's rules for that season, and regular-season weeks SHALL be those before the league's playoffs.

#### Scenario: Mid-season blend
- **WHEN** a receiver has scored 120 points in 8 played weeks after week 10, and is projected for 14, 12, 0 (bye) and 13 points in weeks 11 to 14
- **THEN** his points per game is (120 + 14 + 12 + 13) / (8 + 3) = 14.45

#### Scenario: Completed season
- **WHEN** rankings are built for a completed season
- **THEN** every week is final and points per game uses actual points only

### Requirement: Weeks counted
A week SHALL count as played when the player's team played and he has a stat line. A week SHALL count as projected when it is not yet final and his projection for it is above zero. A week whose games are in progress SHALL count as projected until it is final.

#### Scenario: Not yet played
- **WHEN** a rookie has no stat line in weeks 1 to 10 and is projected for 6 points in each of weeks 11 to 14
- **THEN** his points per game is 6.0 from 4 projected weeks

#### Scenario: Live week
- **WHEN** week 11 games are in progress and a quarterback has 12 points so far against a 19-point projection
- **THEN** week 11 counts as a projected week worth 19 points until week 11 is final

### Requirement: Who is rated
A player whose played and projected weeks total zero points SHALL be left out. Points from games he played for another team, or as a free agent, SHALL count, because the figure rates the player and not the manager's results.

#### Scenario: Nothing scored or projected
- **WHEN** a player has played no week and every remaining projection is zero
- **THEN** he is left out

#### Scenario: Traded in
- **WHEN** a running back scored 60 points in 5 weeks for another manager before being traded
- **THEN** those 5 weeks and 60 points count in his points per game on his new manager's row

### Requirement: Injury flag
For the season in progress, a player whose latest stored injury status is on the shared out-status list (Out, Doubtful, IR, PUP, Sus, NA, DNR) SHALL be flagged as injured, and his status SHALL be recorded. Completed seasons SHALL carry no injury flags or statuses.

#### Scenario: Out this week
- **WHEN** a quarterback's latest stored status is Out
- **THEN** he is flagged as injured in the current season's rankings

#### Scenario: Past season
- **WHEN** rankings are built for 2024
- **THEN** no player is flagged as injured

#### Scenario: Doubtful
- **WHEN** a tight end's latest stored status is Doubtful
- **THEN** he is flagged as injured with status Doubtful

#### Scenario: Questionable
- **WHEN** a receiver's latest stored status is Questionable
- **THEN** he is not flagged and carries no status

### Requirement: Replacement level carried
Each league-season's rankings SHALL carry, per position, the replacement level from that league-season's WAR file. When the WAR file is missing, the rankings SHALL be written without replacement levels.

#### Scenario: WAR present
- **WHEN** redraft 2025 rankings are built and the redraft 2025 WAR file says RB replacement level 7.94
- **THEN** the rankings carry 7.94 for RB

#### Scenario: WAR missing
- **WHEN** a league-season has no WAR file
- **THEN** the rankings are written without replacement levels and nothing fails

### Requirement: Positional rankings exported
The site export SHALL write, per league, one positional rankings file per season the league has stored, and an index listing the seasons and the current one. Re-running on unchanged data SHALL give the same files apart from timestamps.

#### Scenario: Files per season
- **WHEN** the export runs with redraft data stored for 2021 to 2026
- **THEN** six redraft positional rankings files and one index are written, the index naming 2026 as current

#### Scenario: Refreshed daily
- **WHEN** the scheduled refresh runs the export
- **THEN** the current season's positional rankings reflect that run's stats, projections, rosters and injury statuses

### Requirement: Positional rankings file contents
Each season file SHALL hold the weeks covered, the last final week, and the per-position replacement levels and axis ranges. Per manager, it SHALL hold the owner's name, user id and roster id with their players. Each player entry SHALL hold the Sleeper id, name, position, NFL team, points per game, games played, games projected, the taxi and injured flags, and the out status (or none).

#### Scenario: Player entry
- **WHEN** the dynasty 2026 file is read
- **THEN** each player carries his points per game with the played and projected game counts behind it, and his taxi and injured flags with his out status

### Requirement: Fixed axis range
A position's axis range SHALL be the same in every season of a league. It SHALL be chosen from all of that league's seasons so that about 99% of player points-per-game values fall inside it, rounded outward to multiples of 5, and it SHALL include zero and the highest replacement level.

#### Scenario: Same axis every season
- **WHEN** the redraft QB axis is 0 to 30 in 2026
- **THEN** it is 0 to 30 in every other redraft season

#### Scenario: Outlier outside the range
- **WHEN** one kicker averaged 31 points from a single game and nearly every other kicker season is under 15
- **THEN** the K axis does not stretch to 31
