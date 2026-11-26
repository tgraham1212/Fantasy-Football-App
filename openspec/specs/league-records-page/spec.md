# league-records-page Specification

## Purpose

The League sub-tab of each league page and its first tab, Records: the Managers and Players views of the league records in `league-records`, the record pop-up, game tags and the phone layout. It delivers need 4, Manager History, and need 3, Player Value, on the page; its layout serves need 9, Usable by Every Manager.

## Requirements

### Requirement: 4.9 League sub-tab
The League sub-tab SHALL show league-wide information for the current and past seasons in tabs of its own, the first being Records.

**Rationale:** The Managers sub-tab covers one Manager; this sub-tab covers the whole league.
**Traces to:** 4; 9.1.1
**Verified by:** Test: `tests/layout/test_league_records_page.py::test_league_tab_opens_on_records`

#### Scenario: Open League
- **WHEN** a visitor picks "League"
- **THEN** the Records tab is shown with its Managers view

### Requirement: 4.9.1 Tab and view in the URL
The page URL SHALL name the League sub-tab's selected tab and Records view, so that opening a link shows them.

**Traces to:** 4.9; 9.1.1.1
**Verified by:** Test: `tests/layout/test_league_records_page.py::test_url_names_the_tab_and_view`

#### Scenario: Link to the Players view
- **WHEN** a visitor opens a link to the redraft League Records Players view
- **THEN** that view is shown

### Requirement: 4.9.2 Records views
The Records tab SHALL show a Managers view and a Players view, switched by a two-button control.

**Traces to:** 4.9
**Verified by:** Test: `tests/layout/test_league_records_page.py::test_view_switch`

#### Scenario: Switch to Players
- **WHEN** a visitor picks "Players"
- **THEN** the Players view replaces the Managers view and "Players" shows as pressed

### Requirement: 4.9.2.1 Managers view
The Managers view SHALL show four sections in this order: Champions, All-Time Standings, Weekly Records and Season Records.

**Traces to:** 4.9.2; 4.8
**Verified by:** Test: `tests/layout/test_league_records_page.py::test_managers_view_sections`

#### Scenario: Section order
- **WHEN** the Managers view opens
- **THEN** Champions comes first and Season Records last

### Requirement: 4.9.2.1.1 Champions table
Champions SHALL list finished seasons newest first, each with the champion's picture, name and that season's Team Name, the runner-up, the toilet bowl champion (Last Place where there is none), record, points scored, and best Player with his position, NFL team and WAR.

**Traces to:** 4.9.2.1; 4.8.3
**Verified by:** Test: `tests/layout/test_league_records_page.py::test_champions_table`

#### Scenario: Dynasty column
- **WHEN** the dynasty Champions table is shown
- **THEN** its fourth column is headed "Last Place"

### Requirement: 4.9.2.1.2 All-time standings table
All-Time Standings SHALL show each Manager's rank, regular-season record, win % to three decimals without the leading zero, point differential, playoff appearances and record, and counts of 1st, 2nd and 3rd finishes and toilet bowl or last place finishes.

**Traces to:** 4.9.2.1; 4.8.4
**Verified by:** Test: `tests/layout/test_league_records_page.py::test_standings_table`

#### Scenario: Win percentage
- **WHEN** a Manager has won 70% of regular-season games
- **THEN** their win % reads ".700"

### Requirement: 4.9.2.1.2.1 Former Managers
Former Managers SHALL appear after the current ones under a "Former Managers" heading, without a rank.

**Traces to:** 4.9.2.1.2; 4.8.4.2
**Verified by:** Test: `tests/layout/test_league_records_page.py::test_standings_table`

#### Scenario: Retired Manager
- **WHEN** a Manager last played in 2023
- **THEN** they are listed under "Former Managers" with no rank

### Requirement: 4.9.2.1.3 Record rows
Weekly Records and Season Records SHALL show one row per league record with its holder and when it was set, the value of its first entry, and, for weekly records, the opponent and the game's tags or, for season records, the season result.

**Traces to:** 4.9.2.1; 4.8.5; 4.8.6
**Verified by:** Test: `tests/layout/test_league_records_page.py::test_record_rows`

#### Scenario: Season row
- **WHEN** Most Points is held by a 2021 season that finished 3rd
- **THEN** its row shows the holder, 2021, the points and a 3rd pill

### Requirement: 4.9.2.1.3.1 Luck explained
The luck records SHALL explain luck on hover and keyboard focus, and at the top of their pop-ups: "Each week your score plays all 11 other teams, so beating 8 of them counts as 8/11 of a win, and luck is actual wins minus those fractions."

**Traces to:** 4.9.2.1.3; 4.8.6.3
**Verified by:** Test: `tests/layout/test_league_records_page.py::test_luck_explained`

