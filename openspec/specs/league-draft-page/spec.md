# league-draft-page Specification

## Purpose

The League sub-tab's Draft tab: the Board and Table views of the figures in `league-draft`, the Season picker, the Draft Day | Results switch on the board, the grade badges and WAR colours, the Managers summary card, and the phone layouts. It delivers need 4, Manager History, on the page; its layout serves need 9, Usable by Every Manager.

## Requirements

### Requirement: 4.9.7 Draft tab
The League sub-tab SHALL have a Draft tab, after Strength of Schedule, showing the league's drafts.

**Traces to:** 4.9; 4.11
**Verified by:** Test: `tests/layout/test_draft_page.py::test_draft_tab_opens`

#### Scenario: Open the tab
- **WHEN** a visitor picks "Draft" in the League sub-tab
- **THEN** the tab is shown with its Board view for the latest stored draft

### Requirement: 4.9.7.1 Draft views
The tab SHALL show a Board view and a Table view, switched by a two-button control.

**Traces to:** 4.9.7
**Verified by:** Test: `tests/layout/test_draft_page.py::test_view_switch`

#### Scenario: Switch to the table
- **WHEN** a visitor picks "Table"
- **THEN** the table replaces the board and "Table" shows as pressed

### Requirement: 4.9.7.2 Draft season picker
The tab SHALL offer every season with a stored draft in a Season picker, the latest first and selected on opening.

**Traces to:** 4.9.7
**Verified by:** Test: `tests/layout/test_draft_page.py::test_season_picker`

#### Scenario: Dynasty seasons
- **WHEN** a visitor opens the dynasty league's Draft tab
- **THEN** the Season picker lists 2026, 2025, 2024, 2023 and 2022, with 2026 selected

### Requirement: 4.9.7.3 Draft view and season in the URL
The page URL SHALL name the Draft view and season, so that opening a link shows them.

**Traces to:** 4.9.7; 4.9.1
**Verified by:** Test: `tests/layout/test_draft_page.py::test_url_names_view_and_season`

#### Scenario: Link to a past table
- **WHEN** a visitor opens a link to the redraft 2023 Draft table
- **THEN** the 2023 redraft draft is shown as a table

### Requirement: 4.9.7.4 Draft board
The Board view SHALL show one row per round and one column per draft slot, headed by the Manager who held the slot, each cell giving the pick, Player, position and NFL team, tinted in the position's colours.

**Traces to:** 4.9.7
**Verified by:** Test: `tests/layout/test_draft_page.py::test_board_layout`

#### Scenario: Rookie draft
- **WHEN** the 2025 dynasty draft is shown as a board
- **THEN** it has 3 rows and 12 columns, and the 1.01 cell names Ashton Jeanty, RB, LV

### Requirement: 4.9.7.4.1 Traded and kept picks on the board
A board cell SHALL name the Manager who made a traded pick and mark a keeper with the word "Keeper".

**Traces to:** 4.9.7.4
**Verified by:** Test: `tests/layout/test_draft_page.py::test_board_traded_and_keeper_marks`

#### Scenario: Traded pick
- **WHEN** Z28kid86 made the 1.04 pick in CheefWiggum's column
- **THEN** the 1.04 cell names Z28kid86 with the traded-pick icon

### Requirement: 4.9.7.4.2 Grade switch
The board SHALL offer a Draft Day | Results switch that shows, in each graded cell, the pick's Steal or Reach badge or its Hit, Bust or Unlucky badge.

**Traces to:** 4.9.7.4
**Verified by:** Test: `tests/layout/test_draft_page.py::test_grade_switch`

#### Scenario: Results
- **WHEN** a visitor picks "Results"
- **THEN** each hit, bust and unlucky pick shows its badge and no Steal or Reach badge is shown

### Requirement: 4.9.7.5 Draft table
The Table view SHALL list every pick with the columns Pick, Manager, Player, ADP, ADP Rank, WAR, WAR Rank, Slot WAR, Hit/Bust and Games Played.

**Traces to:** 4.9.7
**Verified by:** Test: `tests/layout/test_draft_page.py::test_table_columns`

#### Scenario: Pick column
- **WHEN** the 2025 dynasty draft is shown as a table
- **THEN** the 13th pick's Pick cell reads "2.01 (13)"

### Requirement: 4.9.7.5.1 Steal or Reach in the Player column
The Player column SHALL end with the pick's Steal or Reach badge, when the pick has one.

**Traces to:** 4.9.7.5
**Verified by:** Test: `tests/layout/test_draft_page.py::test_player_column_badge`

#### Scenario: Steal
- **WHEN** the 3.10 pick is a steal of +10
- **THEN** its Player cell ends with "Steal +10"

### Requirement: 4.9.7.5.2 Position rank badges
The ADP Rank and WAR Rank columns SHALL give the position rank as a badge in the position's colours after the overall rank.

**Traces to:** 4.9.7.5; 4.11.3
**Verified by:** Test: `tests/layout/test_draft_page.py::test_position_rank_badges`

#### Scenario: Receiver
- **WHEN** a receiver has ADP rank 5 and ADP position rank WR2
- **THEN** his ADP Rank cell reads 5 followed by a WR2 badge in the receiver colours

