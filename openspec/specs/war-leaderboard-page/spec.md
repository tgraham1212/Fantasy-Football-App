# war-leaderboard-page Specification

## Purpose

The Player WAR sub-tab of each league page: per-position leaderboards for a season or all time, an expanded sortable list with stats, the Manager who held each Player, and an explanation of the calculation drawn from the league's own data. It delivers need 3, Player Value, on the page; the calculation is in `player-war` and `Calculations.txt`, section 16.

## Requirements

### Requirement: 3.2 Player WAR sub-tab
The Player WAR sub-tab SHALL show per-position leaderboards of Player WAR for a chosen season or all time.

**Traces to:** 3; 9.1.1
**Verified by:** Test: `tests/layout/test_war_page.py::test_leaderboards_show_the_top_ten_per_position`

#### Scenario: Open the sub-tab
- **WHEN** a visitor picks "Player WAR"
- **THEN** the league's WAR leaderboards are shown

### Requirement: 3.2.1 Opens on the current season
The Player WAR sub-tab SHALL open on the league's current season.

**Traces to:** 3.2
**Verified by:** Test: `tests/layout/test_war_page.py::test_season_control_and_cut_note`

#### Scenario: Default season
- **WHEN** a visitor opens the sub-tab in November 2026
- **THEN** the 2026 leaderboards are shown

### Requirement: 3.2.1.1 Season list
The season control SHALL list every season with a WAR file, newest first, followed by "All-Time".

**Traces to:** 3.2.1
**Verified by:** Test: `tests/layout/test_war_page.py::test_season_control_and_cut_note`

#### Scenario: Redraft seasons
- **WHEN** the redraft league has WAR files for 2021 to 2026
- **THEN** the control lists 2026 down to 2021, then All-Time

### Requirement: 3.2.1.2 Current season label
While the current season is in progress, its entry SHALL read "<season> (through week N)", N being the last scored week.

**Traces to:** 3.2.1; 3.2.1.1
**Verified by:** Test: `tests/layout/test_war_page.py::test_season_control_and_cut_note`

#### Scenario: Week 11
- **WHEN** week 10 is the last scored week of 2026
- **THEN** the entry reads "2026 (through week 10)"

### Requirement: 3.2.1.3 Cut note
The page SHALL say which replacement cut the shown season uses, a yearly or a merged cut, with no note for a weekly cut.

**Rationale:** Calculations.txt section 16 describes the three cuts.
**Traces to:** 3.2.1; 8
**Verified by:** Test: `tests/layout/test_war_page.py::test_season_control_and_cut_note`

#### Scenario: Past season
- **WHEN** the visitor picks 2023
- **THEN** the yearly-cut note is shown

#### Scenario: Partly captured season
- **WHEN** the visitor views 2026, whose WAR file is marked merged
- **THEN** the merged-cut note is shown instead of the yearly one

### Requirement: 3.2.2 Leaderboards
The page SHALL show one table per lineup position with that position's top 10 Players by WAR, in the order QB, RB, WR, TE, DEF and K.

**Traces to:** 3.2
**Verified by:** Test: `tests/layout/test_war_page.py::test_leaderboards_show_the_top_ten_per_position`

#### Scenario: Redraft tables
- **WHEN** the redraft sub-tab is shown
- **THEN** six tables appear, each listing its top 10 Players by WAR

#### Scenario: Dynasty tables
- **WHEN** the dynasty sub-tab is shown
- **THEN** five tables appear, with no kicker table

### Requirement: 3.2.2.1 Leaderboard columns
Each leaderboard SHALL have the columns rank, name, NFL team, Manager and WAR.

**Traces to:** 3.2.2
**Verified by:** Test: `tests/layout/test_war_page.py::test_leaderboards_show_the_top_ten_per_position`

#### Scenario: Header row
- **WHEN** a season's leaderboards are shown
- **THEN** each reads "#", "Name", "NFL", "Manager" and "WAR"

### Requirement: 3.2.2.2 Two columns
At 1280 px wide, the leaderboards SHALL sit in two columns, with a table alone on the last row centred.

**Traces to:** 3.2.2
**Verified by:** Inspection: the live site at 1280 px, both leagues' grids

#### Scenario: Dynasty layout
- **WHEN** the dynasty sub-tab is shown at 1280 px
- **THEN** the DEF table is centred on the last row

### Requirement: 3.2.2.3 Leaderboards on a phone
At every tested phone width, the leaderboards SHALL stack in one column with no sideways page scrolling.

**Traces to:** 3.2.2; 9.2
**Verified by:** Test: `tests/layout/test_layout.py::test_wide_fonts_do_not_scroll_sideways`

#### Scenario: Phone layout
- **WHEN** the sub-tab is shown at 360 px
- **THEN** the tables stack in one column with no sideways page scrolling

