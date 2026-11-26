# league-odds-site Specification

## Purpose

The public website's league pages and their Forecasts sub-tab: each team's current season Forecast, how it changed week by week, and the Managers' ratings. It delivers needs 1 (Season Forecasts) and 4 (Manager History) on the page, and its layout serves need 9 (Usable by Every Manager). The cold run, deploys and the calibration page are specified in `refresh-scheduling`, `site-updates` and `odds-calibration`.

## Requirements

### Requirement: 9.1 League pages
The site SHALL give each configured league its own page, with a control to switch between the leagues.

**Traces to:** 9
**Verified by:** Inspection: the live site, each league in `config/leagues.yaml` has a page and the league control switches between them

#### Scenario: Switch league
- **WHEN** a visitor on the dynasty page picks the redraft league
- **THEN** the redraft league's page is shown on the same sub-tab

### Requirement: 9.1.1 Sub-tabs
Each league page SHALL have six sub-tabs, in this order: Forecasts, Games, Positions, Managers, Player WAR and League.

**Traces to:** 9.1
**Verified by:** Inspection: the live site, the sub-tab strip of each league page

#### Scenario: Open the Games sub-tab
- **WHEN** a visitor picks "Games", between "Forecasts" and "Positions"
- **THEN** the league's Games page is shown

#### Scenario: Open the League sub-tab
- **WHEN** a visitor picks "League", after "Player WAR"
- **THEN** the league's League page is shown

### Requirement: 9.1.1.1 Sub-tab in the URL
The page URL SHALL name the league and the selected sub-tab, so that opening a link shows that league and sub-tab.

**Rationale:** Managers share links to a page in the league chat.
**Traces to:** 9.1.1
**Verified by:** Test: `tests/layout/test_forecasts_page.py::test_url_opens_the_named_league_and_subtab`

#### Scenario: Link to a sub-tab
- **WHEN** a visitor opens a link whose URL names the dynasty league and the Player WAR sub-tab
- **THEN** the page opens on the dynasty Player WAR page

### Requirement: 9.1.1.2 Sub-tab kept across leagues
Switching league SHALL keep the selected sub-tab.

**Traces to:** 9.1.1
**Verified by:** Test: `tests/layout/test_forecasts_page.py::test_switching_league_keeps_the_subtab`

#### Scenario: Positions in both leagues
- **WHEN** a visitor on the dynasty Positions sub-tab switches to the redraft league
- **THEN** the redraft Positions sub-tab is shown

### Requirement: 9.2 Fits a phone
Every league page SHALL fit each tested phone width, down to 360 px, without the page scrolling sideways.

**Rationale:** The tested widths are in the project standards (StatCounter, October 2026).
**Traces to:** 9
**Verified by:** Test: `tests/layout/test_layout.py::test_control_keeps_the_layout`; Test: `tests/layout/test_layout.py::test_wide_fonts_do_not_scroll_sideways`

#### Scenario: Phone visit
- **WHEN** a visitor opens a league page on a 360 px wide screen
- **THEN** the page does not scroll sideways and the charts fit the screen width

### Requirement: 9.2.1 Pinned Manager column
On screens narrower than 600 px, the Forecast table SHALL scroll sideways inside its own container with the Manager column pinned at its left edge.

**Traces to:** 9.2; 1.3
**Verified by:** Test: `tests/layout/test_layout.py::test_forecast_table_pins_the_manager_column_on_phones`; Test: `tests/layout/test_layout.py::test_pinned_columns_cover_nothing_before_scrolling`

#### Scenario: Scroll the Forecast table on a phone
- **WHEN** a visitor on a 440 px wide phone scrolls the Forecast table to the right
- **THEN** the ELO and 1-week change columns scroll away while the Manager column stays at the left edge

### Requirement: 9.2.1.1 Manager names on one line
Manager names in the pinned column SHALL stay on one line.

**Traces to:** 9.2.1
**Verified by:** Inspection: the live site at 360 px, no Manager name in the Forecast table wraps

#### Scenario: Long display name
- **WHEN** a Manager's display name is the longest in the league
- **THEN** it shows on one line in the pinned column

