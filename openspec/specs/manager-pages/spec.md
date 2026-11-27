# manager-pages Specification

## Purpose

The Managers sub-tab of each league page: one page per Manager, inspired by Football Manager's club page, with a team info bar, a season info bar and four cards (Roster, Team History, Moves and Team News), laid out for desktop and phones. It delivers need 4, Manager History, on the page; the data and calculations are in `manager-history`, `team-news` and `Calculations.txt`, sections 19 to 21.

## Requirements

### Requirement: 4.4 Managers sub-tab
The Managers sub-tab SHALL show one page per Manager of the league, with a team info bar, a season info bar and four cards: Roster, Team History, Moves and Team News.

**Traces to:** 4; 9.1.1
**Verified by:** Test: `tests/test_export.py::test_export_writes_the_managers_file_with_every_manager`

#### Scenario: Open the sub-tab
- **WHEN** a visitor picks "Managers"
- **THEN** a Manager's page is shown with both bars and the four cards

### Requirement: 4.4.1 Manager picker
The page SHALL show one Manager at a time, chosen from a list flanked by previous and next arrows, with current Managers first and then a "Retired" group, each in name order.

**Traces to:** 4.4
**Verified by:** Test: `tests/layout/test_managers_behaviour.py::test_picker_lists_current_managers_then_retired`

#### Scenario: Step to the next Manager
- **WHEN** a visitor on tg1212's page presses the next arrow
- **THEN** the next Manager in the list is shown

### Requirement: 4.4.1.1 Manager in the URL
The page URL SHALL name the chosen Manager, so that opening a link shows that Manager's page.

**Traces to:** 4.4.1; 9.1.1.1
**Verified by:** Test: `tests/layout/test_managers_page.py::test_link_names_the_manager_and_arrows_update_the_url`

#### Scenario: Link to a Manager
- **WHEN** a visitor opens a link naming the redraft league, the Managers sub-tab and kjern17
- **THEN** kjern17's redraft page is shown

### Requirement: 4.4.1.2 Manager kept across leagues
Switching league SHALL keep the chosen Manager when they are in the other league, and otherwise show that league's first Manager.

**Traces to:** 4.4.1; 9.1.1.2
**Verified by:** Test: `tests/layout/test_managers_behaviour.py::test_switching_league_keeps_a_shared_manager_or_shows_the_first`

#### Scenario: Manager in both leagues
- **WHEN** a visitor on DeekBurg's dynasty page switches to the redraft league
- **THEN** DeekBurg's redraft page is shown

### Requirement: 4.4.2 Manager names link to their page
Every Manager name in the site's tables and lists (Forecasts, Games, Positions, Player WAR and Managers) SHALL link to that Manager's page in the same league.

**Traces to:** 4.4; 9
**Verified by:** Test: `tests/layout/test_managers_page.py::test_manager_names_open_their_page`

#### Scenario: Name in the Forecast table
- **WHEN** a visitor selects "djernberg" in the Forecast table
- **THEN** djernberg's Managers page opens

### Requirement: 4.4.3 Team info bar
The page SHALL open with a team info bar showing the crest, the current Team Name, the banners, and Form, Founded, All-Time, Rating and Rival separated by light dividers.

**Traces to:** 4.4
**Verified by:** Inspection: the live site, the team info bar of a current dynasty Manager

#### Scenario: Current Manager
- **WHEN** a current Manager's page is shown
- **THEN** the bar shows the crest, Team Name, banners, Form, Founded, All-Time, Rating and Rival

### Requirement: 4.4.3.1 Crest
The crest SHALL be the team logo, else the Sleeper avatar, else the initials in the team colour with a light fill, darker letters and outline, and at least 4.5:1 contrast for the letters.

**Traces to:** 4.4.3; 9
**Verified by:** Inspection: the live site, a Manager with a logo, one with an avatar only and one with neither

#### Scenario: No logo or avatar
- **WHEN** a Manager has neither a logo nor an avatar
- **THEN** the crest shows their initials in their team colour

### Requirement: 4.4.3.2 Banners
The bar SHALL hang champion banners and then, after a wider gap, toilet bowl banners, stacking them only when one row does not fit.

**Traces to:** 4.4.3
**Verified by:** Test: `tests/layout/test_managers_page.py::test_banners_stack_only_when_out_of_room`