### Requirement: 3.2.3 All-Time modes
With All-Time selected, a toggle SHALL switch between "Seasons", every Player-season ranked together with a year column, and "Career", one row per Player with his WAR summed over his seasons in the league and a seasons-played column.

**Traces to:** 3.2; 3.2.1.1
**Verified by:** Test: `tests/layout/test_war_page.py::test_all_time_modes`

#### Scenario: Seasons mode
- **WHEN** All-Time is selected
- **THEN** Kupp 2021 and McCaffrey 2025 appear as separate rows with their years

#### Scenario: Career mode
- **WHEN** the visitor switches to Career
- **THEN** each Player appears once with his summed WAR and number of seasons

### Requirement: 3.2.3.1 Seasons by default
"Seasons" SHALL be the All-Time default.

**Traces to:** 3.2.3
**Verified by:** Test: `tests/layout/test_war_page.py::test_all_time_modes`

#### Scenario: First pick of All-Time
- **WHEN** a visitor picks All-Time
- **THEN** the Seasons button is selected

### Requirement: 3.2.4 Manager shown
The Manager shown for a Player-season SHALL be the one whose roster held the Player at the end of that season, or holds him now in the season in progress.

**Traces to:** 3.2
**Verified by:** Test: `tests/test_war.py::test_owner_attribution`; Test: `tests/test_war.py::test_build_war_weekly_cut_and_in_progress_owner`

#### Scenario: Traded mid-season
- **WHEN** a Player was traded from Manager A to Manager B in week 8 of a completed season
- **THEN** the row shows B

### Requirement: 3.2.4.1 Other holders on hover
Hovering over the Manager SHALL list every other Manager who held the Player during that season.

**Traces to:** 3.2.4
**Verified by:** Test: `tests/layout/test_war_page.py::test_manager_cell_lists_other_holders_and_dashes_the_unrostered`

#### Scenario: Traded mid-season
- **WHEN** a visitor hovers over B on that Player's row
- **THEN** the tooltip reads "Also held by: A"

### Requirement: 3.2.4.2 Unrostered Player
A Player no team held that season SHALL show a dash in place of a Manager.

**Traces to:** 3.2.4
**Verified by:** Test: `tests/layout/test_war_page.py::test_manager_cell_lists_other_holders_and_dashes_the_unrostered`

#### Scenario: Never rostered
- **WHEN** no roster held the Player that season
- **THEN** the Manager cell shows a dash

### Requirement: 3.2.4.3 Career Manager
In Career mode, the Manager shown SHALL be the one from the Player's latest season.

**Traces to:** 3.2.4; 3.2.3
**Verified by:** Inspection: `site/war.js`, the career rows take Manager, team and name from the latest season

#### Scenario: Player who moved teams
- **WHEN** a Player was on Manager A's roster in 2024 and Manager B's in 2026
- **THEN** his Career row shows B

### Requirement: 3.2.5 Expanded list
Each leaderboard's expand control SHALL open an overlay listing every Player with a WAR at that position for the selected season or mode, most WAR first, with the columns rank, name, NFL team, Manager, games played (GP), points scored (PS), the position's stat columns and WAR, plus the year in All-Time Seasons mode.

**Traces to:** 3.2; 3.2.2
**Verified by:** Test: `tests/layout/test_war_page.py::test_expanded_list_lists_every_player_with_the_position_columns`

#### Scenario: Open the full list
- **WHEN** the visitor expands the RB table for 2024
- **THEN** an overlay lists every 2024 running back with a WAR, most WAR first, with the RB stat columns

### Requirement: 3.2.5.1 One scroll area
The overlay's table SHALL be its only scroll area, filling the overlay below the title and hint.

**Traces to:** 3.2.5
**Verified by:** Test: `tests/layout/test_layout.py::test_full_list_scrolls_only_its_table`

#### Scenario: One scroll bar
- **WHEN** the quarterback list for 2026 is longer than the screen
- **THEN** only the table scrolls, its header stays in view, and the title and close button never scroll away

### Requirement: 3.2.5.2 Pinned names on a phone
Below 600 px wide, the overlay's name column SHALL stay pinned at the table's left edge while the table scrolls sideways.

**Traces to:** 3.2.5; 9.2
**Verified by:** Test: `tests/layout/test_layout.py::test_war_full_list_pins_the_name_column_on_phones`

#### Scenario: Scroll sideways on a phone
- **WHEN** a visitor on a phone scrolls the quarterback list to the right
- **THEN** the Player names stay at the left edge beside the stat columns

### Requirement: 3.2.5.3 Closing the overlay
Closing the overlay SHALL leave the page as it was, with the same season selected.

**Traces to:** 3.2.5
**Verified by:** Test: `tests/layout/test_war_page.py::test_expanded_list_lists_every_player_with_the_position_columns`

#### Scenario: Close
- **WHEN** the visitor closes the overlay
- **THEN** the page is as it was, with the same season selected

