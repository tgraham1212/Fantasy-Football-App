## MODIFIED Requirements

### Requirement: Position charts
The page SHALL show one chart per position the league starts, in two columns in the order QB and RB, WR and TE, K and DEF. A league without a position SHALL omit its chart. A chart left alone on the last row SHALL be centred. Each chart SHALL have one row per manager, labelled with the manager's display name and, beneath it in smaller muted text, the team name, as on the Predictions and Games tabs, with no colour swatch. A label too long for its column SHALL end in an ellipsis, with the full text on hover. On desktop widths, the two charts sharing a grid row SHALL use the same row height, so both fill their cards. A chart alone on its row SHALL keep its own height. The chart SHALL have a horizontal points-per-game axis using the position's fixed range, with light vertical grid lines.

#### Scenario: Redraft layout
- **WHEN** the redraft Positions page is shown at desktop width
- **THEN** six charts appear in three rows of two, each with twelve manager rows

#### Scenario: Dynasty layout
- **WHEN** the dynasty Positions page is shown at desktop width
- **THEN** five charts appear with no K chart, and DEF is centred on the last row

#### Scenario: Manager and team
- **WHEN** a row belongs to the manager Alice whose team is The Big Penguin
- **THEN** the row reads "Alice" with "The Big Penguin" beneath it in smaller muted text

#### Scenario: Neighbour with crowded rows
- **WHEN** the WR chart needs taller rows for its overlapping dots and the TE chart beside it does not
- **THEN** both charts use the taller row height and end level at the bottom of their cards

### Requirement: Top player label
The player with the highest points per game on each chart SHALL have his last name written above his dot, centred on the dot even where it overhangs the plot area. It SHALL move sideways only as far as needed to stay inside the chart's card.

#### Scenario: Top player labelled
- **WHEN** the QB chart's highest points per game belongs to Josh Allen
- **THEN** "Allen" is written above his dot at the top right of the chart

#### Scenario: Top player at the axis end
- **WHEN** the WR chart's top player Smith-Njigba sits at the right end of the axis
- **THEN** "Smith-Njigba" is centred over his dot, overhanging the plot but inside the card

### Requirement: Dot hover
Hovering over a dot, or focusing it with the keyboard, SHALL show a small popup with the player's name and his points per game to one decimal. A player with an out status SHALL show its label in red on a line below. A taxi-squad player SHALL show "Taxi" on a line below, in a gold that is dark in light mode and bright in dark mode, and readable against the popup in both. A player with both SHALL show the status first. Tapping a dot on a touch screen SHALL show the same popup.

#### Scenario: Hover
- **WHEN** a visitor hovers over Tua Tagovailoa's dot
- **THEN** a popup reads "Tua Tagovailoa" and his points per game, such as 16.5

#### Scenario: Injured player
- **WHEN** a visitor hovers over Lamar Jackson's dot and his status is IR
- **THEN** the popup shows his name, his points per game and "IR" in red

#### Scenario: Taxi player
- **WHEN** a visitor hovers over a taxi-squad quarterback's dot
- **THEN** the popup shows his name, his points per game and "Taxi" in gold
