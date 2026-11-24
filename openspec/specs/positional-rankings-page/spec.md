# positional-rankings-page Specification

## Purpose

The Positions sub-tab of each league page, titled "Positional Rankings": one dot chart per position comparing every Manager's rostered Players by points per game against the replacement level, in the style of 538's quarterback Elo charts. It delivers need 3, Player Value, on the page; the data and calculations are in `positional-rankings`.

## Requirements

### Requirement: 3.1 Positions sub-tab
The Positions sub-tab SHALL show one dot chart per position, comparing every Manager's rostered Players by points per game against the replacement level.

**Traces to:** 3; 9.1.1
**Verified by:** Test: `tests/layout/test_positions_page.py::test_one_chart_per_started_position_in_order`

#### Scenario: Open the Positions sub-tab
- **WHEN** a visitor picks "Positions"
- **THEN** the league's position charts are shown

### Requirement: 3.1.1 Opens on the current season
The Positions sub-tab SHALL open on the league's current season.

**Traces to:** 3.1
**Verified by:** Test: `tests/layout/test_positions_page.py::test_season_control_defaults_to_the_current_season`

#### Scenario: Default season
- **WHEN** a visitor opens the Positions sub-tab in week 11 of 2026
- **THEN** the 2026 charts are shown

### Requirement: 3.1.1.1 Season list
The season control SHALL list every season the league has a positional rankings file for, newest first.

**Traces to:** 3.1.1
**Verified by:** Test: `tests/layout/test_positions_page.py::test_season_control_defaults_to_the_current_season`

#### Scenario: Past season
- **WHEN** the visitor picks 2023
- **THEN** the 2023 charts are shown from the final 2023 rosters

### Requirement: 3.1.1.2 Current season label
While the current season is in progress, the page SHALL say the last final week its actual points run through.

**Traces to:** 3.1.1
**Verified by:** Test: `tests/layout/test_positions_page.py::test_season_control_defaults_to_the_current_season`

#### Scenario: Week 11
- **WHEN** a visitor opens the 2026 charts in week 11
- **THEN** the page says the points are actual through week 10 plus projections

### Requirement: 3.1.2 Charts by position
The page SHALL show one chart for each position the league starts, in the order QB, RB, WR, TE, K and DEF.

**Traces to:** 3.1
**Verified by:** Test: `tests/layout/test_positions_page.py::test_one_chart_per_started_position_in_order`

#### Scenario: Redraft layout
- **WHEN** the redraft Positions sub-tab is shown
- **THEN** six charts appear, each with twelve Manager rows

#### Scenario: Dynasty layout
- **WHEN** the dynasty Positions sub-tab is shown
- **THEN** five charts appear, with no K chart

### Requirement: 3.1.2.1 Two columns
At 1280 px wide, the charts SHALL sit in two columns, with a chart alone on the last row centred.

**Traces to:** 3.1.2
**Verified by:** Inspection: the live site at 1280 px, both leagues' grids

#### Scenario: Dynasty grid
- **WHEN** the dynasty Positions sub-tab is shown at 1280 px
- **THEN** QB and RB, then WR and TE share rows, and DEF is centred on the last row

### Requirement: 3.1.2.2 Shared row height
Two charts sharing a grid row SHALL use the same row height and fill their cards, while a chart alone on its row keeps its own height.

**Traces to:** 3.1.2; 3.1.2.1
**Verified by:** Test: `tests/layout/test_layout.py::test_paired_charts_share_row_height_and_fill_their_cards`

#### Scenario: Neighbour with crowded rows
- **WHEN** the WR chart needs taller rows for its overlapping dots and the TE chart beside it does not
- **THEN** both charts use the taller row height and end level at the bottom of their cards

### Requirement: 3.1.2.3 Manager rows
Each chart SHALL have one row per Manager, labelled with the display name and, beneath it in smaller muted text, the Team Name, without a colour swatch.

**Traces to:** 3.1.2
**Verified by:** Test: `tests/layout/test_layout.py::test_row_labels_show_manager_and_team`

#### Scenario: Manager and team
- **WHEN** a row belongs to the Manager Alice whose team is The Big Penguin
- **THEN** the row reads "Alice" with "The Big Penguin" beneath it in smaller muted text

### Requirement: 3.1.2.3.1 Long labels
A row label too long for its column SHALL end in an ellipsis, with the full text on hover.

**Traces to:** 3.1.2.3
**Verified by:** Inspection: the live site at 360 px, the longest Team Name's label and tooltip