### Requirement: 9.2.2 Sub-tab strip on a phone
When the sub-tabs are wider than the screen, the sub-tab strip SHALL scroll sideways on its own: snapping to tab edges, fading the edge with more tabs beyond it, showing no scroll bar, and opening with the selected sub-tab in view.

**Traces to:** 9.2; 9.1.1
**Verified by:** Test: `tests/layout/test_layout.py::test_subtab_strip_swipes_on_a_phone`; Test: `tests/layout/test_layout.py::test_subtab_strip_does_not_scroll_on_desktop`

#### Scenario: Swipe the sub-tabs
- **WHEN** a visitor on a 360 px wide screen swipes the sub-tab strip left
- **THEN** the strip reveals "Player WAR", settles on a tab edge, and the page below stays where it was

#### Scenario: Wide screen
- **WHEN** the sub-tabs fit the screen width
- **THEN** the strip does not scroll and shows no fade

### Requirement: 9.2.3 Metric buttons on a phone
When a chart's metric buttons do not fit on one line, they SHALL form one row that scrolls sideways, without wrapping and without moving the page.

**Traces to:** 9.2; 1.4.2
**Verified by:** Test: `tests/layout/test_layout.py::test_metric_buttons_form_one_swipe_strip_on_phones`

#### Scenario: Buttons on a phone
- **WHEN** the redraft page is shown at 360 px
- **THEN** the four metric buttons sit on one line that can be swiped sideways

### Requirement: 9.2.4 Charts on a phone
On screens narrower than 600 px, each chart SHALL span its card's full width, giving up room at the right edge only for a highlighted team's end label.

**Traces to:** 9.2
**Verified by:** Test: `tests/layout/test_layout.py::test_charts_reach_the_card_edge_on_phones`

#### Scenario: Highlighted team on a phone
- **WHEN** a visitor on a phone highlights a team
- **THEN** that team's end label shows at the chart's right edge, which gives up only that label's width

### Requirement: 9.3 Public pages
Anyone with the link SHALL be able to view every page without signing in.

**Traces to:** 9
**Verified by:** Inspection: the live site opened in a private browser window shows every page

#### Scenario: Shared link
- **WHEN** a Manager sends the site link to someone without any account
- **THEN** that person sees every page

### Requirement: 11.1 Static site
The site SHALL be static files, with no server code, no sign-in and no calls to Sleeper from the visitor's browser.

**Rationale:** Static files host free on GitHub Pages and keep Sleeper's servers out of each visit.
**Traces to:** 11; 12
**Verified by:** Inspection: `site/` holds only HTML, CSS, JavaScript and data files, and its scripts fetch only `site/data/` and the relay

#### Scenario: Visitor loads a page
- **WHEN** a visitor opens a league page
- **THEN** all its data comes from files published with the site

### Requirement: 11.1.1 Works without the relay
Every page SHALL show its published data when the refresh relay is not configured or does not answer.

**Traces to:** 11.1
**Verified by:** Test: `tests/layout/test_layout.py::test_older_bundle_and_relay_down_are_ignored`

#### Scenario: Relay down
- **WHEN** the refresh relay does not answer
- **THEN** the pages show their data as usual and the Refresh Data button says a refresh could not be started

### Requirement: 1.3 Forecast table
The Forecasts sub-tab SHALL show a table with one row per team and these columns, in order: ELO, 1-week ELO change, Manager, projected final record, the league's bottom column, Make Playoffs, Bye and Win Championship.

**Traces to:** 1
**Verified by:** Test: `tests/test_export.py::test_exported_schema`; Inspection: the live site, column order of each league's table

#### Scenario: Table contents
- **WHEN** a visitor opens the dynasty page with the as-of-week-10 Forecast stored
- **THEN** the table shows all 12 teams with the as-of-week-10 values

### Requirement: 1.3.1 Standings order
Until a visitor sorts it, the table SHALL list teams in standings order: wins, a tie counting as half a win, then points scored.

**Traces to:** 1.3; 1.1.7
**Verified by:** Test: `tests/layout/test_forecasts_page.py::test_unsorted_table_follows_the_standings`

