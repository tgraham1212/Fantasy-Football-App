# Spec Delta

## ADDED Requirements

### Requirement: Chart metric buttons
Metric buttons at the top right of the odds-over-time chart SHALL offer the table's four chance columns in the table's order, and the chart SHALL plot the chosen chance (playoffs by default).

#### Scenario: Switch metric
- **WHEN** a visitor clicks the "Bye" metric button
- **THEN** the chart plots each team's first-round-bye chance for every stored as-of week

### Requirement: Team chart colours
Each team's line on the odds-over-time chart SHALL have its own distinct colour, unchanged across weeks, metrics, sorts and highlighting, and the same colour SHALL mark that team's row in the table.

#### Scenario: Colour survives a sort
- **WHEN** a visitor sorts the table by championship chance
- **THEN** every team keeps the line colour and row swatch it had before the sort

### Requirement: Odds chart axis range
The odds-over-time chart's axis floor SHALL be 0 and its top the next multiple of 10 at least 5 points above the highest plotted value, capped at 100.

#### Scenario: Mid-range values
- **WHEN** the highest plotted value is 62%
- **THEN** the axis runs from 0% to 70%

### Requirement: Rating chart
Each league page SHALL show a second line chart, below the odds-over-time chart, with one line per manager who has ever played in the league, plotting the chosen rating series for every rated week since the league's first stored season. Metric buttons SHALL offer "Rating" (the Openskill rating mean, default) and "Z-score" (the career mean z-score). The x-axis SHALL label season boundaries.

#### Scenario: Default rating chart
- **WHEN** a visitor opens the dynasty page with ratings stored for 2022 through 2026
- **THEN** the chart shows every manager's rating mean at every rated week from 2022 week 1 to the latest rated week, with each season start marked on the axis

#### Scenario: Z-score metric
- **WHEN** a visitor clicks "Z-score"
- **THEN** the chart plots each manager's career mean z-score over the same weeks, with a reference line at zero

#### Scenario: Highlight a manager
- **WHEN** a visitor picks one team in the table or one line in the rating chart
- **THEN** that manager's line keeps full strength in both charts and the others are dimmed

### Requirement: Rating chart time range
Range buttons on the rating chart SHALL offer "This season", "Last 3 seasons" and "All time" (default "All time"), and SHALL limit the plotted weeks without changing any manager's colour or the chosen metric. A league with fewer than three stored seasons SHALL show "Last 3 seasons" as the same range as "All time".

#### Scenario: This season
- **WHEN** a visitor on the redraft page picks "This season" during 2026
- **THEN** only 2026's rated weeks are plotted and each line keeps its colour

#### Scenario: Last three seasons
- **WHEN** a visitor picks "Last 3 seasons" on a league with seasons 2021 through 2026
- **THEN** weeks from 2024, 2025 and 2026 are plotted

### Requirement: Manager colours on the rating chart
A current member's line SHALL use the same colour as their team's line on the odds chart and row in the table. Former members SHALL use greys distinct from one another and readable against the chart background in both themes. Vacant rosters SHALL NOT be drawn. Every drawn line SHALL be labelled with the manager's display name at its end.

#### Scenario: Former members
- **WHEN** the dynasty rating chart shows five former members
- **THEN** their five lines are five different greys, none of which matches a current member's colour

#### Scenario: Vacant roster hidden
- **WHEN** a season has a roster with no owner on record
- **THEN** no line is drawn for it, though the other managers' ratings reflect its scores

### Requirement: Rating history exported
Each league's site data SHALL include every manager's rating history (rating mean and career mean z per rated week, with season and week), display name and current or former status, and each current team's latest rating mean and its change over the last rated week. The export SHALL succeed when no rating file exists, leaving the table's ELO cells empty and the rating chart stating that ratings are not yet available.

#### Scenario: Ratings present
- **WHEN** the export runs after the ratings command
- **THEN** each team row carries its ELO and 1-week change and the league file carries the full rating history for current and former managers

#### Scenario: Ratings absent
- **WHEN** the export runs on a store without rating files
- **THEN** the league files are written with empty ELO cells and no rating history, and the page says ratings are not yet available

## MODIFIED Requirements

### Requirement: Odds-over-time chart
Each league page SHALL show a line chart with one line per team, plotting a chosen chance for each stored as-of week of the season.

