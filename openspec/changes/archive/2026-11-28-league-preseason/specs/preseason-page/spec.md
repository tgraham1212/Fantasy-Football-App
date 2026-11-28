## Purpose

The League sub-tab's Preseason tab: each season's preseason Forecast from `preseason-forecast` as a table of grades, shares with bars, forecast record, points per week, Wins Saved and the actual finish, with the Season picker, the 13 grade colours and their key, and the phone layout. It delivers need 1, Season Forecasts, on the page; its layout serves need 9, Usable by Every Manager.

## ADDED Requirements

### Requirement: 4.9.8 Preseason tab
The League sub-tab SHALL have a Preseason tab, after Draft, showing each season's preseason Forecast.

**Traces to:** 4.9; 1.5
**Verified by:** Test: `tests/layout/test_preseason_page.py::test_preseason_tab_opens`

#### Scenario: Open the tab
- **WHEN** a visitor picks "Preseason" in the League sub-tab
- **THEN** the latest season's preseason Forecast is shown

### Requirement: 4.9.8.1 Preseason season picker
The tab SHALL offer every season with a preseason Forecast in a Season picker, the latest first and selected on opening.

**Traces to:** 4.9.8
**Verified by:** Test: `tests/layout/test_preseason_page.py::test_season_picker`

#### Scenario: Redraft seasons
- **WHEN** a visitor opens the redraft league's Preseason tab
- **THEN** the picker lists 2026 back to 2021, with 2026 selected

### Requirement: 4.9.8.2 Preseason season in the URL
The page URL SHALL name the Preseason season, so that opening a link shows it.

**Traces to:** 4.9.8; 4.9.1
**Verified by:** Test: `tests/layout/test_preseason_page.py::test_url_names_the_season`

#### Scenario: Link to 2023
- **WHEN** a visitor opens a link to the dynasty 2023 Preseason tab
- **THEN** the 2023 dynasty preseason Forecast is shown

### Requirement: 4.9.8.3 Preseason table
The tab SHALL show one row per team with the columns Grade, Manager, Title, Playoffs, Last, Forecast, Pts/Wk, Wins Saved and Finished, ordered by title share, highest first, on opening.

**Traces to:** 4.9.8; 1.5.4
**Verified by:** Test: `tests/layout/test_preseason_page.py::test_table_columns_and_order`

#### Scenario: 2025 redraft
- **WHEN** a visitor views the 2025 redraft preseason Forecast
- **THEN** the first row is the team with the highest title share, and a finished season's Finished column holds each team's final place

### Requirement: 4.9.8.3.1 Share bars
Each of the Title, Playoffs and Last cells SHALL show its share as a number and as a bar whose length is the share of the full width, 0% to 100%.

**Traces to:** 4.9.8.3
**Verified by:** Test: `tests/layout/test_preseason_page.py::test_share_bars`

#### Scenario: 50% playoff share
- **WHEN** a team's playoff share is 50%
- **THEN** its playoff bar fills half its track, within 1 px

### Requirement: 4.9.8.3.2 Sortable preseason table
Each column of the preseason table SHALL sort the table when its header is pressed.

**Traces to:** 4.9.8.3
**Verified by:** Test: `tests/layout/test_preseason_page.py::test_table_sorting`

#### Scenario: Sort by Wins Saved
- **WHEN** a visitor presses the Wins Saved header
- **THEN** the teams are listed from the most Wins Saved to the fewest

### Requirement: 4.9.8.3.4 Draft Strength column
For a redraft season, the preseason table SHALL add a Draft Strength column after Pts/Wk giving each team's draft strength rank as an ordinal.

**Traces to:** 4.9.8.3; 1.5.6.1
**Verified by:** Test: `tests/layout/test_preseason_page.py::test_draft_strength_column`

#### Scenario: Redraft and dynasty
- **WHEN** a visitor views a redraft season and then a dynasty season
- **THEN** the redraft table shows Draft Strength, 1st to 12th, and the dynasty table has no such column

### Requirement: 4.9.8.4 Grade colours
Each of the 13 grades SHALL have its own badge colour, the same hue within a letter and darker toward A+ and toward D-, with text contrast of at least 4.5:1 in light and dark modes.

**Traces to:** 4.9.8; 9.7
**Verified by:** Test: `tests/test_colour_contrast.py::test_preseason_grade_badges`

#### Scenario: Dark mode
- **WHEN** the page is shown in dark mode
- **THEN** every grade badge keeps text contrast of at least 4.5:1

### Requirement: 4.9.8.5 Grades explained
The tab SHALL show a key of the grade letters with their bands and a note on how the preseason Forecast is made, below the table.

**Traces to:** 4.9.8; 1.5.5
**Verified by:** Test: `tests/layout/test_preseason_page.py::test_key_and_note`

#### Scenario: Key
- **WHEN** a visitor views the tab
- **THEN** the key lists A Title Contender, B Playoff Team, C Playoff Bubble, D Unlikely Playoffs and F Last Place with their bands

### Requirement: 4.9.8.3.3 Preseason table on phones
On screens narrower than 600 px, the tab SHALL show each team as a list row with its grade, Manager, final place, the three shares, forecast record and Wins Saved.

**Traces to:** 4.9.8.3; 9.2.1
**Verified by:** Test: `tests/layout/test_preseason_page.py::test_phone_rows`

#### Scenario: 360 px phone
- **WHEN** a visitor on a 360 px screen opens the tab
- **THEN** each team is one list row, nothing is cut off and the page does not scroll sideways