#### Scenario: Champion and toilet bowl
- **WHEN** a Manager won the 2023 title and the 2022 toilet bowl
- **THEN** a gold 2023 banner hangs on the left rod and a brown 2022 banner on a second rod after a gap

#### Scenario: No banners
- **WHEN** a Manager has neither
- **THEN** the banner space stays empty

### Requirement: 4.4.3.3 Retired Manager's bar
A retired Manager's bar SHALL hide Form and read "Seasons <first>–<last>" in place of Founded.

**Traces to:** 4.4.3
**Verified by:** Inspection: the live site, TateFM's dynasty page

#### Scenario: Retired Manager
- **WHEN** TateFM's dynasty page is shown
- **THEN** Form is hidden and the bar reads "Seasons 2022–2023"

### Requirement: 4.4.3.4 Form bars
Form SHALL show the current season's five most recent results as bars from a centre line, oldest on the left: a win rising in green, a loss dropping in red, and a draw or a week without a game a short grey dash on the line.

**Traces to:** 4.4.3
**Verified by:** Test: `tests/test_managers.py::test_form_is_the_last_five_of_the_season_oldest_first`; Inspection: the live site, Form bars of a Manager with wins and losses

#### Scenario: Mixed form
- **WHEN** a Manager's last five results are W, L, W, W, L
- **THEN** the bars read rise, drop, rise, rise, drop from left to right

### Requirement: 4.4.3.4.1 Form before week one
Before week 1, Form SHALL show five grey dashes.

**Traces to:** 4.4.3.4
**Verified by:** Inspection: the live site after a draft and before week 1

#### Scenario: Pre-season
- **WHEN** no game of the season has been played
- **THEN** Form shows five grey dashes

### Requirement: 4.4.3.4.2 Form for screen readers
The Form bars SHALL carry their sequence of results as text for screen readers.

**Traces to:** 4.4.3.4; 9
**Verified by:** Inspection: the Form bars' accessible name in the browser's accessibility tree

#### Scenario: Screen reader
- **WHEN** a screen reader reaches the Form bars
- **THEN** it reads the five results in order

### Requirement: 4.4.4 Season info bar
Below the team info bar, the page SHALL show seven tiles: Current League Position with the record and points for, Last Result with both crests and the score, Next Matchup with the win Forecast, Manager with the win rate, Top Scorer, Best Player All-Time with WAR and seasons on the team, and Playoff Forecast with its weekly change.

**Traces to:** 4.4
**Verified by:** Test: `tests/layout/test_managers_page.py::test_tiles_fit_the_worst_case`

#### Scenario: Current Manager's tiles
- **WHEN** a current Manager's page is shown in week 11
- **THEN** all seven tiles show this season's figures

### Requirement: 4.4.4.1 Rivalry Week badge
In rivalry week, the Next Matchup tile SHALL carry a Rivalry Week badge when the next game is against the Manager's rival.

**Traces to:** 4.4.4
**Verified by:** Inspection: the live site in rivalry week

#### Scenario: Rivalry week
- **WHEN** the next game is against the Manager's rival in rivalry week
- **THEN** the Next Matchup tile carries a Rivalry Week badge

### Requirement: 4.4.4.2 Projected top scorer
Before week 1, the Top Scorer tile SHALL show the roster's highest projected scorer, labelled "Top Scorer (Projected)".

**Traces to:** 4.4.4
**Verified by:** Inspection: the live site after a draft and before week 1

#### Scenario: Before week 1
- **WHEN** no game has been played
- **THEN** Top Scorer shows the highest projected scorer labelled "Top Scorer (Projected)"

### Requirement: 4.4.4.3 Retired Manager's tiles
A retired Manager's tiles SHALL show their last season, labelled with its year, with Next Matchup and Playoff Forecast reading "Retired".

**Traces to:** 4.4.4
**Verified by:** Inspection: the live site, TateFM's dynasty tiles

#### Scenario: Retired Manager tiles
- **WHEN** a retired Manager's page is shown
- **THEN** the tiles show their last season and Next Matchup and Playoff Forecast read "Retired"

### Requirement: 4.4.4.4 Tile layout
Every tile SHALL share one layout: a fixed first line holding a 32 px image or a large number, then a detail line, so that images and numbers line up across the bar.

**Traces to:** 4.4.4
**Verified by:** Inspection: the live site at 1280 px, the first lines of the seven tiles

#### Scenario: Lined up
- **WHEN** the bar is shown at 1280 px
- **THEN** every tile's image or number sits on one line across the bar