#### Scenario: Long Team Name
- **WHEN** a Team Name is wider than the label column
- **THEN** it ends in an ellipsis and hovering shows the full name

### Requirement: 3.1.2.4 Points-per-game axis
Each chart SHALL have a horizontal points-per-game axis over the position's fixed range, with light vertical grid lines.

**Rationale:** A fixed range per position lets seasons be compared by eye.
**Traces to:** 3.1.2
**Verified by:** Test: `tests/test_positions.py::test_axis_is_shared_across_seasons_and_ignores_outliers`

#### Scenario: Same axis every season
- **WHEN** a visitor switches the QB chart from 2025 to 2026
- **THEN** the axis range stays the same

### Requirement: 3.1.3 Row order
Each chart SHALL order its rows by the points per game of the Manager's best Player at that position, highest first, breaking ties by the second-best Player's, then the third and so on, then by Team Name.

**Traces to:** 3.1
**Verified by:** Test: `tests/layout/test_positions_page.py::test_rows_follow_each_managers_best_player`

#### Scenario: Best player first
- **WHEN** one Manager's best quarterback averages 25.1 points per game, the highest of any Manager
- **THEN** that Manager's row is the top row of the QB chart

#### Scenario: Tie on the best player
- **WHEN** two Managers' best tight ends both average 11.0 and their second-best average 7.2 and 4.9
- **THEN** the Manager whose second-best averages 7.2 ranks above the other

### Requirement: 3.1.3.1 Empty rows last
A Manager with no listed Player at a position SHALL keep an empty row at the bottom of that chart.

**Traces to:** 3.1.3
**Verified by:** Test: `tests/layout/test_positions_page.py::test_rows_follow_each_managers_best_player`

#### Scenario: No kicker rostered
- **WHEN** a redraft Manager has no kicker
- **THEN** that Manager has an empty row at the bottom of the K chart

### Requirement: 3.1.4 Replacement line
Each chart with a replacement level SHALL draw a vertical dotted line at that level, labelled "Replacement Level" above the chart.

**Traces to:** 3.1
**Verified by:** Test: `tests/layout/test_positions_page.py::test_replacement_line_sits_at_the_replacement_level`

#### Scenario: Line drawn
- **WHEN** the redraft 2025 RB chart is shown and the RB replacement level is 7.94
- **THEN** a dotted line labelled "Replacement Level" crosses the chart at 7.94

### Requirement: 3.1.5 Player dots
Each listed Player SHALL be a dot on his Manager's row at his points per game, filled with a lighter shade of the Manager's colour and outlined in the full colour.

**Traces to:** 3.1
**Verified by:** Inspection: the live site, dots on the dynasty charts

#### Scenario: Manager colour
- **WHEN** a Manager's line on the Forecast chart is blue
- **THEN** that Manager's dots are light blue with a blue outline

### Requirement: 3.1.5.1 Shared Manager colours
Dot colours SHALL be each Manager's colours from the other sub-tabs, with former Managers in the greys used elsewhere.

**Traces to:** 3.1.5; 1.4.3; 4.2.3.1
**Verified by:** Inspection: the live site, a Manager's colour on the Forecasts and Positions sub-tabs, and a 2022 former Manager

#### Scenario: Former member in a past season
- **WHEN** the 2022 charts include a Manager who has since left the league
- **THEN** that Manager's dots use a grey

### Requirement: 3.1.6 Taxi and injury markers
A taxi-squad Player's dot SHALL have a dotted outline, and an injured Player's dot a red cross.

**Traces to:** 3.1; 3.1.5
**Verified by:** Test: `tests/layout/test_positions_page.py::test_taxi_and_injury_markers_follow_the_flags`

#### Scenario: Taxi player
- **WHEN** a dynasty Manager's rookie quarterback is on the taxi squad
- **THEN** his dot has a dotted outline in the Manager's colour

#### Scenario: Injured player
- **WHEN** a receiver in the current season is flagged injured
- **THEN** his dot carries a red cross

### Requirement: 3.1.7 Top player label
The Player with the highest points per game on each chart SHALL have his last name written above his dot, centred on it even where it overhangs the plot area.

**Traces to:** 3.1
**Verified by:** Test: `tests/layout/test_positions_page.py::test_top_player_is_labelled_over_his_dot`

#### Scenario: Top player labelled
- **WHEN** the QB chart's highest points per game belongs to Josh Allen
- **THEN** "Allen" is written above his dot

