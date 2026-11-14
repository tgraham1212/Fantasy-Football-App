# league-odds-site Specification

## Purpose

Gives league members a public website where they can see their team's current playoff odds and how those odds have changed over the season. A scheduled job keeps it current.

## Requirements

### Requirement: League pages
The site SHALL have a page for each configured league that shows that league's current season. Visitors SHALL be able to switch between leagues.

#### Scenario: Switch league
- **WHEN** a visitor on the dynasty page picks the redraft league
- **THEN** the redraft league's odds are shown

### Requirement: Current odds table
Each league page SHALL show a table with one row per team and these columns in order: ELO, 1-week ELO change, owner (owner display name with the team name beneath it and the current record beside the owner name), projected final record, and four chance columns: the league's bottom column (see "League-dependent bottom column"), make playoffs, first-round bye, win championship. Until a visitor sorts the table, rows SHALL be in league standings order: wins (a tie counts half), then points scored.

#### Scenario: Table contents
- **WHEN** a visitor opens the dynasty page with the as-of-week-10 results stored
- **THEN** the table shows all 12 teams with the as-of-week-10 values in standings order

#### Scenario: Owner cell
- **WHEN** a team is owned by `tg1212`, named "Diaper Dandies" and has 7 wins, 2 losses and no ties
- **THEN** its owner cell shows "tg1212" with "7-2" beside it and "Diaper Dandies" beneath

#### Scenario: Projected record format
- **WHEN** a team's projected record is 10.59 wins and 3.41 losses
- **THEN** the projected record cell shows "10.6 - 3.4"

#### Scenario: Weekly change
- **WHEN** results exist for both the current as-of week and the one before it
- **THEN** hovering over any of a team's chance cells shows that chance's change since the previous as-of week, and no separate change column is shown

#### Scenario: First week of results
- **WHEN** results exist only for the current as-of week
- **THEN** chance cells show no change information

### Requirement: Odds-over-time chart
Each league page SHALL show a line chart with one line per team, plotting a chosen chance (playoffs by default) for each stored as-of week of the season. Metric buttons at the top right of the chart SHALL offer the table's four chance columns in the table's order. Each team's line SHALL have its own distinct color, unchanged across weeks, metrics, sorts and highlighting, and the same color SHALL mark that team's row in the table. The axis floor SHALL be 0 and its top the next multiple of 10 at least 5 points above the highest plotted value, capped at 100.

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

### Requirement: Freshness shown
Each league page SHALL show the as-of week of the results and when they were generated.

#### Scenario: Freshness label
- **WHEN** the results were produced on 2026-11-17 as of week 10
- **THEN** the page states the results are as of week 10 and were updated on 2026-11-17

### Requirement: Static and public
The site SHALL be static files that need no server code, login or calls to Sleeper from the visitor's browser. Anyone with the link SHALL be able to view it.

#### Scenario: Visitor loads page
- **WHEN** a visitor opens a league page
- **THEN** all data comes from files published with the site

### Requirement: Usable on phones
League pages SHALL be readable on a 375px-wide screen without horizontal page scrolling. The odds table MAY scroll horizontally inside its own container.

#### Scenario: Phone visit
- **WHEN** a visitor opens a league page on a 375px-wide screen
- **THEN** the page itself doesn't scroll sideways and the chart fits the screen width

### Requirement: Scheduled refresh
A scheduled job SHALL run at least once a day. It SHALL sync league data, refresh projections, run the simulation for the current as-of week, save the results, commit the stored data to the repository and republish the site. It SHALL also be possible to start the job by hand.

#### Scenario: Day after Monday night
- **WHEN** the scheduled run happens the day after Monday night's game ends and week 10 is final in Sleeper
- **THEN** the published site shows results as of week 10

#### Scenario: Failed refresh
- **WHEN** any step of the scheduled job fails
- **THEN** the previously published site stays online unchanged, no partial data is committed, and the job run is marked failed

### Requirement: League-dependent bottom column
The first chance column SHALL depend on the league's Sleeper settings. A toilet-bowl league SHALL show "Avoid Loser's Bye": the chance of finishing outside the bottom two of the regular-season standings. A dynasty league with a consolation bracket SHALL show "#1 Pick": the chance of finishing last. Any other league SHALL show "Avoid Loser's Bye". The exported data SHALL name the column so the site needs no league-specific rules.

#### Scenario: Toilet-bowl league
- **WHEN** a visitor opens the redraft page (toilet bowl) for a team that finishes 11th in 3% of runs and 12th in 1%
- **THEN** the first chance column is titled "Avoid Loser's Bye" and shows 96% for that team

#### Scenario: Dynasty consolation league
- **WHEN** a visitor opens the dynasty page (consolation bracket, dynasty league) for a team that finishes last in 40% of runs
- **THEN** the first chance column is titled "#1 Pick" and shows 40% for that team

### Requirement: Chance cell fill
Every chance cell SHALL be filled with a single-hue blue that gets darker as the chance rises: no fill at or below 1%, the darkest blue at or above 99%, and text that stays readable at every step, switching to light text on dark fills. Values SHALL print as "<1%", ">99%" or a whole-number percentage. Each theme SHALL use a ramp designed for its own background rather than a flipped copy of the other theme's.

#### Scenario: Low, mid and high chances
- **WHEN** three teams have 0.3%, 50% and 99.6% playoff chances
- **THEN** their cells read "<1%", "50%" and ">99%", with no fill, a mid blue, and the darkest blue with light text respectively

#### Scenario: Dark theme
- **WHEN** a visitor views the table in the dark theme
- **THEN** chance cells use the dark-theme ramp and every value stays readable against its fill

### Requirement: Odds table sorting
Every table column except ELO and 1-week ELO change SHALL be sortable from its header. The first click on a header SHALL sort descending (owner: A to Z), the second ascending, and the sorted header SHALL show a dark fill and a small arrow for the direction. An unsorted table SHALL show no fill and no arrow on any header. Record sorts by wins then points scored; projected record by projected wins.

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
- **WHEN** a visitor clicks the ELO or 1-week change header before the ELO feature exists
- **THEN** the row order does not change

### Requirement: ELO placeholder columns
The ELO and 1-week ELO change columns SHALL be present with their headers. While no ELO data is exported, both columns SHALL render as empty cells. Once ELO data exists, a positive 1-week change SHALL render as black text on a green fill, a negative change as black text on a red fill, and no change as an empty cell.

#### Scenario: Before ELO exists
- **WHEN** the exported data carries no ELO values
- **THEN** every ELO and 1-week change cell is empty and the two headers are still shown

#### Scenario: Future ELO change rendering
- **WHEN** the exported data gives a team an ELO of 1676 and a 1-week change of +20
- **THEN** the ELO cell shows "1676" and the change cell shows "+20" as black text on a green fill

### Requirement: Grouped chance headers
The four chance columns SHALL sit under a single "Playoff chances" group header, and every column header SHALL use small uppercase labels that wrap to two lines where needed.

#### Scenario: Header layout
- **WHEN** a visitor views the table on a desktop-width screen
- **THEN** a "Playoff chances" label spans exactly the four chance columns, above their individual headers
