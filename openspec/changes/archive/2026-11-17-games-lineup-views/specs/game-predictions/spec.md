# Spec Delta

## ADDED Requirements

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
