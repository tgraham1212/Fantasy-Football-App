## MODIFIED Requirements

### Requirement: Season control
The Player WAR page SHALL default to the league's current season, labelled with the last scored week it runs through, and SHALL offer a dropdown of every season the league has a WAR file for plus an "All-Time" entry. The page SHALL say which replacement cut the shown season uses:

- **Yearly:** one start-percentage snapshot for the season.
- **Merged:** weekly snapshots where they exist, and otherwise each player's start percentage from the weeks he played, or his ownership when he was not seen active.
- **Weekly:** no note.

#### Scenario: Default season
- **WHEN** a visitor opens the Player WAR page in November 2026
- **THEN** the 2026 leaderboards are shown with a label saying they run through week 9

#### Scenario: Past season
- **WHEN** the visitor picks 2023
- **THEN** the 2023 leaderboards are shown with the yearly-cut note

#### Scenario: Partly captured season
- **WHEN** the visitor views 2026, whose WAR file is marked merged
- **THEN** the page shows the merged-cut note instead of the yearly-cut note
