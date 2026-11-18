## MODIFIED Requirements

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

### Requirement: Positional rankings file contents
Each season file SHALL hold the weeks covered, the last final week, and the per-position replacement levels and axis ranges. Per manager, it SHALL hold the owner's name, user id and roster id with their players. Each player entry SHALL hold the Sleeper id, name, position, NFL team, points per game, games played, games projected, the taxi and injured flags, and the out status (or none).

#### Scenario: Player entry
- **WHEN** the dynasty 2026 file is read
- **THEN** each player carries his points per game with the played and projected game counts behind it, and his taxi and injured flags with his out status