### Requirement: 4.4.4.5 Tile text fits
Tile text SHALL scale with the tile's width, label icons hiding first on the narrowest tiles, with no text cut at every tested width or with wide system fonts.

**Traces to:** 4.4.4; 9.2
**Verified by:** Test: `tests/layout/test_managers_page.py::test_tiles_fit_the_worst_case`

#### Scenario: Wide system font
- **WHEN** the page is drawn at 360 px and 1280 px with a wide font like the Linux defaults
- **THEN** no tile's text is cut

### Requirement: 4.4.4.6 Last Result tile
The Last Result score SHALL stay on one line with both crests inside the tile, the score shrinking first.

**Traces to:** 4.4.4; 4.4.4.5
**Verified by:** Test: `tests/layout/test_managers_page.py::test_tiles_fit_the_worst_case`

#### Scenario: Narrow tile
- **WHEN** the Last Result tile is at its narrowest
- **THEN** the score text shrinks and both crests stay inside the tile

### Requirement: 4.4.4.7 Tiles link to their source
Each tile SHALL link to the page its number comes from.

**Traces to:** 4.4.4
**Verified by:** Inspection: the live site, each tile's link target

#### Scenario: Playoff Forecast tile
- **WHEN** a visitor selects the Playoff Forecast tile
- **THEN** the Forecasts sub-tab opens

### Requirement: 4.4.4.8 Tiles on a phone
Below 600 px wide, the tiles SHALL form two columns, with the seventh spanning both.

**Traces to:** 4.4.4; 9.2
**Verified by:** Inspection: the live site at 360 px, the tile grid

#### Scenario: Phone tiles
- **WHEN** the page is shown at 360 px
- **THEN** the tiles sit in two columns and Playoff Forecast spans both

### Requirement: 4.4.5 Player names on tiles and cards
Player names on the tiles and cards SHALL show in full when they fit and otherwise as first initial and last name, with the full name as a tooltip, never cut at any tested width.

**Rationale:** The project's Player name standard.
**Traces to:** 4.4; 9.2
**Verified by:** Test: `tests/layout/test_managers_page.py::test_cards_cut_nothing_and_never_scroll_sideways`; Test: `tests/layout/test_managers_page.py::test_tiles_fit_the_worst_case`

#### Scenario: Longest name on a phone
- **WHEN** Jaxon Smith-Njigba is the top scorer on a 360 px phone
- **THEN** the tile shows "J. Smith-Njigba" in full

#### Scenario: Room for the full name
- **WHEN** a roster card at 1280 px has room for "Amon-Ra St. Brown"
- **THEN** the full name shows

### Requirement: 4.4.6 Roster card
The Roster card SHALL list the current roster, or a retired Manager's final roster, in lineup order and then bench, IR and taxi, with slot, status, Player, position and PPG columns.

**Traces to:** 4.4
**Verified by:** Inspection: the live site, a dynasty Manager's Roster card

#### Scenario: Roster order
- **WHEN** a Manager's Roster card is shown
- **THEN** starters come first in lineup order, then bench, IR and taxi

### Requirement: 4.4.6.1 PPG chip colours
The PPG chip SHALL be coloured against the position's replacement level R: dark green from 1.5R, light green from 1.2R, grey from 0.9R, light red from 0.7R and red below 0.7R.

**Rationale:** Calculations.txt section 14 defines the replacement level.
**Traces to:** 4.4.6; 3
**Verified by:** Test: `tests/layout/test_managers_behaviour.py::test_ppg_chips_follow_the_replacement_tiers`

#### Scenario: Weak bench player
- **WHEN** a receiver averages 4.9 against a WR replacement level of 8.8
- **THEN** his chip is red

### Requirement: 4.4.6.2 Slot pills
Each slot SHALL show as a pill in the position colour, with FLEX split into RB, WR and TE thirds, BN outlined, IR red and Taxi gold.

**Traces to:** 4.4.6
**Verified by:** Inspection: the live site, each kind of slot pill in both themes

#### Scenario: FLEX pill
- **WHEN** a Player sits in the FLEX slot
- **THEN** his pill shows the RB, WR and TE colours in thirds

### Requirement: 4.4.6.3 Status badges
Each status SHALL show as a badge, red for the site's out statuses and grey for Questionable.

**Traces to:** 4.4.6
**Verified by:** Inspection: the live site, an Out, a Doubtful and a Questionable Player

