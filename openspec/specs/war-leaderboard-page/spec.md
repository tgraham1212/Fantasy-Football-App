# war-leaderboard-page Specification

## Purpose

The Player WAR page of each league: per-position leaderboards for a season or all time, an expanded sortable list with stats, owner attribution, and an explanation of the calculation drawn from the league's own data.

## Requirements

### Requirement: Season control
The Player WAR page SHALL default to the league's current season, labelled with the last scored week it runs through, and SHALL offer a dropdown of every season the league has a WAR file for plus an "All-Time" entry. Seasons before the first weekly-cut season SHALL be noted on the page as using a yearly replacement cut.

#### Scenario: Default season
- **WHEN** a visitor opens the Player WAR page in November 2026
- **THEN** the 2026 leaderboards are shown with a label saying they run through week 9

#### Scenario: Past season
- **WHEN** the visitor picks 2023
- **THEN** the 2023 leaderboards are shown with the yearly-cut note

### Requirement: Position leaderboards
The page SHALL show one table per lineup position with the top 10 players by WAR, laid out in two columns in the order QB and RB, WR and TE, DEF and K. A league without a position SHALL omit that table, and a table left alone on the last row SHALL be centred. Compact columns SHALL be rank, name, NFL team, fantasy owner and WAR.

#### Scenario: Redraft layout
- **WHEN** the redraft page is shown on a desktop width
- **THEN** six tables appear in three rows of two

#### Scenario: Dynasty layout
- **WHEN** the dynasty page is shown on a desktop width
- **THEN** five tables appear, with the DEF table centred on the last row

#### Scenario: Phone layout
- **WHEN** the page is shown at 375px width
- **THEN** the tables stack in one column with no horizontal page scroll

### Requirement: All-Time modes
With "All-Time" selected, a toggle SHALL switch between "Seasons" (every player-season ranked together, with a year column) and "Career" (one row per player, WAR summed across their seasons in the league, with a seasons-played column). "Seasons" SHALL be the default.

#### Scenario: Seasons mode
- **WHEN** All-Time is selected
- **THEN** Kupp 2021 and McCaffrey 2025 appear as separate rows with their years

#### Scenario: Career mode
- **WHEN** the visitor switches to Career
- **THEN** each player appears once with their summed WAR and number of seasons

### Requirement: Owner attribution
The fantasy owner shown for a player-season SHALL be the manager whose roster held the player at the end of that season, or the current roster for the season in progress. Hovering the owner SHALL list any other managers who held the player during that season. A player no team held SHALL show a dash. In Career mode the owner SHALL be the one from the player's latest season.

#### Scenario: Traded mid-season
- **WHEN** a player was traded from manager A to manager B in week 8 of a completed season
- **THEN** the row shows B, and hovering it lists A

#### Scenario: Never rostered
- **WHEN** no roster held the player that season
- **THEN** the owner cell shows a dash

### Requirement: Expanded list
Each table SHALL have an expand control that opens a scrollable overlay listing every player with a WAR at that position for the selected season or mode, with columns rank, name, NFL team, owner, games played (GP), points scored (PS), the position's stat columns, WAR, and year in All-Time Seasons mode.

#### Scenario: Open the full list
- **WHEN** the visitor expands the RB table for 2024
- **THEN** an overlay lists every 2024 running back with a WAR, most WAR first, with the RB stat columns

#### Scenario: Close
- **WHEN** the visitor closes the overlay
- **THEN** the page is as it was, with the same season selected

### Requirement: Position stat columns
The expanded list's stat columns SHALL depend on the position: QB pass yds, pass TD, INT, rush yds, rush TD; RB rush yds, rush TD, rec, rec yds, rec TD; WR and TE rec, rec yds, rec TD, rush yds; K FG made, FG att, XP made; DEF sacks, INT, fumble rec, TD, points allowed per game. All SHALL be season totals from the stored stat lines except points allowed per game, which is the mean over games played.

#### Scenario: Quarterback columns
- **WHEN** the QB list is expanded
- **THEN** the stat columns are pass yds, pass TD, INT, rush yds and rush TD

#### Scenario: Defense points allowed
- **WHEN** a defense allowed 260 points over 13 games
- **THEN** its points allowed per game shows 20.0

### Requirement: Expanded list sorting
Every column of the expanded list SHALL be sortable from its header with the same behaviour as the odds table: first click descending (name and owner A to Z), second click ascending, sorted header shown with a dark fill and arrow, no fill or arrow until a header is clicked.

#### Scenario: Sort by points
- **WHEN** the visitor clicks "PS" once in the expanded list
- **THEN** rows are ordered by points scored, highest first, and that header shows the fill and a down arrow

### Requirement: Calculation explained
The page SHALL end with an explanation of the calculation: a flow chart from start percentage to consensus lineup, slot means and spread, replacement cut, weekly win probability, season sum and the replacement baseline, followed by a week-by-week walkthrough of Kittle and Bowers in 2024 using the selected league's own weekly scores, win probabilities, replacement fills and totals. When the league has no 2024 file the walkthrough SHALL be omitted and the flow chart kept.

#### Scenario: Walkthrough numbers
- **WHEN** the redraft page is shown
- **THEN** the walkthrough lists each 2024 week for both players with the score used and its win probability, marks Kittle's missed weeks as replacement fills, and ends with both expected-wins totals and WARs

### Requirement: Leaderboard data exported
Each league's site data SHALL include, per season with a WAR file, every qualifying player's name, position, NFL team, owner attribution, games, points, position stats and WAR, plus the season's cut mode and week it runs through, and the weekly series for the two walkthrough players, in files the page loads per season. The export SHALL succeed for a league with no WAR files, and the page SHALL then say WAR is not yet available.

#### Scenario: Files per season
- **WHEN** the export runs with WAR files for 2021 to 2026
- **THEN** the redraft site data has one leaderboard file per season and the page lists those seasons

#### Scenario: No WAR yet
- **WHEN** the export runs on a store without WAR files
- **THEN** the site builds and the Player WAR page says WAR is not yet available