#### Scenario: Unsorted table
- **WHEN** two teams are both 7-2 and one has scored more points
- **THEN** that team's row is above the other's

### Requirement: 1.3.2 Manager cell
Each Manager cell SHALL show the Manager's display name in bold, the team's current record beside it and the Team Name beneath.

**Traces to:** 1.3
**Verified by:** Inspection: the live site, Manager cells of each league's table

#### Scenario: Manager cell
- **WHEN** a team is managed by `tg1212`, named "Diaper Dandies" and is 7-2 with no ties
- **THEN** its cell shows "tg1212" in bold with "7-2" beside it and "Diaper Dandies" beneath

### Requirement: 1.3.3 Column alignment
Columns left of Manager SHALL be left-aligned, the Manager column centred and the columns right of it right-aligned, headers and cells alike.

**Traces to:** 1.3
**Verified by:** Inspection: the live site at 360 and 1280 px, header and cell alignment

#### Scenario: Alignment
- **WHEN** the table is shown at any tested width
- **THEN** ELO and 1-week change are left-aligned, Manager centred, and the record and probability columns right-aligned

### Requirement: 1.3.4 Narrow rating columns
The ELO and 1-week ELO change columns SHALL be no wider than their header or widest value needs.

**Traces to:** 1.3
**Verified by:** Inspection: the live site at 1280 px, no padding beyond the widest ELO value or header

#### Scenario: Desktop table
- **WHEN** the table is shown at 1280 px
- **THEN** the ELO columns take only the width of their content

### Requirement: 1.3.5 Projected record format
The projected record SHALL show the mean simulated wins and losses to one decimal place, as "10.6 - 3.4".

**Traces to:** 1.3; 1.1.9
**Verified by:** Test: `tests/layout/test_forecasts_page.py::test_projected_record_and_probabilities_are_formatted`

#### Scenario: Projected record format
- **WHEN** a team's projected record is 10.59 wins and 3.41 losses
- **THEN** the cell shows "10.6 - 3.4"

### Requirement: 1.3.6 Weekly change on hover
Hovering over a probability cell SHALL show its change since the previous as-of week, when one is stored.

**Traces to:** 1.3; 1.2
**Verified by:** Test: `tests/test_export.py::test_single_week_has_null_changes`

#### Scenario: Weekly change
- **WHEN** Forecasts exist for the current as-of week and the one before it
- **THEN** hovering over a team's probability cell shows that probability's change since the previous week

#### Scenario: First week of Forecasts
- **WHEN** only the current as-of week is stored
- **THEN** probability cells show no change

### Requirement: 1.3.7 Bottom column
The bottom column SHALL show "#1 Pick", the probability of finishing last, for a dynasty league with a consolation bracket, and "Avoid Loser's Bye", the probability of finishing outside the bottom two, for every other league.

**Traces to:** 1.3; 1.1.9
**Verified by:** Test: `tests/test_export.py::test_bottom_column_follows_league_settings`; Test: `tests/test_export.py::test_avoid_losers_bye_is_one_minus_bottom_two`

#### Scenario: Toilet-bowl league
- **WHEN** a redraft (toilet bowl) team finishes 11th in 3% of runs and 12th in 1%
- **THEN** the column is titled "Avoid Loser's Bye" and shows 96% for that team

#### Scenario: Dynasty consolation league
- **WHEN** a dynasty team finishes last in 40% of runs
- **THEN** the column is titled "#1 Pick" and shows 40% for that team

### Requirement: 1.3.7.1 Bottom column named in the data
The exported data SHALL name each league's bottom column, so that the site applies no league-specific rules.

**Traces to:** 1.3.7
**Verified by:** Test: `tests/test_export.py::test_bottom_column_follows_league_settings`

#### Scenario: Page reads the column name
- **WHEN** the page builds the table
- **THEN** it takes the bottom column's title from the league's data file

### Requirement: 1.3.8 Probability format
Probability cells SHALL print "100%" from 99.95%, ">99%" from 99.5%, "<1%" above 0 and below 0.5%, and otherwise the whole-number percentage.

**Traces to:** 1.3
**Verified by:** Test: `tests/layout/test_forecasts_page.py::test_projected_record_and_probabilities_are_formatted`

