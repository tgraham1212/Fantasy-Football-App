## MODIFIED Requirements

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

### Requirement: Game files stored
The system SHALL commit, per league, season and week:
- the log entries;
- once the week is final, the prediction of record, with each team's actual score and the winner.

The latest forecast and the lineup views SHALL be rebuilt by each run and never committed. Re-running on unchanged data SHALL NOT add log entries or change the record.

#### Scenario: Re-run without news
- **WHEN** the games step runs twice with no new projections and no new runs of the simulation
- **THEN** the second run leaves the committed week files unchanged

## ADDED Requirements

### Requirement: Slate forecasts
When a slate goes final, the cold run SHALL store the league forecast as of that moment in the week's slate file, keyed by the slate's kickoff time. A slate's entry SHALL never be overwritten.

#### Scenario: Sunday's slates
- **WHEN** the 1:00 pm, 4:05 pm and Sunday night slates of week 11 go final
- **THEN** week 11's slate file holds three forecasts, one per slate
