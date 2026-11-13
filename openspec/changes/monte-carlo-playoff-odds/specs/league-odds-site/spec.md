# Spec Delta

## Purpose

Gives league members a public website where they can see their team's current playoff odds and how those odds have changed over the season. A scheduled job keeps it current.

## ADDED Requirements

### Requirement: League pages
The site SHALL have a page for each configured league that shows that league's current season. Visitors SHALL be able to switch between leagues.

#### Scenario: Switch league
- **WHEN** a visitor on the dynasty page picks the redraft league
- **THEN** the redraft league's odds are shown

### Requirement: Current odds table
Each league page SHALL show a table with one row per team: team name, owner, current record, points scored, projected final record, and chances of making the playoffs, a first-round bye, reaching the final, winning the title, landing in the losers bracket, and finishing last. Rows SHALL be sorted by playoff chance, highest first.

#### Scenario: Table contents
- **WHEN** a visitor opens the dynasty page with the as-of-week-10 results stored
- **THEN** the table shows all 12 teams with the as-of-week-10 values, sorted by playoff chance

#### Scenario: Weekly change
- **WHEN** results exist for both the current as-of week and the one before it
- **THEN** each team's playoff chance shows its change since the previous as-of week

### Requirement: Odds-over-time chart
Each league page SHALL show a line chart with one line per team, plotting a chosen chance (playoffs by default) for each stored as-of week of the season. Visitors SHALL be able to switch the chart to bye, final or title chances.

#### Scenario: Default chart
- **WHEN** a visitor opens a league page with results for as-of weeks 0 through 10
- **THEN** the chart shows each team's playoff chance at weeks 0 through 10

#### Scenario: Highlight a team
- **WHEN** a visitor picks one team in the chart or table
- **THEN** that team's line is highlighted and the others are dimmed

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
