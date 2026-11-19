## MODIFIED Requirements

### Requirement: Current odds table
Each league page SHALL show a table with one row per team and these columns in order: ELO, 1-week ELO change, Manager (the manager's display name in bold with the team name beneath it and the current record beside the name), projected final record, and four chance columns: the league's bottom column (see "League-dependent bottom column"), make playoffs, first-round bye, win championship. Until a visitor sorts the table, rows SHALL be in league standings order: wins (a tie counts half), then points scored. Columns left of Manager SHALL be left-aligned, the Manager column centred, and columns right of it right-aligned, headers and cells alike. The table SHALL be compact: the ELO and 1-week change columns no wider than their content needs, tight row padding, and text a step larger than body text.

#### Scenario: Table contents
- **WHEN** a visitor opens the dynasty page with the as-of-week-10 results stored
- **THEN** the table shows all 12 teams with the as-of-week-10 values in standings order

#### Scenario: Owner cell
- **WHEN** a team is managed by `tg1212`, named "Diaper Dandies" and has 7 wins, 2 losses and no ties
- **THEN** its Manager cell shows "tg1212" in bold with "7-2" beside it and "Diaper Dandies" beneath, centred in the column under the header "Manager"

#### Scenario: Alignment
- **WHEN** the table is shown at any width
- **THEN** the ELO and 1-week change headers and cells are left-aligned, the Manager header and cells centred, and the projected record and chance headers and cells right-aligned

#### Scenario: Projected record format
- **WHEN** a team's projected record is 10.59 wins and 3.41 losses
- **THEN** the projected record cell shows "10.6 - 3.4"

#### Scenario: Weekly change
- **WHEN** results exist for both the current as-of week and the one before it
- **THEN** hovering over any of a team's chance cells shows that chance's change since the previous as-of week, and no separate change column is shown

#### Scenario: First week of results
- **WHEN** results exist only for the current as-of week
- **THEN** chance cells show no change information

### Requirement: Usable on phones
League pages SHALL be readable on a 375px-wide screen without horizontal page scrolling. The odds table MAY scroll horizontally inside its own container. Below 600 px the Manager column SHALL stay pinned to the container's left edge while the table scrolls, with ELO and 1-week change scrolling away beneath it; manager names SHALL not wrap. When the sub-tabs do not fit the screen width, the sub-tab menu SHALL scroll sideways inside its own strip with a swipe:

- The tabs SHALL snap into place.
- The edge with more tabs beyond it SHALL fade.
- The selected sub-tab SHALL be scrolled into view on load.
- No scroll bar SHALL show.
- Swiping the menu SHALL not move the rest of the page.

#### Scenario: Phone visit
- **WHEN** a visitor opens a league page on a 375px-wide screen
- **THEN** the page itself doesn't scroll sideways and the chart fits the screen width

#### Scenario: Swipe the sub-tabs
- **WHEN** a visitor on a 375px-wide screen swipes the sub-tab menu left
- **THEN** the menu scrolls to reveal "Player WAR", the tabs settle on a tab edge, and the page below stays where it was

#### Scenario: Linked to the last sub-tab
- **WHEN** a visitor on a phone opens a link to the Player WAR sub-tab
- **THEN** the menu opens scrolled so "Player WAR" is visible and marked selected

#### Scenario: Wide screen
- **WHEN** the sub-tabs fit the screen width
- **THEN** the menu does not scroll and shows no fade

#### Scenario: Scroll the forecast table on a phone
- **WHEN** a visitor on a 440 px-wide phone scrolls the forecast table to the right
- **THEN** the ELO and 1-week change columns scroll out of view while the Manager column stays at the left edge beside the chance columns

### Requirement: Chart metric buttons
Metric buttons at the top left of the odds-over-time chart's card, where they serve as the chart's heading, SHALL offer the table's four chance columns in the table's order, and the chart SHALL plot the chosen chance (playoffs by default). When the buttons do not fit on one line they SHALL form one row that scrolls sideways under a finger, without wrapping and without moving the page. On narrow screens the chart SHALL use the card's full width, reserving room at its right edge for an end label only while a team is highlighted, and then only that label's width.

#### Scenario: Switch metric
- **WHEN** a visitor clicks the "Bye" metric button
- **THEN** the chart plots each team's first-round-bye chance for every stored as-of week

#### Scenario: Buttons on a phone
- **WHEN** the redraft page is shown at 375 px
- **THEN** the four metric buttons sit on one line that can be swiped sideways, and the chart spans the card's width

#### Scenario: Highlighted team on a phone
- **WHEN** a visitor on a phone highlights a team
- **THEN** that team's end label shows at the right of the chart, which gives up only that label's width

### Requirement: Rating chart time range
Range buttons below the rating chart, smaller than the Rating and Z-score buttons above it, SHALL offer "This season", "Last 3 seasons" and "All time" (default "All time"), and SHALL limit the plotted weeks without changing any manager's colour or the chosen metric. A league with fewer than three stored seasons SHALL show "Last 3 seasons" as the same range as "All time".

#### Scenario: This season
- **WHEN** a visitor on the redraft page picks "This season" during 2026
- **THEN** only 2026's rated weeks are plotted and each line keeps its colour

#### Scenario: Last three seasons
- **WHEN** a visitor picks "Last 3 seasons" on a league with seasons 2021 through 2026
- **THEN** weeks from 2024, 2025 and 2026 are plotted

#### Scenario: Placement
- **WHEN** the rating chart is shown
- **THEN** the Rating and Z-score buttons lead the card above the chart and the range buttons sit below the chart in a smaller size