#### Scenario: Hover
- **WHEN** a visitor hovers over "Luckiest Season"
- **THEN** the explanation is shown

### Requirement: 4.9.2.1.3.2 Current season marker
A season entry from the current season SHALL carry an asterisk, explained by a note under its table.

**Traces to:** 4.9.2.1.3; 4.8.6.4
**Verified by:** Test: `tests/layout/test_league_records_page.py::test_record_rows`

#### Scenario: Season under way
- **WHEN** a lineup-choices record is held by the current season
- **THEN** its year reads "2026*" and the note "* Current season, so far" is shown

### Requirement: 4.9.3 Record pop-up
Selecting a league record SHALL open a pop-up listing its top 25 entries with rank, value, holder and when each was set, ranks 1 to 3 in gold, silver and bronze.

**Traces to:** 4.9; 4.8.2
**Verified by:** Test: `tests/layout/test_league_records_page.py::test_record_popup`

#### Scenario: Biggest blowout
- **WHEN** a visitor selects Biggest Blowout
- **THEN** a pop-up lists its 25 entries, the first three ranks in gold, silver and bronze

### Requirement: 4.9.3.1 Pop-up on phones
On phone widths the record pop-up SHALL open as a sheet from the bottom of the screen with a close button at least 48 by 48 px.

**Traces to:** 4.9.3; 9.6
**Verified by:** Test: `tests/layout/test_league_records_page.py::test_record_popup`

#### Scenario: 360 px
- **WHEN** a visitor at 360 px selects a record
- **THEN** a sheet rises from the bottom with a 48 px close button

### Requirement: 4.9.2.1.3.3 Game tags
A weekly entry SHALL carry a tag for its game's kind and another when it is from the current season: Playoffs in green, Championship in gold, 3rd Place in bronze, Toilet Bowl and Toilet Bowl Final in brown, and This season in blue.

**Traces to:** 4.9.2.1.3; 4.8.5.2
**Verified by:** Test: `tests/layout/test_league_records_page.py::test_record_rows`

#### Scenario: Toilet bowl final
- **WHEN** an entry comes from a toilet bowl final
- **THEN** it carries a brown "Toilet Bowl Final" tag

### Requirement: 4.9.2.1.3.4 Lineup choices explained
The lineup-choices records SHALL explain on hover, on keyboard focus and atop their pop-ups that the figure is the starters' points minus those of the roster's highest Sleeper projections.

**Rationale:** The figure is set against Sleeper's projections, not the best lineup in hindsight, so it can be positive.
**Traces to:** 4.9.2.1.3; 2.8
**Verified by:** Test: `tests/layout/test_league_records_page.py::test_lineup_choices_explained`

#### Scenario: Hover
- **WHEN** a visitor hovers over "Most Points Gained by Lineup Choices"
- **THEN** "Your starters' points minus what starting your roster's highest Sleeper projections would have scored; following the projections scores 0." is shown

### Requirement: 4.9.2.2 Players view
The Players view SHALL show four cards (Best Games, Best Bench Games, Career Scoring and Championships), each with its top 5 entries and a control that opens its top 25.

**Traces to:** 4.9.2; 3.6
**Verified by:** Test: `tests/layout/test_league_records_page.py::test_players_view`

#### Scenario: Career Scoring
- **WHEN** the Players view opens
- **THEN** Career Scoring shows its top 5 Players with games, points and points per game

### Requirement: 4.9.2.2.1 Position filter
Each Players card SHALL filter by position with buttons in this order, styled as the roster position badges: All, QB, RB, WR, TE, DEF, K.

**Traces to:** 4.9.2.2; 3.6
**Verified by:** Test: `tests/layout/test_league_records_page.py::test_players_view`

#### Scenario: Quarterbacks
- **WHEN** a visitor picks QB on Best Games
- **THEN** the card shows the five best QB games

### Requirement: 4.9.4 Pictures with names
Each Manager name SHALL carry the team logo, else the Sleeper avatar, and each Player name the Player's photo and position badge, as on the Managers sub-tab.

**Traces to:** 4.9; 4.4.6
**Verified by:** Test: `tests/layout/test_league_records_page.py::test_pictures_with_names`

#### Scenario: No logo
- **WHEN** a Manager has no team logo
- **THEN** their Sleeper avatar is shown

### Requirement: 4.9.5 Records on phones
On phone widths each Records table SHALL become a list of rows that fits the screen without scrolling sideways, without the game score lines.

**Traces to:** 4.9; 9.2
**Verified by:** Test: `tests/layout/test_league_records_page.py::test_phone_lists`

#### Scenario: Weekly Records at 360 px
- **WHEN** Weekly Records is shown at 360 px
- **THEN** each record is one row with its value, holder and opponent, and no score line
