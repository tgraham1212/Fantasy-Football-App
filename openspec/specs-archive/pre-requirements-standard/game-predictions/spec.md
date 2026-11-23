# game-predictions Specification

## Purpose

Per-game forecasts from the playoff-odds simulation, the projected playoff bracket, a log of how each game's forecast moved before kickoff, and the prediction of record each finished game is judged against.

## Requirements

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
Each cold run SHALL append an entry for each game of the current week. The entry SHALL hold:
- the run time;
- each team's model lineup and win probability;
- every rostered player's projected points, with whether his NFL game has kicked off.

An entry SHALL be appended only when a lineup, projection, kickoff state or win probability differs from the game's previous entry. A player's projection SHALL stop updating at his kickoff. Later weeks SHALL NOT be logged until they become the current week.

#### Scenario: Weekend runs
- **WHEN** cold runs happen Thursday, Saturday and Sunday morning during week 11 and projections change between each run
- **THEN** each week-11 game has three log entries, and players whose games had kicked off keep their last pre-kickoff projection in the later entries

#### Scenario: Nothing changed
- **WHEN** a run produces the same lineups, projections, kickoff states and win probabilities as the previous entry
- **THEN** no entry is appended

#### Scenario: Next week not logged
- **WHEN** a cold run happens during week 11 while week 12's projections change
- **THEN** week 12's games get no log entries

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
The system SHALL commit, per league, season and week:
- the log entries;
- once the week is final, the prediction of record, with each team's actual score and the winner.

The latest forecast and the lineup views SHALL be rebuilt by each run and never committed. Re-running on unchanged data SHALL NOT add log entries or change the record.

#### Scenario: Re-run without news
- **WHEN** the games step runs twice with no new projections and no new runs of the simulation
- **THEN** the second run leaves the committed week files unchanged

### Requirement: Model and actual lineup views
For every finished week and the live week, each game SHALL be stored in two views. Model: each team's best legal lineup from its roster that week, every player at his last projection before kickoff, with the week's replacement-level floor. Actual: the starters each manager used, at the same projections. Each view SHALL carry its own lineups, means, histogram, win probabilities and margin, simulated with the same model and no results.

#### Scenario: Different picks
- **WHEN** a manager started a receiver projected 6.4 over one projected 6.6
- **THEN** the actual view has the 6.4 receiver in that slot and the model view the 6.6 receiver, each with its own win probability

#### Scenario: Same lineup
- **WHEN** a manager started exactly the model's lineup
- **THEN** both views have the same lineups and probabilities

### Requirement: Live week views
During the live week, the actual view SHALL be the live forecast (locked starters with their results, open slots as the model picks them) and the model view SHALL be the model lineup at frozen pre-kickoff projections with no results.

#### Scenario: Saturday of week 11
- **WHEN** a visitor opens week 11 on Saturday
- **THEN** the actual view shows the live probabilities and the model view the model's pre-kickoff forecast

### Requirement: Rebuilt actual views before the log
For a finished week with no log entries, the model view SHALL be the pre-week forecast and the actual view SHALL be simulated from the real starters at their stored projections for that week, marked as rebuilt.

#### Scenario: Week 10 of 2026
- **WHEN** week 10 finished before the log existed
- **THEN** its model view is the as-of-week-9 forecast and its actual view is rebuilt from the starters each manager used, labelled rebuilt

### Requirement: Lineup choices
For each team in a finished or live game, the system SHALL compute lineup choices: the actual starters' points minus the model lineup's points, where a replacement fill counts the week's realised replacement level for its position. During the live week, both sides SHALL count only players whose games have kicked off, and replacement fills SHALL count once the week is final.

#### Scenario: Better choice
- **WHEN** the manager's starters scored 104.3 and the model lineup's players scored 96.9
- **THEN** the team's lineup choices are +7.4

#### Scenario: Benched the better player
- **WHEN** the model lineup would have scored 12 more points
- **THEN** the team's lineup choices are -12.0

### Requirement: Slate forecasts
When a slate goes final, the cold run SHALL store the league forecast as of that moment in the week's slate file, keyed by the slate's kickoff time. A slate's entry SHALL never be overwritten.

#### Scenario: Sunday's slates
- **WHEN** the 1:00 pm, 4:05 pm and Sunday night slates of week 11 go final
- **THEN** week 11's slate file holds three forecasts, one per slate
