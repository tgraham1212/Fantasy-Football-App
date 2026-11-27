# strength-of-schedule-page Specification

## Purpose

The League sub-tab's Strength of Schedule tab: the Weekly Ranks and Schedule Swap views of the figures in `strength-of-schedule`, the Season selector, the heat-grid tables with their colours and sorting, and the phone layout with the Manager column pinned. It delivers need 4, Manager History, on the page; its layout serves need 9, Usable by Every Manager.

## Requirements

### Requirement: 4.9.6 Strength of Schedule tab
The League sub-tab SHALL have a Strength of Schedule tab, after Records, showing the league's strength of schedule figures.

**Traces to:** 4.9; 4.10
**Verified by:** Test: `tests/layout/test_schedule_page.py::test_schedule_tab_opens`

#### Scenario: Open the tab
- **WHEN** a visitor picks "Strength of Schedule" in the League sub-tab
- **THEN** the tab is shown with its Weekly Ranks view for the current season

### Requirement: 4.9.6.1 Strength of Schedule views
The tab SHALL show a Weekly Ranks view and a Schedule Swap view, switched by a two-button control.

**Traces to:** 4.9.6
**Verified by:** Test: `tests/layout/test_schedule_page.py::test_view_switch`

#### Scenario: Switch to Schedule Swap
- **WHEN** a visitor picks "Schedule Swap"
- **THEN** the Schedule Swap table replaces the Weekly Ranks table and "Schedule Swap" shows as pressed

### Requirement: 4.9.6.2 Season selector
The tab SHALL offer every stored season of the league in a Season selector, the current season first and selected on opening.

**Traces to:** 4.9.6
**Verified by:** Test: `tests/layout/test_schedule_page.py::test_season_selector`

#### Scenario: Finished season
- **WHEN** a visitor selects 2025 in the dynasty league
- **THEN** the tables show 2025 with every week played and no Upcoming column

### Requirement: 4.9.6.3 View and season in the URL
The page URL SHALL name the Strength of Schedule view and season, so that opening a link shows them.

**Traces to:** 4.9.6; 4.9.1
**Verified by:** Test: `tests/layout/test_schedule_page.py::test_url_names_view_and_season`

#### Scenario: Link to a past swap
- **WHEN** a visitor opens a link to the dynasty Schedule Swap for 2024
- **THEN** the 2024 Schedule Swap is shown

### Requirement: 4.9.6.4 Weekly Ranks table
The Weekly Ranks table SHALL have one row per Manager in Weekly Ranks order, giving their rank as "1st Hardest" and the like, their Season, Played and Upcoming mean opponent ranks, and one cell per regular-season week.

**Traces to:** 4.9.6; 4.10.2.1; 4.10.2.2
**Verified by:** Test: `tests/layout/test_schedule_page.py::test_weekly_ranks_table`

#### Scenario: Week 11 of 14
- **WHEN** the dynasty 2026 table is shown after week 11
- **THEN** each row has rank, Season, Played and Upcoming columns and 14 week cells

### Requirement: 4.9.6.4.1 Week cell
Each week cell SHALL show the opponent's points at the top, the opponent's weekly rank in large type and the opponent's picture, with the opponent's full name, points and rank on hover.

**Traces to:** 4.9.6.4; 4.9.4
**Verified by:** Test: `tests/layout/test_schedule_page.py::test_week_cell`

#### Scenario: Played week
- **WHEN** a Manager's week 1 opponent tg1212 scored 140.0, the 2nd most that week
- **THEN** the cell shows 140.0, a large 2 and tg1212's picture

### Requirement: 4.9.6.4.2 Weekly Ranks colours
Week cells SHALL be coloured by the opponent's weekly rank in four groups, ranks 1-3 red, 4-6 yellow, 7-9 light green and 10-12 dark green in a 12-team league, each group a quarter of the league's teams.

**Traces to:** 4.9.6.4
**Verified by:** Test: `tests/layout/test_schedule_page.py::test_weekly_ranks_colours`

#### Scenario: Rank 3 and rank 4
- **WHEN** one opponent ranked 3rd and another 4th
- **THEN** the first cell is red and the second yellow

### Requirement: 4.9.6.4.3 Forecast weeks
Week cells for upcoming weeks SHALL use the solid shade of their colour group and played weeks the faded shade, with a line before the first upcoming week under a "Forecast" heading.

**Traces to:** 4.9.6.4; 4.10.3
**Verified by:** Test: `tests/layout/test_schedule_page.py::test_projected_weeks_marked`