### Requirement: 3.1.7.1 Label inside the card
The top Player's label SHALL move sideways by the least distance that keeps it inside the chart's card.

**Traces to:** 3.1.7
**Verified by:** Test: `tests/layout/test_layout.py::test_positions_charts_fit_a_phone`

#### Scenario: Top player at the axis end
- **WHEN** the WR chart's top Player Smith-Njigba sits at the right end of the axis
- **THEN** "Smith-Njigba" is centred over his dot, overhanging the plot but inside the card

### Requirement: 3.1.8 Out-of-range values
A value outside the axis range SHALL be drawn at the nearest edge with an arrow showing it continues, its popup showing the true value.

**Traces to:** 3.1; 3.1.2.4
**Verified by:** Test: `tests/layout/test_positions_page.py::test_out_of_range_value_sits_at_the_edge_with_an_arrow`

#### Scenario: Outlier
- **WHEN** a kicker averages 31 points per game from one game and the K axis ends at 15
- **THEN** his dot sits at the right edge with an arrow, and its popup shows 31.0

### Requirement: 3.1.9 Overlapping dots
Dots on one row closer together than one dot width SHALL be offset alternately above and below the row line, so that each stays visible.

**Traces to:** 3.1; 3.1.5
**Verified by:** Test: `tests/layout/test_layout.py::test_position_dots_do_not_hide_each_other`

#### Scenario: Close values
- **WHEN** a Manager's three running backs average 11.0, 11.3 and 12.4
- **THEN** the dots are offset above and below the line and none hides another

### Requirement: 3.1.9.1 Stable offsets
The dot offsets SHALL be the same on every visit for the same data.

**Traces to:** 3.1.9
**Verified by:** Inspection: `site/positions.js`, the dot placement uses no random numbers

#### Scenario: Second visit
- **WHEN** a visitor reloads the page with the same data
- **THEN** every dot sits where it was

### Requirement: 3.1.10 Dot popup
Hovering over a dot, focusing it with the keyboard or tapping it SHALL show a popup with the Player's name and his points per game to one decimal.

**Traces to:** 3.1; 3.1.5; 9
**Verified by:** Test: `tests/layout/test_layout.py::test_popup_shows_status_and_taxi_lines`; Inspection: the live site, hover on desktop and tap on a phone

#### Scenario: Hover
- **WHEN** a visitor hovers over Tua Tagovailoa's dot
- **THEN** a popup reads "Tua Tagovailoa" and his points per game, such as 16.5

### Requirement: 3.1.10.1 Status line
A Player with an out status SHALL show its label in red on a line below his name in the popup, above any Taxi line.

**Traces to:** 3.1.10
**Verified by:** Test: `tests/layout/test_layout.py::test_popup_shows_status_and_taxi_lines`

#### Scenario: Injured player
- **WHEN** a visitor hovers over Lamar Jackson's dot and his status is IR
- **THEN** the popup shows his name, his points per game and "IR" in red

### Requirement: 3.1.10.2 Taxi line
A taxi-squad Player SHALL show "Taxi" on a line below his name in the popup, in gold with at least 4.5:1 contrast against the popup in both themes.

**Traces to:** 3.1.10
**Verified by:** Test: `tests/layout/test_layout.py::test_popup_shows_status_and_taxi_lines`; Test: `tests/test_colour_contrast.py::test_colour_tokens_meet_contrast`

#### Scenario: Taxi player
- **WHEN** a visitor hovers over a taxi-squad quarterback's dot
- **THEN** the popup shows his name, his points per game and "Taxi" in gold

### Requirement: 3.1.11 Positions on a phone
At every tested phone width, the charts SHALL stack in one column, with every row and the top Player's name inside its chart and no sideways page scrolling.

**Traces to:** 3.1; 9.2
**Verified by:** Test: `tests/layout/test_layout.py::test_positions_charts_fit_a_phone`

#### Scenario: Phone layout
- **WHEN** the Positions sub-tab is shown at 360 px
- **THEN** the charts stack in one column with no sideways page scrolling

### Requirement: 3.1.12 Data swapped in place
When newer site data arrives while the Positions sub-tab is open, the page SHALL redraw from it, keeping the selected season.

**Traces to:** 3.1; 5
**Verified by:** Test: `tests/layout/test_layout.py::test_positions_data_swap_keeps_the_season`

#### Scenario: Refresh while viewing 2025
- **WHEN** new data is deployed while a visitor views the 2025 charts
- **THEN** the 2025 charts are redrawn and the season stays 2025