#### Scenario: Low, mid and high probabilities
- **WHEN** three teams have 0.3%, 50% and 99.6% playoff probabilities
- **THEN** their cells read "<1%", "50%" and ">99%"

### Requirement: 1.3.8.1 Probability fill
Each probability cell SHALL be filled from a single-hue blue ramp that darkens as the probability rises, with no fill below 1% and the darkest step above 99%.

**Traces to:** 1.3.8
**Verified by:** Inspection: the live site in both themes, fills at 0.3%, 50% and 99.6%

#### Scenario: Mid probability
- **WHEN** a team's playoff probability is 50%
- **THEN** its cell has a mid blue fill

### Requirement: 1.3.8.1.1 Readable fills
Text on every step of the probability ramp SHALL have at least 4.5:1 contrast with its fill in both themes, using light text on the dark steps.

**Rationale:** Each theme has its own ramp, designed for its background.
**Traces to:** 1.3.8.1; 9
**Verified by:** Test: `tests/test_colour_contrast.py::test_colour_tokens_meet_contrast`

#### Scenario: Dark theme
- **WHEN** a visitor views the table in the dark theme
- **THEN** every value stays readable against its fill

### Requirement: 1.3.9 Grouped probability headers
The four probability columns SHALL sit under one "Playoff Forecast" group header, with every column header in small uppercase letters wrapping to two lines where needed.

**Traces to:** 1.3
**Verified by:** Inspection: the live site at 1280 px, the group header spans exactly the four probability columns

#### Scenario: Header layout
- **WHEN** a visitor views the table at 1280 px
- **THEN** "Playoff Forecast" spans the four probability columns above their headers

### Requirement: 1.3.10 Sorting
Every column SHALL sort from its header, descending on the first click (Manager: A to Z) and ascending on the second.

**Traces to:** 1.3
**Verified by:** Test: `tests/layout/test_forecasts_page.py::test_header_clicks_sort_descending_then_ascending`; Test: `tests/layout/test_forecasts_page.py::test_manager_column_sorts_a_to_z`

#### Scenario: Sort by a probability column
- **WHEN** a visitor clicks the "Win Championship" header once
- **THEN** rows are ordered by title probability, highest first

#### Scenario: Second click flips direction
- **WHEN** the visitor clicks the same header again
- **THEN** rows are ordered lowest first

### Requirement: 1.3.10.1 Sort state shown
The sorted column's header SHALL show a dark fill and an arrow for the direction, which no header shows before the table is sorted.

**Traces to:** 1.3.10
**Verified by:** Inspection: the live site, headers before and after a sort

#### Scenario: Untouched table
- **WHEN** a visitor has not clicked any header
- **THEN** no header has a fill or an arrow

### Requirement: 1.3.10.2 Sort keys
Projected record SHALL sort by projected wins, ELO by rating, 1-week change by its signed value, and each probability column by its probability, with unrated teams last.

**Traces to:** 1.3.10
**Verified by:** Test: `tests/layout/test_forecasts_page.py::test_each_column_sorts_by_its_key`

#### Scenario: Sort by ELO
- **WHEN** a visitor clicks the ELO header once
- **THEN** rows are ordered by rating, highest first, with unrated teams last

### Requirement: 1.3.11 Live Forecast in the table
While a week is live, the table SHALL show the live Forecast, labelled with how many of the week's NFL games are final.

**Traces to:** 1.3; 1.2.3
**Verified by:** Test: `tests/test_export.py::test_live_result_drives_the_table_and_history_stays_on_as_of_files`

#### Scenario: Saturday of week 11
- **WHEN** a visitor opens the Forecasts sub-tab on Saturday of week 11
- **THEN** the table shows the live Forecast labelled "Live: 1 of 14 games final"

### Requirement: 1.3.11.1 Live changes
During a live week, the change shown on hover SHALL compare with the as-of Forecast the live run started from.

**Traces to:** 1.3.11; 1.3.6
**Verified by:** Test: `tests/test_export.py::test_live_result_drives_the_table_and_history_stays_on_as_of_files`