#### Scenario: After week 11
- **WHEN** the dynasty 2026 table is shown after week 11
- **THEN** weeks 1-11 are faded and weeks 12-14 solid, with a line before week 12

### Requirement: 4.9.6.5 Schedule Swap table
The Schedule Swap table SHALL have one row and one schedule column per Manager, both in Schedule Swap order, giving each Manager's rank as "1st Hardest" and the like, wins under each schedule with their own outlined, and Own, Avg, Index and Range columns.

**Traces to:** 4.9.6; 4.10.4.3; 4.10.4.4
**Verified by:** Test: `tests/layout/test_schedule_page.py::test_schedule_swap_table`

#### Scenario: Own schedule on the diagonal
- **WHEN** the dynasty 2026 Schedule Swap is shown
- **THEN** each Manager's own-schedule wins sit on the diagonal, outlined, to one decimal

### Requirement: 4.9.6.5.1 Schedule Swap colours
Each swap cell SHALL be coloured by its wins against the Manager's own-schedule wins: dark orange for 2 or more fewer, light orange for fewer, light blue for more, dark blue for 2 or more more, and grey when within 0.05.

**Traces to:** 4.9.6.5
**Verified by:** Test: `tests/layout/test_schedule_page.py::test_schedule_swap_colours`

#### Scenario: Two fewer wins
- **WHEN** a Manager has 8.8 wins on their own schedule and 6.8 under another
- **THEN** that cell is dark orange

### Requirement: 4.9.6.6 Cell text colour
Text in a coloured cell SHALL be a tint of the cell's colour with a contrast ratio of at least 4.5:1 against it, in light and dark modes.

**Rationale:** The tint keeps the grid calm, as in the reference design, while staying readable.
**Traces to:** 4.9.6; 9.7
**Verified by:** Test: `tests/test_colour_contrast.py::test_schedule_cells`

#### Scenario: Forecast-week dark green cell
- **WHEN** a forecast-week cell is dark green
- **THEN** its text is a pale green with at least 4.5:1 contrast

### Requirement: 4.9.6.7 Sortable columns
The Rank, Season, Played and Upcoming headers of Weekly Ranks and the Rank, Own, Avg and Index headers of Schedule Swap SHALL sort their table when picked.

**Traces to:** 4.9.6; 4.9.6.4; 4.9.6.5
**Verified by:** Test: `tests/layout/test_schedule_page.py::test_sortable_columns`

#### Scenario: Sort by Upcoming
- **WHEN** a visitor picks the Upcoming header
- **THEN** the rows reorder by Upcoming mean opponent rank, lowest first

### Requirement: 4.9.6.8 Measures explained
Each table SHALL carry a one-line note under it saying what the cells hold and which end is the hardest schedule.

**Traces to:** 4.9.6; 8
**Verified by:** Test: `tests/layout/test_schedule_page.py::test_notes_shown`

#### Scenario: Schedule Swap note
- **WHEN** the Schedule Swap view is shown
- **THEN** a note under the table says the Index is mean wins across all schedules minus own wins and the highest is the hardest

### Requirement: 4.9.6.9 Pinned Manager column on phones
On screens narrower than 600 px, each Strength of Schedule table SHALL scroll sideways inside its card with the Manager column pinned at its left edge and Manager names on one line.

**Traces to:** 4.9.6; 9.2.1
**Verified by:** Test: `tests/layout/test_schedule_page.py::test_manager_column_pinned_on_phones`

#### Scenario: Scroll Weekly Ranks on a phone
- **WHEN** a visitor at 360 px scrolls the Weekly Ranks table to week 14
- **THEN** the Manager column stays at the left edge with each name on one line

### Requirement: 4.9.6.9.1 Summary columns first on phones
On screens narrower than 600 px, the only columns between the Manager column and the week or schedule cells SHALL be the rank and the Season mean (Weekly Ranks) or the rank and Index (Schedule Swap).

**Rationale:** The ranking then reads without scrolling; Played, Upcoming, Own and Avg stay on wider screens or after the cells.
**Traces to:** 4.9.6.9
**Verified by:** Test: `tests/layout/test_schedule_page.py::test_summary_columns_first_on_phones`

#### Scenario: Swap at 360 px
- **WHEN** the Schedule Swap is shown at 360 px before any scrolling
- **THEN** Manager, Rank and Index are visible

#### Scenario: Weekly Ranks at 360 px
- **WHEN** Weekly Ranks is shown at 360 px
- **THEN** the columns before week 1 are Manager, Rank and Season, with no Played or Upcoming column