### Requirement: 3.2.6 Position stat columns
The expanded list's stat columns SHALL depend on the position:
- QB: pass yds, pass TD, INT, rush yds, rush TD;
- RB: rush yds, rush TD, rec, rec yds, rec TD;
- WR and TE: rec, rec yds, rec TD, rush yds;
- K: FG made, FG att, XP made;
- DEF: sacks, INT, fumble rec, TD, points allowed per game.

**Traces to:** 3.2; 3.2.5
**Verified by:** Test: `tests/layout/test_war_page.py::test_expanded_list_lists_every_player_with_the_position_columns`

#### Scenario: Quarterback columns
- **WHEN** the QB list is expanded
- **THEN** the stat columns are pass yds, pass TD, INT, rush yds and rush TD

### Requirement: 3.2.6.1 Stat totals
Every stat column SHALL be a season total from the stored stat lines, except points allowed per game, the mean over games played.

**Traces to:** 3.2.6
**Verified by:** Test: `tests/test_war.py::test_stat_totals_sum_and_points_allowed_per_game`

#### Scenario: Defense points allowed
- **WHEN** a defense allowed 260 points over 13 games
- **THEN** its points allowed per game shows 20.0

### Requirement: 3.2.7 Expanded list sorting
Every column of the expanded list SHALL sort from its header as the Forecast table does: descending on the first click (name and Manager A to Z), ascending on the second, with the sorted header filled and marked by an arrow.

**Traces to:** 3.2; 3.2.5; 1.3.10
**Verified by:** Test: `tests/layout/test_war_page.py::test_expanded_list_sorts_from_its_headers`

#### Scenario: Sort by points
- **WHEN** the visitor clicks "PS" once in the expanded list
- **THEN** rows are ordered by points scored, highest first, and that header shows the fill and a down arrow

### Requirement: 3.2.8 Calculation explained
The page SHALL end with a flow chart of the calculation: start percentage, consensus lineup, slot means and spread, replacement cut, weekly win probability, season sum and the replacement baseline.

**Traces to:** 3.2; 8
**Verified by:** Inspection: the live site, the flow chart below the leaderboards

#### Scenario: Reading the method
- **WHEN** a visitor scrolls past the leaderboards
- **THEN** the flow chart shows each step from start percentage to WAR

### Requirement: 3.2.8.1 Worked example
Below the flow chart, the page SHALL walk week by week through Kittle and Bowers in 2024, using the selected league's own weekly scores, win probabilities, expected wins and WAR.

**Traces to:** 3.2.8
**Verified by:** Test: `tests/layout/test_war_page.py::test_worked_example_uses_the_leagues_2024_weeks`

#### Scenario: Walkthrough numbers
- **WHEN** the redraft sub-tab is shown
- **THEN** the walkthrough lists each 2024 week for both Players and ends with both expected-wins totals and WARs

### Requirement: 3.2.8.2 Missed weeks
A week a Player did not play SHALL read "Bye" or "Out" in the worked example, with no score or win probability.

**Traces to:** 3.2.8; 3.2.8.1
**Verified by:** Test: `tests/layout/test_war_page.py::test_worked_example_uses_the_leagues_2024_weeks`

#### Scenario: Kittle's missed weeks
- **WHEN** Kittle did not play in a 2024 week
- **THEN** that week reads Bye or Out for him

### Requirement: 3.2.8.3 No 2024 file
A league without a 2024 WAR file SHALL show the flow chart without the worked example.

**Traces to:** 3.2.8; 3.2.8.1
**Verified by:** Inspection: `site/war.js`, the worked example is hidden when the 2024 file or either Player's series is missing

#### Scenario: Newer league
- **WHEN** a league's first WAR file is 2025
- **THEN** the flow chart shows and the worked example does not

### Requirement: 3.2.9 Leaderboard data exported
Each league's site data SHALL include, in one file per season with a WAR file, every qualifying Player's name, position, NFL team, Manager attribution, games, points, position stats and WAR, the season's cut and the week it runs through, and the weekly series of the two worked-example Players.

**Traces to:** 3.2; 3
**Verified by:** Test: `tests/test_export.py::test_export_writes_war_leaderboards_index_and_walkthrough`

#### Scenario: Files per season
- **WHEN** the export runs with WAR files for 2021 to 2026
- **THEN** the redraft site data has one leaderboard file per season and the page lists those seasons

### Requirement: 3.2.9.1 Export without WAR
The export SHALL succeed for a league with no WAR files, leaving the Player WAR sub-tab to say that WAR is not yet available.

**Traces to:** 3.2.9
**Verified by:** Test: `tests/test_export.py::test_export_without_war_files_has_no_war_entry`

#### Scenario: No WAR yet
- **WHEN** the export runs on a store without WAR files
- **THEN** the site builds and the Player WAR sub-tab says WAR is not yet available