#### Scenario: Live change
- **WHEN** a team's live playoff probability is 70% and its as-of-week-10 probability was 60%
- **THEN** hovering shows +10 points

### Requirement: 1.3.12 Freshness shown
The Forecasts sub-tab SHALL show the as-of week of the Forecast and when it was generated.

**Traces to:** 1.3; 5
**Verified by:** Test: `tests/test_export.py::test_refresh_export_shows_this_runs_start_not_the_previous_one`

#### Scenario: Freshness label
- **WHEN** the Forecast was made on 2026-11-17 as of week 10
- **THEN** the page says it is as of week 10 and updated on 2026-11-17

### Requirement: 1.4 Forecast chart
The Forecasts sub-tab SHALL show a line chart with one line per team, plotting the chosen probability at every stored as-of week of the season.

**Traces to:** 1; 1.2
**Verified by:** Inspection: the live site, one line per team and one point per stored as-of week

#### Scenario: Default chart
- **WHEN** a visitor opens a league page with Forecasts as of weeks 0 to 10
- **THEN** the chart shows each team's playoff probability at weeks 0 to 10

### Requirement: 1.4.1 Chart uses as-of Forecasts
The Forecast chart SHALL plot only stored as-of Forecasts, never the live one.

**Rationale:** The history never shows a partly played week.
**Traces to:** 1.4; 1.2.3
**Verified by:** Test: `tests/test_export.py::test_live_result_drives_the_table_and_history_stays_on_as_of_files`

#### Scenario: Live week
- **WHEN** week 11 is live
- **THEN** the chart's last point is still as of week 10

### Requirement: 1.4.2 Chart metric buttons
Metric buttons heading the chart's card SHALL offer the table's four probability columns in the table's order, with Make Playoffs chosen by default.

**Traces to:** 1.4
**Verified by:** Inspection: the live site, button order on each league page

#### Scenario: Metric order
- **WHEN** a visitor views the redraft chart's metric buttons
- **THEN** they read, in order: Avoid Loser's Bye, Make Playoffs, Bye, Win Championship

#### Scenario: Switch metric
- **WHEN** a visitor clicks "Bye"
- **THEN** the chart plots each team's bye probability at every stored as-of week

### Requirement: 1.4.3 Team colours
Each team SHALL keep one distinct line colour across weeks, metrics, sorts and highlighting, shown as a swatch on its table row.

**Traces to:** 1.4
**Verified by:** Inspection: the live site, colours before and after a sort and a metric change

#### Scenario: Colour survives a sort
- **WHEN** a visitor sorts the table by title probability
- **THEN** every team keeps its line colour and row swatch

### Requirement: 1.4.3.1 Readable lines
Every team line colour SHALL have at least 3:1 contrast with the chart background in both themes.

**Traces to:** 1.4.3; 9
**Verified by:** Test: `tests/test_colour_contrast.py::test_colour_tokens_meet_contrast`

#### Scenario: Twelve teams in the dark theme
- **WHEN** a 12-team league's chart is shown in the dark theme
- **THEN** all 12 line colours meet 3:1 against the chart background

### Requirement: 1.4.4 Highlight a team
Picking a team in the chart or the table SHALL keep its line at full strength and dim every other line.

**Traces to:** 1.4
**Verified by:** Test: `tests/layout/test_forecasts_page.py::test_picking_a_team_dims_the_other_lines`

#### Scenario: Highlight a team
- **WHEN** a visitor picks one team in the table
- **THEN** that team's line keeps its colour at full strength and the others are dimmed

### Requirement: 1.4.5 Chart axis
The Forecast chart's axis SHALL run from 0 to the next multiple of 10 at least 5 points above the highest plotted value, no lower than 10% and no higher than 100%.

**Traces to:** 1.4
**Verified by:** Test: `tests/layout/test_forecasts_page.py::test_chart_axis_follows_the_highest_value`

#### Scenario: Axis fits the data
- **WHEN** the highest plotted value is 34%
- **THEN** the axis runs from 0% to 40%

#### Scenario: Axis cap
- **WHEN** the highest plotted value is 100%
- **THEN** the axis top is 100%

