# Spec Delta

## MODIFIED Requirements

### Requirement: ELO placeholder columns
The ELO and 1-week ELO change columns SHALL show each team's current manager rating mean, rounded to a whole number, and its signed change over the last rated week. After a season's draft and before its first scored week, the ELO cell SHALL show the preseason (reverted) rating and the change cell SHALL be empty; from week 1 the change is measured from that preseason rating. While no rating data is exported, both columns SHALL render as empty cells. A positive change SHALL render as black text on a green fill, a negative change as black text on a red fill, and no change as an empty cell.

#### Scenario: Before ELO exists
- **WHEN** the exported data carries no ELO values
- **THEN** every ELO and 1-week change cell is empty and the two headers are still shown

#### Scenario: Future ELO change rendering
- **WHEN** the exported data gives a team an ELO of 1676 and a 1-week change of +20
- **THEN** the ELO cell shows "1676" and the change cell shows "+20" as black text on a green fill

#### Scenario: First rated week of a newcomer
- **WHEN** a team's manager has only one rated week
- **THEN** the ELO cell shows their rating and the change cell is empty

#### Scenario: After the draft, before week 1
- **WHEN** a manager ended last season at 1300 and this season's draft is done but no week is scored
- **THEN** the ELO cell shows 1200 and the change cell is empty

#### Scenario: Week 1 change
- **WHEN** the same manager's week-1 rating is 1240
- **THEN** the change cell shows +40

### Requirement: Rating chart
Each league page SHALL show a second line chart, below the odds-over-time chart, with one line per manager who has ever played in the league, plotting the chosen rating series for every stored week since the league's first stored season, including each season's preseason point where one exists. Metric buttons SHALL offer "Rating" (the Openskill rating mean, default) and "Z-score" (the career mean z-score). The x-axis SHALL label season boundaries.

#### Scenario: Default rating chart
- **WHEN** a visitor opens the dynasty page with ratings stored for 2022 through 2026
- **THEN** the chart shows every manager's rating mean at every rated week from 2022 week 1 to the latest rated week, with each season start marked on the axis

#### Scenario: Z-score metric
- **WHEN** a visitor clicks "Z-score"
- **THEN** the chart plots each manager's career mean z-score over the same weeks, with a reference line at zero

#### Scenario: Highlight a manager
- **WHEN** a visitor picks one team in the table or one line in the rating chart
- **THEN** that manager's line keeps full strength in both charts and the others are dimmed

#### Scenario: Preseason point
- **WHEN** a season's draft is done
- **THEN** the chart shows a "Pre" point at that season's start holding each manager's reverted rating, so the step toward 1000 is visible
