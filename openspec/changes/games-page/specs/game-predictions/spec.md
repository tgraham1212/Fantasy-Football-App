# Spec Delta

## Purpose

Per-game forecasts from the playoff-odds simulation, the projected playoff bracket, a log of how each game's forecast moved before kickoff, and the prediction of record each finished game is judged against.

## ADDED Requirements

### Requirement: Game forecasts
For every week the simulation plays, the stored result SHALL include, per game, each team's mean simulated score, a histogram of its simulated scores in 2-point bins, each team's win probability, and each team's model lineup with every slot's player, position and projected points. A slot filled at replacement level SHALL be marked as a free-agent fill.

#### Scenario: Regular-season game
- **WHEN** the simulation runs as of week 9
- **THEN** the stored result lists every week-10 to week-14 game with both teams' mean score, histogram, win probability and lineup

#### Scenario: Replacement fill
- **WHEN** the model fills a team's TE slot with the replacement level of 6.4
- **THEN** that slot is stored as a free-agent TE fill projected at 6.4

### Requirement: Projected playoff bracket
For playoff weeks whose pairings Sleeper has not set, the system SHALL project the bracket the league plays: seeds by expected seed from the simulations, pairings by the league's bracket rules, and the team with the higher win probability advancing from each projected game. Each projected game SHALL carry how often that pairing occurred across the simulations. Only the winners bracket and, for toilet-bowl leagues, the toilet bowl SHALL be projected.

#### Scenario: Semifinal projection
- **WHEN** seed 3 is favoured over seed 6 in the projected first round
- **THEN** the projected semifinal pairs seed 3 with the seed the bracket rules send it to, with its win probability and the share of simulations in which that semifinal occurred

#### Scenario: Consolation league
- **WHEN** a league plays a consolation bracket rather than a toilet bowl
- **THEN** only its winners-bracket games are projected

### Requirement: Real playoff pairings
Once Sleeper sets a playoff week's pairings, that week's games SHALL be the real ones, forecast like regular-season games, and no projected games SHALL be shown for it.

#### Scenario: Pairings set
- **WHEN** Sleeper has set the week-15 pairings
- **THEN** week 15 shows those real games and no projected ones

### Requirement: Projection log
Each refresh run SHALL append, for each game of the current week and every later week of the season, an entry holding the run time, each team's model lineup and win probability, and every rostered player's projected points with whether his NFL game has kicked off. An entry SHALL be appended only when a lineup, projection, kickoff state or win probability differs from the game's previous entry. A player's projection SHALL stop updating at his kickoff.

#### Scenario: Weekend runs
- **WHEN** the refresh runs Thursday, Saturday and Sunday morning during week 11 and projections change between each run
- **THEN** each week-11 game has three log entries, and players whose games had kicked off keep their last pre-kickoff projection in the later entries

#### Scenario: Nothing changed
- **WHEN** a run produces the same lineups, projections, kickoff states and win probabilities as the previous entry
- **THEN** no entry is appended

### Requirement: Prediction of record
Once a week is final, each game's prediction of record SHALL be simulated from the lineup each manager actually started, each player at his last logged projection before kickoff, using the same model as the forecasts. A starter never logged before his kickoff SHALL use his stored projection for that week. The record SHALL include the same fields as a game forecast.

#### Scenario: News before Sunday
- **WHEN** a Sunday starter's projection drops from 14 to 2 on Saturday after he is ruled out, and Thursday starters locked at their Thursday projections
- **THEN** the record uses 2 for the Sunday starter and the Thursday projections for the Thursday starters

#### Scenario: Manager starts an unexpected player
- **WHEN** a manager starts a player the model's lineup never included
- **THEN** the record uses that player in that slot at his last logged pre-kickoff projection

### Requirement: Weeks before the log
For a finished week with no log entries, the prediction of record SHALL be the game forecast from the simulation run as of the week before it, marked as a pre-week forecast.

#### Scenario: Early 2026 weeks
- **WHEN** week 6 of 2026 finished before the log existed
- **THEN** its games show the as-of-week-5 forecast, labelled as a pre-week forecast

### Requirement: Game files stored
The system SHALL write, per league, season and week, the log entries, the latest forecast and, once the week is final, the prediction of record with each team's actual score and the winner. Re-running on unchanged data SHALL not add log entries or change the record.

#### Scenario: Re-run without news
- **WHEN** the games step runs twice with no new projections and no new runs of the simulation
- **THEN** the second run leaves the week files unchanged