### Requirement: 4.1 ELO columns
The ELO and 1-week ELO change columns SHALL show each team's current rating mean, rounded to a whole number, and its signed change over the last rated week.

**Traces to:** 4; 1.3
**Verified by:** Test: `tests/test_export.py::test_export_carries_ratings_when_present`

#### Scenario: Rated team
- **WHEN** a team's rating is 1676 and it rose 20 last week
- **THEN** the ELO cell shows "1676" and the change cell "+20"

### Requirement: 4.1.1 ELO before week one
After a season's draft and before its first scored week, the ELO cell SHALL show the preseason (reverted) rating, the base the week-1 change is measured from.

**Traces to:** 4.1
**Verified by:** Test: `tests/test_export.py::test_preseason_rating_shows_with_no_change_until_week_one`

#### Scenario: Preseason rating shown
- **WHEN** a Manager ended last season at 1300 and this season's draft is done but no week is scored
- **THEN** the ELO cell shows 1200 and the change cell is empty

#### Scenario: Change from the preseason rating
- **WHEN** the same Manager's week-1 rating is 1240
- **THEN** the change cell shows +40

### Requirement: 4.1.2 Empty change cell
The change cell SHALL be empty when a Manager has only one rated week, before week 1, and when the change is zero.

**Traces to:** 4.1
**Verified by:** Test: `tests/test_export.py::test_newcomer_with_one_rated_week_has_no_elo_change`

#### Scenario: Newcomer's first week
- **WHEN** a team's Manager has only one rated week
- **THEN** the ELO cell shows their rating and the change cell is empty

### Requirement: 4.1.3 ELO change fill
A positive 1-week change SHALL show as black text on a green fill, and a negative one as black text on a red fill.

**Traces to:** 4.1
**Verified by:** Inspection: the live site, change cells of +20 and -33 in both themes

#### Scenario: Negative change
- **WHEN** a team's 1-week change is -33
- **THEN** the cell shows "-33" as black text on a red fill

### Requirement: 4.1.4 No ratings yet
While no rating data is exported, the ELO and change columns SHALL show empty cells under their headers.

**Traces to:** 4.1
**Verified by:** Test: `tests/test_export.py::test_exported_schema`

#### Scenario: Before ratings exist
- **WHEN** the exported data carries no ratings
- **THEN** every ELO and change cell is empty and both headers still show

### Requirement: 4.2 Rating chart
Below the Forecast chart, the Forecasts sub-tab SHALL show a line chart with one line per Manager who has played in the league, plotting the chosen rating series at every stored week, with season starts and each season's preseason point marked.

**Traces to:** 4
**Verified by:** Inspection: the live site, the dynasty rating chart from 2022 to the latest week

#### Scenario: Default rating chart
- **WHEN** a visitor opens the dynasty page with ratings stored for 2022 to 2026
- **THEN** the chart shows every Manager's rating at every rated week, with each season start marked

#### Scenario: Preseason point
- **WHEN** a season's draft is done
- **THEN** the chart shows a "Pre" point at that season's start holding each Manager's reverted rating

### Requirement: 4.2.1 Rating metrics
Metric buttons leading the rating chart's card SHALL offer "Rating", the Openskill rating mean and the default, and "Z-score", the career mean z-score plotted with a reference line at zero.

**Traces to:** 4.2
**Verified by:** Inspection: the live site, both metrics on the dynasty rating chart

#### Scenario: Z-score metric
- **WHEN** a visitor clicks "Z-score"
- **THEN** the chart plots each Manager's career mean z-score with a reference line at zero

### Requirement: 4.2.2 Rating chart range
Range buttons below the rating chart, smaller than its metric buttons, SHALL offer "This season", "Last 3 seasons" and "All time" (the default), limiting the plotted weeks without changing colours or the chosen metric.

**Traces to:** 4.2
**Verified by:** Inspection: the live site, each range on the dynasty rating chart

#### Scenario: Last three seasons
- **WHEN** a visitor picks "Last 3 seasons" in a league with seasons 2021 to 2026
- **THEN** weeks from 2024, 2025 and 2026 are plotted and each line keeps its colour