#### Scenario: Doubtful player
- **WHEN** a bench Player is Doubtful
- **THEN** his status badge is red, like Out

### Requirement: 4.4.6.4 Roster points footer
The Roster card's footer SHALL show this week's starter and bench points.

**Traces to:** 4.4.6
**Verified by:** Test: `tests/test_managers.py::test_bench_points_example`

#### Scenario: Week in progress
- **WHEN** a Manager's starters have 88.4 points and the bench 31.2
- **THEN** the footer shows both totals

### Requirement: 4.4.6.5 Keeper eligible badge
On the redraft Roster card, a keeper-eligible Player SHALL show a gold "KE" badge after his name.

**Traces to:** 4.4.6; 4.11.6
**Verified by:** Test: `tests/layout/test_managers_page.py::test_keeper_eligible_badge`

#### Scenario: Kept receiver
- **WHEN** a visitor opens the redraft Manager whose roster holds Jaxon Smith-Njigba, keeper eligible for 2027
- **THEN** his row shows a gold "KE" badge after his name

### Requirement: 4.4.7 Team History card
The Team History card SHALL have three tabs: History, Head to Head and Records.

**Traces to:** 4.4
**Verified by:** Test: `tests/layout/test_managers_page.py::test_cards_cut_nothing_and_never_scroll_sideways`

#### Scenario: Switch tabs
- **WHEN** a visitor picks Head to Head
- **THEN** the head-to-head table replaces the History tab

### Requirement: 4.4.7.1 History tab
The History tab SHALL show an About sentence, the League History chart, Honours as years without counts, and Luck with its numbers right-aligned.

**Traces to:** 4.4.7
**Verified by:** Test: `tests/test_managers.py::test_all_play_and_luck`; Inspection: the live site, a champion's History tab

#### Scenario: Honours
- **WHEN** a Manager won the 2023 title
- **THEN** Honours lists 2023 without a count

### Requirement: 4.4.7.2 Head to Head tab
The Head to Head tab SHALL list one row per opponent, the rival first and the rest by games played, each with the record, points and a last result that stays on one line.

**Traces to:** 4.4.7
**Verified by:** Test: `tests/layout/test_managers_behaviour.py::test_head_to_head_lists_the_rival_first_then_by_games`; Test: `tests/test_managers.py::test_head_to_head_counts_regular_and_playoff_games`

#### Scenario: Head to head order
- **WHEN** the Head to Head tab is opened
- **THEN** the rival is the first row, followed by the other opponents by games played

### Requirement: 4.4.7.3 Records tab
The Records tab SHALL show the Manager's records with their values centred on their rows, then the history of their Team Names.

**Traces to:** 4.4.7
**Verified by:** Test: `tests/test_managers.py::test_records_rank_against_every_game_in_league_history`; Inspection: the live site, a Records tab

#### Scenario: Records
- **WHEN** the Records tab is opened
- **THEN** each record's value is centred and the Team Names follow

### Requirement: 4.4.7.3.1 All-time rank tag
A record that is the league's best ever SHALL carry a gold "#1 All Time" tag.

**Traces to:** 4.4.7.3
**Verified by:** Test: `tests/test_managers.py::test_records_rank_against_every_game_in_league_history`

#### Scenario: Records with ranks
- **WHEN** a Manager's highest score is the league's highest ever
- **THEN** the record carries a gold "#1 All Time" tag

### Requirement: 4.4.7.4 League History chart
The League History chart SHALL plot each season's final finish, 1st at the top, with the playoff places shaded, a gold trophy for a title, 💩 for a toilet bowl, a green dot for a playoff season and a grey dot for a miss, and a legend on one line.

**Traces to:** 4.4.7; 4.4.7.1
**Verified by:** Test: `tests/test_managers.py::test_dynasty_champions_and_runners_up_match_league_history`; Inspection: the live site, a champion's chart

#### Scenario: Title season
- **WHEN** a Manager won the 2023 title
- **THEN** a gold trophy marks 2023 at 1st

### Requirement: 4.4.7.4.1 Current season on the chart
The current season SHALL show as a hollow dot at the forecast finish, joined to the last final season by a dashed line.

**Traces to:** 4.4.7.4; 1
**Verified by:** Inspection: the live site, a current Manager's chart in week 11

#### Scenario: Current season
- **WHEN** the season is under way with a forecast finish of 3rd
- **THEN** a hollow dot sits at 3rd in the current season's column