### Requirement: 4.9.7.5.3 Traded picks in the table
The Manager column SHALL add "via" and the slot's original Manager under the Manager who made a traded pick.

**Traces to:** 4.9.7.5
**Verified by:** Test: `tests/layout/test_draft_page.py::test_table_via`

#### Scenario: Traded first
- **WHEN** Z28kid86 made the 1.04 pick of CheefWiggum's slot
- **THEN** the Manager cell shows Z28kid86 with "via CheefWiggum" below

### Requirement: 4.9.7.5.4 Sortable draft table
Each column of the draft table SHALL sort the table when its header is pressed, with Pick ascending on opening.

**Traces to:** 4.9.7.5
**Verified by:** Test: `tests/layout/test_draft_page.py::test_table_sorting`

#### Scenario: Sort by WAR
- **WHEN** a visitor presses the WAR header
- **THEN** the picks are listed from the most WAR to the least

### Requirement: 4.9.7.6 Grade colours
Steal badges SHALL be light blue, Reach badges light orange, Hit badges dark blue with light blue text and Bust badges dark red with light red text, each with text contrast of at least 4.5:1 in light and dark modes.

**Traces to:** 4.9.7; 9.7
**Verified by:** Test: `tests/test_colour_contrast.py::test_draft_badges`

#### Scenario: Dark mode
- **WHEN** the page is shown in dark mode
- **THEN** every Steal, Reach, Hit and Bust badge keeps text contrast of at least 4.5:1

### Requirement: 4.9.7.6.1 WAR colours
WAR values on the Draft tab SHALL show in blue when positive and red when negative, with text contrast of at least 4.5:1 in light and dark modes.

**Traces to:** 4.9.7.6; 9.7
**Verified by:** Test: `tests/test_colour_contrast.py::test_draft_war_text`

#### Scenario: Negative WAR
- **WHEN** a pick has -1.57 WAR
- **THEN** its WAR shows in red

### Requirement: 4.9.7.7 Managers card
The tab SHALL show the Managers summary below the draft, with a This Draft | All Drafts switch, Managers listed by mean WAR above slot WAR, highest first.

**Traces to:** 4.9.7; 4.11.4
**Verified by:** Test: `tests/layout/test_draft_page.py::test_managers_card`

#### Scenario: All drafts
- **WHEN** a visitor picks "All Drafts" in the dynasty league
- **THEN** the card summarises every Manager's picks across the 2022 to 2026 rookie drafts

### Requirement: 4.9.7.8 Draft measures explained
The tab SHALL explain Steal/Reach, Hit/Bust and Unlucky, with their thresholds for the league shown, in a note below the draft.

**Traces to:** 4.9.7
**Verified by:** Test: `tests/layout/test_draft_page.py::test_measures_note`

#### Scenario: Redraft note
- **WHEN** a visitor views a redraft draft
- **THEN** the note gives a full round (12 picks) for Steal/Reach and 0.75 WAR for Hit/Bust

### Requirement: 4.9.7.4.3 Draft board on phones
On screens narrower than 600 px, the board SHALL scroll sideways inside its card with the round column pinned at its left edge.

**Traces to:** 4.9.7.4; 9.2.1
**Verified by:** Test: `tests/layout/test_draft_page.py::test_phone_board_pinned_round_column`

#### Scenario: 390 px phone
- **WHEN** a visitor on a 390 px screen scrolls the board sideways
- **THEN** the round labels stay in view and the page itself does not scroll sideways

### Requirement: 4.9.7.5.5 Draft table on phones
On screens narrower than 600 px, the Table view SHALL show each pick as a list row giving the pick, Player, the Manager who made it, any Steal or Reach badge and any Hit, Bust or Unlucky badge.

**Traces to:** 4.9.7.5; 9.2.1
**Verified by:** Test: `tests/layout/test_draft_page.py::test_phone_table_rows`

#### Scenario: 360 px phone
- **WHEN** a visitor on a 360 px screen opens the Table view
- **THEN** each pick is one list row and nothing is cut off

### Requirement: 4.9.7.9 Keeper Eligible matrix
Below the latest redraft draft, the tab SHALL show a Keeper Eligible matrix with one row per Manager and one column per price round, each cell listing that Manager's keeper-eligible Players at that price.

**Traces to:** 4.9.7; 4.11.6
**Verified by:** Test: `tests/layout/test_draft_page.py::test_keeper_matrix`

#### Scenario: 2026 redraft
- **WHEN** a visitor opens the 2026 redraft draft
- **THEN** the matrix titled "Keeper Eligible for 2027" lists Jaxon Smith-Njigba under round 1 in his Manager's row

### Requirement: 4.9.7.9.1 Keeper matrix on phones
On screens narrower than 600 px, the Keeper Eligible matrix SHALL show one list per Manager of that Manager's keeper-eligible Players with their prices.

**Traces to:** 4.9.7.9; 9.2.1
**Verified by:** Test: `tests/layout/test_draft_page.py::test_keeper_matrix_on_phones`

#### Scenario: 390 px phone
- **WHEN** a visitor on a 390 px screen opens the 2026 redraft draft
- **THEN** each Manager's keeper-eligible Players are listed with their price rounds and the page does not scroll sideways