### Requirement: 4.2.2.1 Short history
In a league with fewer than three stored seasons, "Last 3 seasons" SHALL plot the same weeks as "All time".

**Traces to:** 4.2.2
**Verified by:** Test: `tests/layout/test_forecasts_page.py::test_last_three_seasons_equals_all_time_with_a_short_history`

#### Scenario: Two seasons stored
- **WHEN** a league has seasons 2025 and 2026
- **THEN** "Last 3 seasons" plots the same weeks as "All time"

### Requirement: 4.2.3 Manager colours
A current Manager's rating line SHALL use their team's colour from the Forecast chart.

**Traces to:** 4.2; 1.4.3
**Verified by:** Inspection: the live site, each current Manager's colour in both charts

#### Scenario: Same colour in both charts
- **WHEN** a team's Forecast line is teal
- **THEN** its Manager's rating line is the same teal

### Requirement: 4.2.3.1 Former Managers
Former Managers' rating lines SHALL use greys distinct from one another and from every current Manager's colour, each with at least 3:1 contrast with the chart background in both themes.

**Traces to:** 4.2.3; 9
**Verified by:** Inspection: the live site in both themes, the five former dynasty Managers' lines

#### Scenario: Former members
- **WHEN** the dynasty rating chart shows five former Managers
- **THEN** their lines are five different greys, none matching a current Manager's colour

### Requirement: 4.2.5 Vacant rosters hidden
Only rosters held by a Manager in at least one stored season SHALL be drawn on the rating chart.

**Traces to:** 4.2
**Verified by:** Test: `tests/test_vacant_owner.py::test_never_owned_stays_vacant`

#### Scenario: Vacant roster hidden
- **WHEN** a roster had no Manager in any stored season
- **THEN** no line is drawn for it, though the other Managers' ratings reflect its scores

### Requirement: 4.2.6 Inherited rosters
A roster without a Manager in a season SHALL be drawn as part of the line of the Manager who held it before or after.

**Traces to:** 4.2
**Verified by:** Test: `tests/test_vacant_owner.py::test_owner_quit_before_the_year_ended`; Test: `tests/test_vacant_owner.py::test_vacant_in_the_first_stored_season_takes_the_later_owner`

#### Scenario: Inherited roster drawn
- **WHEN** dynasty roster 11 had no Manager in 2023 and was DeekBurg's in 2022
- **THEN** DeekBurg's line continues through 2023

### Requirement: 4.2.7 End labels
Every rating line SHALL be labelled with its Manager's display name at its end.

**Traces to:** 4.2
**Verified by:** Inspection: the live site, every line on the dynasty rating chart has an end label

#### Scenario: End label
- **WHEN** the rating chart is drawn
- **THEN** each line ends with its Manager's display name

### Requirement: 4.2.4 Highlight across charts
Picking a team in the table or a line in the rating chart SHALL keep that Manager's line at full strength in both charts and dim the others.

**Traces to:** 4.2; 1.4.4
**Verified by:** Test: `tests/layout/test_forecasts_page.py::test_picking_a_team_highlights_its_manager_in_both_charts`

#### Scenario: Highlight a Manager
- **WHEN** a visitor picks one line in the rating chart
- **THEN** that Manager's lines keep full strength in both charts and the others are dimmed

### Requirement: 4.3 Rating history exported
Each league's site data SHALL include every Manager's rating history (rating mean and career mean z-score for each rated week, with season and week), display name, and current or former status.

**Traces to:** 4; 4.1; 4.2
**Verified by:** Test: `tests/test_export.py::test_export_carries_ratings_when_present`

#### Scenario: Ratings present
- **WHEN** the export runs after the ratings command
- **THEN** each team row carries its ELO and change, and the league file carries the rating history of current and former Managers

### Requirement: 4.3.1 Export without ratings
The export SHALL succeed without a rating file, leaving the rating chart to say that ratings are not yet available.

**Traces to:** 4.3
**Verified by:** Test: `tests/test_export.py::test_exported_schema`

#### Scenario: Ratings absent
- **WHEN** the export runs on a store without rating files
- **THEN** the league files are written with empty ELO cells and no rating history, and the page says ratings are not yet available