### Requirement: 4.4.8 Team News card
The Team News card SHALL show the most important story of the latest week as a feature story, with a picture drawn from the data, and below it "More Stories" listing the rest newest first, each with a thumbnail, headline, time, category and link to its source page.

**Rationale:** Calculations.txt section 20 ranks the stories.
**Traces to:** 4.4
**Verified by:** Test: `tests/test_news.py::test_record_beats_result_for_the_feature_and_player_stories_are_capped`

#### Scenario: Story list
- **WHEN** a Manager has twelve stories this season
- **THEN** the feature shows the most important and the other eleven follow, newest first

### Requirement: 4.4.8.1 Feature result picture
A feature story about a result SHALL show both crests and the score, inside the card at every width.

**Traces to:** 4.4.8
**Verified by:** Test: `tests/layout/test_managers_page.py::test_cards_cut_nothing_and_never_scroll_sideways`

#### Scenario: Feature result
- **WHEN** the latest week's main story is a win
- **THEN** the feature shows both crests and the score inside the card at every width

### Requirement: 4.4.8.2 Show more on a phone
Below 600 px wide, the card SHALL show the first seven stories under the feature, with a "Show more" button for the rest.

**Traces to:** 4.4.8; 9.2
**Verified by:** Test: `tests/layout/test_managers_behaviour.py::test_phone_news_shows_seven_stories_then_show_more`

#### Scenario: Long news list
- **WHEN** a phone visitor opens a card with twelve stories
- **THEN** seven show under the feature, and "Show more" reveals the other four

### Requirement: 4.4.9 Moves card
The Moves card SHALL show, for the chosen season or all seasons, a FAAB meter, then the Added, Dropped and Trades lists, then a Players block.

**Rationale:** Calculations.txt section 21.
**Traces to:** 4.4
**Verified by:** Test: `tests/layout/test_managers_page.py::test_moves_card_cuts_nothing`; Inspection: the live site, a 2026 Moves card

#### Scenario: Season shown
- **WHEN** a Manager's 2026 moves are shown
- **THEN** the FAAB meter, the three lists and the Players block show that season's figures

### Requirement: 4.4.9.1 Moves season picker
A season picker with arrows SHALL offer each season with moves, newest first, and "All seasons".

**Traces to:** 4.4.9
**Verified by:** Test: `tests/layout/test_managers_behaviour.py::test_moves_filter_season_picker_and_headers`

#### Scenario: All seasons
- **WHEN** a visitor picks "All seasons"
- **THEN** every season's moves show together

### Requirement: 4.4.9.2 Moves filter
A filter SHALL offer All moves, Waivers, Free agents and Trades, showing only the chosen kind.

**Traces to:** 4.4.9
**Verified by:** Test: `tests/layout/test_managers_behaviour.py::test_moves_filter_season_picker_and_headers`

#### Scenario: Filter
- **WHEN** the visitor chooses Trades
- **THEN** only the Trades list shows

### Requirement: 4.4.9.3 FAAB meter
The FAAB meter SHALL show the FAAB spent of the budget, the biggest bid and the overpaid total.

**Traces to:** 4.4.9
**Verified by:** Test: `tests/test_moves.py::test_faab_biggest_bid_and_overpaid_total`

#### Scenario: Season meter
- **WHEN** a Manager spent $75 of $100, with a biggest bid of $41 and $29 overpaid
- **THEN** the meter shows all three

### Requirement: 4.4.9.4 Players block
The Players block SHALL name the Player with the most seasons on the team and the one that got away.

**Traces to:** 4.4.9
**Verified by:** Test: `tests/test_managers.py::test_redraft_got_away_counts_only_the_latest_season`

#### Scenario: Got away
- **WHEN** a dropped Player went on to the most WAR elsewhere
- **THEN** he is named as the one that got away, with his WAR elsewhere

### Requirement: 4.4.10 Move rows
Each added or dropped row SHALL show the Player's name, how the move happened and its week on a second line, and a WAR chip in the Roster card's colours.

**Traces to:** 4.4; 4.4.9
**Verified by:** Test: `tests/test_moves.py::test_add_and_drop_in_one_move_and_claimed_by`

#### Scenario: Added Player
- **WHEN** a Manager added a running back off waivers in week 3
- **THEN** his row shows his name, "Waiver · week 3" and his WAR chip

