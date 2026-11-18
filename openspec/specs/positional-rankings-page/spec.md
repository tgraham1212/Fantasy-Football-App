# positional-rankings-page Specification

## Purpose

The Positions sub-tab of each league, titled "Positional Rankings": one dot chart per position comparing every manager's rostered players by points per game against the replacement level, in the style of 538's quarterback Elo charts.

## Requirements

### Requirement: Season control
The Positions page SHALL default to the league's current season and SHALL offer a dropdown of every season the league has a positional rankings file for. The current season SHALL be labelled with the last final week its actual points run through.

#### Scenario: Default season
- **WHEN** a visitor opens the Positions page in week 11 of 2026
- **THEN** the 2026 charts are shown, labelled as actual points through week 10 plus projections

#### Scenario: Past season
- **WHEN** the visitor picks 2023
- **THEN** the 2023 charts are shown from the final 2023 rosters

### Requirement: Position charts
The page SHALL show one chart per position the league starts, in two columns in the order QB and RB, WR and TE, K and DEF. A league without a position SHALL omit its chart. A chart left alone on the last row SHALL be centred. Each chart SHALL have one row per manager, labelled with the team or owner name. The chart SHALL have a horizontal points-per-game axis using the position's fixed range, with light vertical grid lines.

#### Scenario: Redraft layout
- **WHEN** the redraft Positions page is shown at desktop width
- **THEN** six charts appear in three rows of two, each with twelve manager rows

#### Scenario: Dynasty layout
- **WHEN** the dynasty Positions page is shown at desktop width
- **THEN** five charts appear with no K chart, and DEF is centred on the last row

### Requirement: Row order
Each chart SHALL order its manager rows by the points per game of the manager's best player at that position, highest first. Ties SHALL break by the second-best player's points per game, then the third and so on, then by team name. A manager with no listed player at the position SHALL keep an empty row at the bottom.

#### Scenario: Best player first
- **WHEN** one manager's best quarterback averages 25.1 points per game, the highest of any manager
- **THEN** that manager's row is the top row of the QB chart

#### Scenario: Tie on the best player
- **WHEN** two managers' best tight ends both average 11.0 and their second-best average 7.2 and 4.9
- **THEN** the manager whose second-best averages 7.2 is ranked above the other

#### Scenario: No kicker rostered
- **WHEN** a redraft manager has no kicker
- **THEN** that manager has an empty row at the bottom of the K chart

### Requirement: Replacement line
Each chart SHALL draw a vertical dotted line at the position's replacement level, labelled "Replacement Level" above the chart. A chart with no replacement level SHALL omit the line.

#### Scenario: Line drawn
- **WHEN** the redraft 2025 RB chart is shown and the RB replacement level is 7.94
- **THEN** a dotted line labelled "Replacement Level" crosses the chart at 7.94

### Requirement: Player dots
Each listed player SHALL be a dot on his manager's row at his points per game. It SHALL be filled with a lighter shade of the manager's colour and outlined in the full colour. The colours SHALL be the manager colours used on the other sub-tabs, matched by owner, and former members SHALL use the grey shades used elsewhere.

#### Scenario: Manager colour
- **WHEN** a manager's line on the Predictions chart is blue
- **THEN** that manager's dots on the Positions page are light blue with a blue outline

#### Scenario: Former member in a past season
- **WHEN** the 2022 charts include a manager who has since left the league
- **THEN** that manager's dots use a grey shade

### Requirement: Dot markers
A taxi-squad player's dot SHALL have a dotted outline. A player flagged injured SHALL carry a red cross on his dot.

#### Scenario: Taxi player
- **WHEN** a dynasty manager's rookie quarterback is on the taxi squad
- **THEN** his dot has a dotted outline in the manager's colour

#### Scenario: Injured player
- **WHEN** a receiver in the current season is flagged injured
- **THEN** his dot carries a red cross

### Requirement: Top player label
The player with the highest points per game on each chart SHALL have his last name written above his dot, kept inside the chart.

#### Scenario: Top player labelled
- **WHEN** the QB chart's highest points per game belongs to Josh Allen
- **THEN** "Allen" is written above his dot at the top right of the chart

### Requirement: Out-of-range values
A value outside the axis range SHALL be drawn at the nearest edge with an arrow showing it continues, and its popup SHALL show the true value.

#### Scenario: Outlier
- **WHEN** a kicker averages 31 points per game from one game and the K axis ends at 15
- **THEN** his dot sits at the right edge with an arrow, and hovering it shows 31.0

### Requirement: Overlapping dots
Dots on one row closer together than one dot width SHALL be offset alternately above and below the row line, so that each dot stays visible. The offsets SHALL be the same on every visit for the same data.

#### Scenario: Close values
- **WHEN** a manager's three running backs average 11.0, 11.3 and 12.4
- **THEN** the dots are offset above and below the line and none hides another

### Requirement: Dot hover
Hovering over a dot, or focusing it with the keyboard, SHALL show a small popup with the player's name and his points per game to one decimal. Tapping a dot on a touch screen SHALL show the same popup.

#### Scenario: Hover
- **WHEN** a visitor hovers over Tua Tagovailoa's dot
- **THEN** a popup reads "Tua Tagovailoa" and his points per game, such as 16.5

### Requirement: Positions on phones
At 375px width the charts SHALL stack in one column, every manager row and the top player's name SHALL stay inside the chart, and the page SHALL not scroll sideways.

#### Scenario: Phone layout
- **WHEN** the Positions page is shown at 375px width
- **THEN** the charts stack in one column with no horizontal page scroll

### Requirement: Positions data swapped in place
When newer site data arrives while the Positions page is open, the page SHALL redraw from the new data, keeping the selected season.

#### Scenario: Refresh while viewing 2025
- **WHEN** new data is deployed while a visitor views the 2025 Positions charts
- **THEN** the 2025 charts are redrawn and the season stays 2025