#### Scenario: Default chart
- **WHEN** a visitor opens a league page with results for as-of weeks 0 through 10
- **THEN** the chart shows each team's playoff chance at weeks 0 through 10

#### Scenario: Metric order
- **WHEN** a visitor views the redraft chart's metric buttons
- **THEN** they read, in order: Avoid Loser's Bye, Make Playoffs, Bye, Win Championship

#### Scenario: Bottom-column metric
- **WHEN** a visitor on the redraft page switches the chart to the bottom column
- **THEN** the chart plots each team's chance of avoiding the loser's bye for every stored as-of week

#### Scenario: Distinct team colors
- **WHEN** a visitor views a 12-team league's chart in either theme
- **THEN** the 12 lines use 12 different colors, each readable against the chart background, and each team's table row shows a swatch of its line color

#### Scenario: Highlight a team
- **WHEN** a visitor picks one team in the chart or table
- **THEN** that team's line keeps its color at full strength and the others are dimmed

#### Scenario: Axis fits the data
- **WHEN** the visitor switches to the title metric and the highest plotted value is 34%
- **THEN** the axis runs from 0% to 40%

#### Scenario: Axis cap
- **WHEN** the highest plotted value is 100%
- **THEN** the axis top is 100%

### Requirement: Odds table sorting
Every table column SHALL be sortable from its header. The first click on a header SHALL sort descending (owner: A to Z), the second ascending, and the sorted header SHALL show a dark fill and a small arrow for the direction. An unsorted table SHALL show no fill and no arrow on any header. Record sorts by wins then points scored; projected record by projected wins; ELO by rating; 1-week ELO change by the signed change.

#### Scenario: Sort by a chance column
- **WHEN** a visitor clicks the "Win Championship" header once
- **THEN** rows are ordered by championship chance, highest first, and that header shows a dark fill and a down arrow

#### Scenario: Second click flips direction
- **WHEN** the visitor clicks the same header again
- **THEN** rows are ordered lowest first and the arrow points up

#### Scenario: Untouched table
- **WHEN** a visitor opens a league page and has not clicked any header
- **THEN** no header has a fill or an arrow

#### Scenario: ELO headers not yet sortable
- **WHEN** a visitor clicks the ELO or 1-week change header while the exported data carries no ratings
- **THEN** the header takes the sorted state and the row order does not change, since every value is empty

#### Scenario: Sort by ELO
- **WHEN** a visitor clicks the ELO header once
- **THEN** rows are ordered by rating, highest first, and teams without a rating sort last

### Requirement: ELO placeholder columns
The ELO and 1-week ELO change columns SHALL show each team's current manager rating mean, rounded to a whole number, and its signed change over the last rated week. While no rating data is exported, both columns SHALL render as empty cells. A positive change SHALL render as black text on a green fill, a negative change as black text on a red fill, and no change as an empty cell.

#### Scenario: Before ELO exists
- **WHEN** the exported data carries no ELO values
- **THEN** every ELO and 1-week change cell is empty and the two headers are still shown

#### Scenario: Future ELO change rendering
- **WHEN** the exported data gives a team an ELO of 1676 and a 1-week change of +20
- **THEN** the ELO cell shows "1676" and the change cell shows "+20" as black text on a green fill

#### Scenario: First rated week of a newcomer
- **WHEN** a team's manager has only one rated week
- **THEN** the ELO cell shows their rating and the change cell is empty

### Requirement: Scheduled refresh
A scheduled job SHALL run at least once a day. It SHALL sync league data, refresh projections and player stats, refresh manager ratings and replacement levels, run the simulation for the current as-of week, save the results, commit the stored data to the repository and republish the site. It SHALL also be possible to start the job by hand.

#### Scenario: Day after Monday night
- **WHEN** the scheduled run happens the day after Monday night's game ends and week 10 is final in Sleeper
- **THEN** the published site shows results as of week 10

#### Scenario: Failed refresh
- **WHEN** any step of the scheduled job fails
- **THEN** the previously published site stays online unchanged, no partial data is committed, and the job run is marked failed

#### Scenario: Stats and replacement levels refreshed
- **WHEN** the scheduled run completes
- **THEN** the current season's stats for played weeks and the current season's replacement levels are stored alongside the odds

#### Scenario: Ratings refreshed
- **WHEN** the scheduled run completes after week 10 is final
- **THEN** every league's rating file includes week 10 and the published table shows the updated ELO values