### Requirement: 4.4.10.1 Moves list headers
Each Moves list header SHALL give its count, with Added also giving its FAAB spent and total WAR, and Dropped its WAR elsewhere.

**Traces to:** 4.4.10
**Verified by:** Test: `tests/layout/test_managers_behaviour.py::test_moves_filter_season_picker_and_headers`

#### Scenario: Added header
- **WHEN** a Manager added five Players for $75 worth +1.5 WAR in total
- **THEN** the header reads "Added (5)" with "$75 · +1.5 WAR"

### Requirement: 4.4.10.2 Overpay tag
A won waiver row SHALL show its bid and its overpay as a red tag such as "+$29", explained on hover as against the next bid or no other bids, with a tie reading "tied".

**Traces to:** 4.4.10
**Verified by:** Test: `tests/test_moves.py::test_overpay_contested_uncontested_tie_and_other_runs`

#### Scenario: Overpay tag
- **WHEN** Rico Dowdle was won for $41 against a next bid of $12
- **THEN** his row reads "Waiver · $41 +$29 · week 3" with the tag in red

### Requirement: 4.4.10.3 No games
A Player with no game after the move SHALL show "no games" in place of a WAR chip, or "no games yet" while nothing after the move is scored.

**Traces to:** 4.4.10
**Verified by:** Test: `tests/test_moves.py::test_no_games_and_pending`

#### Scenario: Never played
- **WHEN** a dropped Player had no game while away from the team
- **THEN** his chip reads "no games"

### Requirement: 4.4.10.4 Trade blocks
Each trade SHALL be one block naming the other Manager, linked to their page, and the week, with Got and Gave sides showing Players with their WAR chips, picks as season and round ("2027 2nd") and FAAB as "$5 FAAB".

**Traces to:** 4.4.10
**Verified by:** Test: `tests/test_moves.py::test_trade_with_pick_and_faab_never_repeats_as_rows`

#### Scenario: Trade with a pick
- **WHEN** a trade sent T. Etienne Jr. for J. Smith-Njigba and a 2027 2nd
- **THEN** the block shows Got: J. Smith-Njigba with his chip and "2027 2nd"; Gave: T. Etienne Jr. with his chip

### Requirement: 4.4.10.5 Moves text never cut
On the Moves card, a row's second line and any name too wide even when shortened SHALL wrap onto another line, never cut, at every tested width and with wide system fonts.

**Traces to:** 4.4.10; 9.2
**Verified by:** Test: `tests/layout/test_managers_page.py::test_moves_card_cuts_nothing`

#### Scenario: Long name in a trade
- **WHEN** "C. Edwards-Helaire" is still wider than its trade column
- **THEN** the name wraps instead of ending in an ellipsis

### Requirement: 4.4.11 Cards on desktop
From 600 px wide, the four cards SHALL sit side by side with the Roster card widest, all the same height, each scrolling vertically inside itself and never sideways.

**Traces to:** 4.4
**Verified by:** Test: `tests/layout/test_managers_page.py::test_desktop_cards_share_one_height`; Test: `tests/layout/test_managers_page.py::test_cards_cut_nothing_and_never_scroll_sideways`

#### Scenario: Desktop cards
- **WHEN** the page is shown at 1280 px
- **THEN** the four cards share one height and scroll only up and down

### Requirement: 4.4.11.1 Cards on a phone
Below 600 px wide, a tab row (Roster, History, Moves, News) SHALL show one card at a time, each card sharing one minimum height, growing with longer content and never scrolling inside itself.

**Traces to:** 4.4.11; 9.2
**Verified by:** Test: `tests/layout/test_managers_page.py::test_phone_cards_never_scroll_inside_and_share_a_height`

#### Scenario: Phone card switch
- **WHEN** a phone visitor taps "History"
- **THEN** only the Team History card is shown, with no scrollbar of its own

### Requirement: 4.4.12 Managers sub-tab accessible
The Managers sub-tab SHALL meet WCAG 2.2 AA, with 48 by 48 px touch targets on phones, at every tested width and in both themes.

**Traces to:** 4.4; 9
**Verified by:** Test: `tests/layout/test_accessibility.py::test_accessibility_wcag_22_aa`; Test: `tests/layout/test_accessibility.py::test_touch_targets_on_phones`

#### Scenario: Picker arrows on a phone
- **WHEN** the page is shown at 360 px
- **THEN** the picker arrows are at least 48 by 48 px and the page passes the accessibility check
