## MODIFIED Requirements

### Requirement: Position leaderboards
The page SHALL show one table per lineup position with the top 10 players by WAR, laid out in two columns in the order QB and RB, WR and TE, DEF and K. A league without a position SHALL omit that table, and a table left alone on the last row SHALL be centred. Compact columns SHALL be rank, name, NFL team, Manager (the fantasy manager holding the player) and WAR.

#### Scenario: Redraft layout
- **WHEN** the redraft page is shown on a desktop width
- **THEN** six tables appear in three rows of two

#### Scenario: Dynasty layout
- **WHEN** the dynasty page is shown on a desktop width
- **THEN** five tables appear, with the DEF table centred on the last row

#### Scenario: Phone layout
- **WHEN** the page is shown at 375px width
- **THEN** the tables stack in one column with no horizontal page scroll

### Requirement: Expanded list
Each table SHALL have an expand control that opens a scrollable overlay listing every player with a WAR at that position for the selected season or mode, with columns rank, name, NFL team, Manager, games played (GP), points scored (PS), the position's stat columns, WAR, and year in All-Time Seasons mode. The table SHALL be the overlay's only scroll area: it fills the overlay's height below the title and hint, and the overlay itself never scrolls. Below 600 px the name column SHALL stay pinned to the table's left edge while the table scrolls sideways.

#### Scenario: Open the full list
- **WHEN** the visitor expands the RB table for 2024
- **THEN** an overlay lists every 2024 running back with a WAR, most WAR first, with the RB stat columns

#### Scenario: Close
- **WHEN** the visitor closes the overlay
- **THEN** the page is as it was, with the same season selected

#### Scenario: One scroll bar
- **WHEN** the quarterback list for 2026 is longer than the screen
- **THEN** only the table scrolls, its header stays in view, and the overlay's title and close button never scroll away

#### Scenario: Scroll sideways on a phone
- **WHEN** a visitor on a phone scrolls the quarterback list to the right
- **THEN** the player names stay at the left edge beside the stat columns
