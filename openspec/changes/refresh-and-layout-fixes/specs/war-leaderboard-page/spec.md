# Spec Delta

## MODIFIED Requirements

### Requirement: Expanded list
Each table SHALL have an expand control that opens a scrollable overlay listing every player with a WAR at that position for the selected season or mode, with columns rank, name, NFL team, owner, games played (GP), points scored (PS), the position's stat columns, WAR, and year in All-Time Seasons mode. The table SHALL be the overlay's only scroll area: it fills the overlay's height below the title and hint, and the overlay itself never scrolls.

#### Scenario: Open the full list
- **WHEN** the visitor expands the RB table for 2024
- **THEN** an overlay lists every 2024 running back with a WAR, most WAR first, with the RB stat columns

#### Scenario: Close
- **WHEN** the visitor closes the overlay
- **THEN** the page is as it was, with the same season selected

#### Scenario: One scroll bar
- **WHEN** the quarterback list for 2026 is longer than the screen
- **THEN** only the table scrolls, its header stays in view, and the overlay's title and close button never scroll away
