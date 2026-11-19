# league-odds-site Specification

## Purpose

Gives league members a public website where they can see their team's current playoff odds and how those odds have changed over the season. A scheduled job keeps it current.

## Requirements

### Requirement: League pages
The site SHALL have a page for each configured league that shows that league's current season. Visitors SHALL be able to switch between leagues. Each league page SHALL have four sub-tabs in this order: "Predictions" (the odds table and charts), "Games", "Positions" and "Player WAR". The selected sub-tab SHALL be kept in the page URL, so a link opens on that sub-tab, and SHALL be kept when switching league.

#### Scenario: Switch league
- **WHEN** a visitor on the dynasty page picks the redraft league
- **THEN** the redraft league's odds are shown

#### Scenario: Open the WAR sub-tab
- **WHEN** a visitor on the redraft Predictions sub-tab picks "Player WAR"
- **THEN** the redraft Player WAR page is shown and the URL identifies both the league and the sub-tab

#### Scenario: Link to a sub-tab
- **WHEN** a visitor opens a link whose URL names the dynasty league and the Player WAR sub-tab
- **THEN** the page opens on the dynasty Player WAR page

#### Scenario: Open the Games sub-tab
- **WHEN** a visitor picks "Games", which sits between "Predictions" and "Positions"
- **THEN** the league's Games page is shown and the URL identifies the league and the Games sub-tab

#### Scenario: Open the Positions sub-tab
- **WHEN** a visitor picks "Positions", which sits between "Games" and "Player WAR"
- **THEN** the league's Positional Rankings page is shown and the URL identifies the league and the Positions sub-tab

### Requirement: Current odds table
Each league page SHALL show a table with one row per team and these columns in order: ELO, 1-week ELO change, Manager (the manager's display name in bold with the team name beneath it and the current record beside the name), projected final record, and four chance columns: the league's bottom column (see "League-dependent bottom column"), make playoffs, first-round bye, win championship. Until a visitor sorts the table, rows SHALL be in league standings order: wins (a tie counts half), then points scored. Columns left of Manager SHALL be left-aligned, the Manager column centred, and columns right of it right-aligned, headers and cells alike. The table SHALL be compact: the ELO and 1-week change columns no wider than their content needs, tight row padding, and text a step larger than body text.

#### Scenario: Table contents
- **WHEN** a visitor opens the dynasty page with the as-of-week-10 results stored
- **THEN** the table shows all 12 teams with the as-of-week-10 values in standings order

#### Scenario: Owner cell
- **WHEN** a team is managed by `tg1212`, named "Diaper Dandies" and has 7 wins, 2 losses and no ties
- **THEN** its Manager cell shows "tg1212" in bold with "7-2" beside it and "Diaper Dandies" beneath, centred in the column under the header "Manager"

#### Scenario: Alignment
- **WHEN** the table is shown at any width
- **THEN** the ELO and 1-week change headers and cells are left-aligned, the Manager header and cells centred, and the projected record and chance headers and cells right-aligned

#### Scenario: Projected record format
- **WHEN** a team's projected record is 10.59 wins and 3.41 losses
- **THEN** the projected record cell shows "10.6 - 3.4"

#### Scenario: Weekly change
- **WHEN** results exist for both the current as-of week and the one before it
- **THEN** hovering over any of a team's chance cells shows that chance's change since the previous as-of week, and no separate change column is shown

#### Scenario: First week of results
- **WHEN** results exist only for the current as-of week
- **THEN** chance cells show no change information

### Requirement: Odds-over-time chart
Each league page SHALL show a line chart with one line per team, plotting a chosen chance for each stored as-of week of the season.

#### Scenario: Default chart
- **WHEN** a visitor opens a league page with results for as-of weeks 0 through 10
- **THEN** the chart shows each team's playoff chance at weeks 0 through 10

#### Scenario: Metric order
- **WHEN** a visitor views the redraft chart's metric buttons
- **THEN** they read, in order: Avoid Loser's Bye, Make Playoffs, Bye, Win Championship

#### Scenario: Bottom-column metric
- **WHEN** a visitor on the redraft page switches the chart to the bottom column
- **THEN** the chart plots each team's chance of avoiding the loser's bye for every stored as-of week

#### Scenario: Distinct team colors
- **WHEN** a visitor views a 12-team league's chart in either theme
- **THEN** the 12 lines use 12 different colors, each readable against the chart background, and each team's table row shows a swatch of its line color

#### Scenario: Highlight a team
- **WHEN** a visitor picks one team in the chart or table
- **THEN** that team's line keeps its color at full strength and the others are dimmed

#### Scenario: Axis fits the data
- **WHEN** the visitor switches to the title metric and the highest plotted value is 34%
- **THEN** the axis runs from 0% to 40%

#### Scenario: Axis cap
- **WHEN** the highest plotted value is 100%
- **THEN** the axis top is 100%

### Requirement: Freshness shown
Each league page SHALL show the as-of week of the results and when they were generated.

#### Scenario: Freshness label
- **WHEN** the results were produced on 2026-11-17 as of week 10
- **THEN** the page states the results are as of week 10 and were updated on 2026-11-17

### Requirement: Static and public
The site SHALL be static files that need no server code, login or calls to Sleeper from the visitor's browser. Anyone with the link SHALL be able to view it. The optional refresh button MAY call the refresh relay; every page SHALL work fully when the relay is not configured or not reachable.

#### Scenario: Visitor loads page
- **WHEN** a visitor opens a league page
- **THEN** all data comes from files published with the site

#### Scenario: Relay down
- **WHEN** the refresh relay does not answer
- **THEN** the pages show their data as usual and the button reports that a refresh could not be started

### Requirement: Usable on phones
League pages SHALL be readable on a 375px-wide screen without horizontal page scrolling. The odds table MAY scroll horizontally inside its own container. Below 600 px the Manager column SHALL stay pinned to the container's left edge while the table scrolls, with ELO and 1-week change scrolling away beneath it; manager names SHALL not wrap. When the sub-tabs do not fit the screen width, the sub-tab menu SHALL scroll sideways inside its own strip with a swipe:

- The tabs SHALL snap into place.
- The edge with more tabs beyond it SHALL fade.
- The selected sub-tab SHALL be scrolled into view on load.
- No scroll bar SHALL show.
- Swiping the menu SHALL not move the rest of the page.

#### Scenario: Phone visit
- **WHEN** a visitor opens a league page on a 375px-wide screen
- **THEN** the page itself doesn't scroll sideways and the chart fits the screen width

#### Scenario: Swipe the sub-tabs
- **WHEN** a visitor on a 375px-wide screen swipes the sub-tab menu left
- **THEN** the menu scrolls to reveal "Player WAR", the tabs settle on a tab edge, and the page below stays where it was

#### Scenario: Linked to the last sub-tab
- **WHEN** a visitor on a phone opens a link to the Player WAR sub-tab
- **THEN** the menu opens scrolled so "Player WAR" is visible and marked selected

#### Scenario: Wide screen
- **WHEN** the sub-tabs fit the screen width
- **THEN** the menu does not scroll and shows no fade

#### Scenario: Scroll the forecast table on a phone
- **WHEN** a visitor on a 440 px-wide phone scrolls the forecast table to the right
- **THEN** the ELO and 1-week change columns scroll out of view while the Manager column stays at the left edge beside the chance columns

### Requirement: Scheduled refresh
A scheduled job SHALL check hourly, following the game-aware schedule, whether to refresh, and SHALL refresh at least daily. A refresh SHALL update league data, projections, stats, the NFL schedule, injury statuses and the start-percentage snapshot; recompute ratings, replacement levels, WAR, the odds for the current as-of week and the game logs and records; commit the stored data and republish the site. The job SHALL also be startable by hand.

#### Scenario: Day after Monday night
- **WHEN** the scheduled run happens the day after Monday night's game ends and week 10 is final in Sleeper
- **THEN** the published site shows results as of week 10

#### Scenario: Failed refresh
- **WHEN** any step of the scheduled job fails
- **THEN** the previously published site stays online unchanged, no partial data is committed, and the job run is marked failed

#### Scenario: Stats and replacement levels refreshed
- **WHEN** the scheduled run completes
- **THEN** the current season's stats for played weeks and the current season's replacement levels are stored alongside the odds

#### Scenario: Ratings refreshed
- **WHEN** the scheduled run completes after week 10 is final
- **THEN** every league's rating file includes week 10 and the published table shows the updated ELO values

#### Scenario: Snapshot and WAR refreshed
- **WHEN** the scheduled run completes during week 11
- **THEN** the week-11 start-percentage snapshot is stored and every league's current-season WAR file and leaderboard reflect the weeks scored so far

#### Scenario: ESPN unavailable
- **WHEN** the snapshot capture fails during a scheduled run
- **THEN** the failure is logged, the remaining steps still run using the snapshots already stored, the odds are still refreshed and published, and the run ends with a warning naming the skipped step and the reason, shown as an annotation on the job run

#### Scenario: Games refreshed before kickoff
- **WHEN** the refresh runs 40 minutes before Sunday's 1 pm games
- **THEN** the NFL schedule, injury statuses and every current-week game log are updated and the Games page shows the new forecasts

### Requirement: League-dependent bottom column
The first chance column SHALL depend on the league's Sleeper settings. A toilet-bowl league SHALL show "Avoid Loser's Bye": the chance of finishing outside the bottom two of the regular-season standings. A dynasty league with a consolation bracket SHALL show "#1 Pick": the chance of finishing last. Any other league SHALL show "Avoid Loser's Bye". The exported data SHALL name the column so the site needs no league-specific rules.

#### Scenario: Toilet-bowl league
- **WHEN** a visitor opens the redraft page (toilet bowl) for a team that finishes 11th in 3% of runs and 12th in 1%
- **THEN** the first chance column is titled "Avoid Loser's Bye" and shows 96% for that team

#### Scenario: Dynasty consolation league
- **WHEN** a visitor opens the dynasty page (consolation bracket, dynasty league) for a team that finishes last in 40% of runs
- **THEN** the first chance column is titled "#1 Pick" and shows 40% for that team

### Requirement: Chance cell fill
Every chance cell SHALL be filled with a single-hue blue that gets darker as the chance rises: no fill at or below 1%, the darkest blue at or above 99%, and text that stays readable at every step, switching to light text on dark fills. Values SHALL print as "<1%", ">99%" or a whole-number percentage. Each theme SHALL use a ramp designed for its own background rather than a flipped copy of the other theme's.

#### Scenario: Low, mid and high chances
- **WHEN** three teams have 0.3%, 50% and 99.6% playoff chances
- **THEN** their cells read "<1%", "50%" and ">99%", with no fill, a mid blue, and the darkest blue with light text respectively

#### Scenario: Dark theme
- **WHEN** a visitor views the table in the dark theme
- **THEN** chance cells use the dark-theme ramp and every value stays readable against its fill

### Requirement: Odds table sorting
Every table column SHALL be sortable from its header. The first click on a header SHALL sort descending (owner: A to Z), the second ascending, and the sorted header SHALL show a dark fill and a small arrow for the direction. An unsorted table SHALL show no fill and no arrow on any header. Record sorts by wins then points scored; projected record by projected wins; ELO by rating; 1-week ELO change by the signed change.

#### Scenario: Sort by a chance column
- **WHEN** a visitor clicks the "Win Championship" header once
- **THEN** rows are ordered by championship chance, highest first, and that header shows a dark fill and a down arrow

#### Scenario: Second click flips direction
- **WHEN** the visitor clicks the same header again
- **THEN** rows are ordered lowest first and the arrow points up

#### Scenario: Untouched table
- **WHEN** a visitor opens a league page and has not clicked any header
- **THEN** no header has a fill or an arrow

#### Scenario: ELO headers not yet sortable
- **WHEN** a visitor clicks the ELO or 1-week change header while the exported data carries no ratings
- **THEN** the header takes the sorted state and the row order does not change, since every value is empty

#### Scenario: Sort by ELO
- **WHEN** a visitor clicks the ELO header once
- **THEN** rows are ordered by rating, highest first, and teams without a rating sort last

### Requirement: ELO placeholder columns
The ELO and 1-week ELO change columns SHALL show each team's current manager rating mean, rounded to a whole number, and its signed change over the last rated week. While no rating data is exported, both columns SHALL render as empty cells.

#### Scenario: Before ELO exists
- **WHEN** the exported data carries no ELO values
- **THEN** every ELO and 1-week change cell is empty and the two headers are still shown

#### Scenario: Future ELO change rendering
- **WHEN** the exported data gives a team an ELO of 1676 and a 1-week change of +20
- **THEN** the ELO cell shows "1676" and the change cell shows "+20" as black text on a green fill

#### Scenario: First rated week of a newcomer
- **WHEN** a team's manager has only one rated week
- **THEN** the ELO cell shows their rating and the change cell is empty

#### Scenario: After the draft, before week 1
- **WHEN** a manager ended last season at 1300 and this season's draft is done but no week is scored
- **THEN** the ELO cell shows 1200 and the change cell is empty

#### Scenario: Week 1 change
- **WHEN** the same manager's week-1 rating is 1240
- **THEN** the change cell shows +40

### Requirement: Grouped chance headers
The four chance columns SHALL sit under a single "Playoff chances" group header, and every column header SHALL use small uppercase labels that wrap to two lines where needed.

#### Scenario: Header layout
- **WHEN** a visitor views the table on a desktop-width screen
- **THEN** a "Playoff chances" label spans exactly the four chance columns, above their individual headers

### Requirement: Calibration page
The site SHALL have a calibration page, reachable from every league page, that shows how well past odds matched real outcomes: for each season outcome, predicted chance against observed rate with the number of cases behind each point; observed against nominal coverage of the score intervals; the Brier skill against the baseline; the lineup gap per league; when the calibration was produced, how many seasons it covers and the residual scale used; and the known caveats.

#### Scenario: Visitor checks the odds
- **WHEN** a visitor opens the calibration page after a calibration report has been published
- **THEN** they can see, for playoff chances, how often teams shown at each level of chance actually made the playoffs

#### Scenario: Calibration not yet run
- **WHEN** the site is published without a calibration report
- **THEN** the calibration page says calibration has not been run and the league pages work as before

#### Scenario: Data from published files
- **WHEN** the calibration page loads
- **THEN** all figures come from a file published with the site, with no server code

#### Scenario: Member reads how it works
- **WHEN** a league member opens the calibration page
- **THEN** they can read what a replacement-level player is, see this week's replacement level per position for each league, and see how many of a 20-point edge the model expects a team to keep two and twelve weeks out, computed from the published drift model

#### Scenario: Model switches shown
- **WHEN** the calibration page shows a report
- **THEN** it states whether the replacement floor and roster drift were on for that report and the N used

### Requirement: Calibration report exported
The export SHALL include the stored calibration report in the site data when one exists, and SHALL succeed without one.

#### Scenario: Report present
- **WHEN** the export runs after calibration has been run
- **THEN** the site data contains the calibration report that was stored

#### Scenario: Report absent
- **WHEN** the export runs on a store that has never been calibrated
- **THEN** the league files are written as usual and the export succeeds

### Requirement: Replacement levels exported
Each league's site data SHALL include the current season's replacement levels: the next unplayed week's projected level per position, the season values, the N used, and the drift model in force, so the calibration page can explain the model with live numbers. The export SHALL succeed when the replacement or model files are missing, leaving those fields absent.

#### Scenario: Levels present
- **WHEN** the export runs after the replacement and simulate commands
- **THEN** the dynasty and redraft site files carry the replacement levels for the next unplayed week and the drift factors

#### Scenario: Levels absent
- **WHEN** the export runs on a store without replacement files
- **THEN** the league files are written without the replacement fields and the page explains the model without the live numbers

### Requirement: Chart metric buttons
Metric buttons at the top left of the odds-over-time chart's card, where they serve as the chart's heading, SHALL offer the table's four chance columns in the table's order, and the chart SHALL plot the chosen chance (playoffs by default). When the buttons do not fit on one line they SHALL form one row that scrolls sideways under a finger, without wrapping and without moving the page. On narrow screens the chart SHALL use the card's full width, reserving room at its right edge for an end label only while a team is highlighted, and then only that label's width.

#### Scenario: Switch metric
- **WHEN** a visitor clicks the "Bye" metric button
- **THEN** the chart plots each team's first-round-bye chance for every stored as-of week

#### Scenario: Buttons on a phone
- **WHEN** the redraft page is shown at 375 px
- **THEN** the four metric buttons sit on one line that can be swiped sideways, and the chart spans the card's width

#### Scenario: Highlighted team on a phone
- **WHEN** a visitor on a phone highlights a team
- **THEN** that team's end label shows at the right of the chart, which gives up only that label's width

### Requirement: Team chart colours
Each team's line on the odds-over-time chart SHALL have its own distinct colour, unchanged across weeks, metrics, sorts and highlighting, and the same colour SHALL mark that team's row in the table.

#### Scenario: Colour survives a sort
- **WHEN** a visitor sorts the table by championship chance
- **THEN** every team keeps the line colour and row swatch it had before the sort

### Requirement: Odds chart axis range
The odds-over-time chart's axis floor SHALL be 0 and its top the next multiple of 10 at least 5 points above the highest plotted value, capped at 100.

#### Scenario: Mid-range values
- **WHEN** the highest plotted value is 62%
- **THEN** the axis runs from 0% to 70%

### Requirement: Rating chart
Each league page SHALL show a second line chart, below the odds-over-time chart, with one line per manager who has ever played in the league, plotting the chosen rating series for every stored week since the league's first stored season, including each season's preseason point where one exists. Metric buttons SHALL offer "Rating" (the Openskill rating mean, default) and "Z-score" (the career mean z-score). The x-axis SHALL label season boundaries.

#### Scenario: Default rating chart
- **WHEN** a visitor opens the dynasty page with ratings stored for 2022 through 2026
- **THEN** the chart shows every manager's rating mean at every rated week from 2022 week 1 to the latest rated week, with each season start marked on the axis

#### Scenario: Z-score metric
- **WHEN** a visitor clicks "Z-score"
- **THEN** the chart plots each manager's career mean z-score over the same weeks, with a reference line at zero

#### Scenario: Highlight a manager
- **WHEN** a visitor picks one team in the table or one line in the rating chart
- **THEN** that manager's line keeps full strength in both charts and the others are dimmed

#### Scenario: Preseason point
- **WHEN** a season's draft is done
- **THEN** the chart shows a "Pre" point at that season's start holding each manager's reverted rating, so the step toward 1000 is visible

### Requirement: Rating chart time range
Range buttons below the rating chart, smaller than the Rating and Z-score buttons above it, SHALL offer "This season", "Last 3 seasons" and "All time" (default "All time"), and SHALL limit the plotted weeks without changing any manager's colour or the chosen metric. A league with fewer than three stored seasons SHALL show "Last 3 seasons" as the same range as "All time".

#### Scenario: This season
- **WHEN** a visitor on the redraft page picks "This season" during 2026
- **THEN** only 2026's rated weeks are plotted and each line keeps its colour

#### Scenario: Last three seasons
- **WHEN** a visitor picks "Last 3 seasons" on a league with seasons 2021 through 2026
- **THEN** weeks from 2024, 2025 and 2026 are plotted

#### Scenario: Placement
- **WHEN** the rating chart is shown
- **THEN** the Rating and Z-score buttons lead the card above the chart and the range buttons sit below the chart in a smaller size

### Requirement: Manager colours on the rating chart
A current member's line SHALL use the same colour as their team's line on the odds chart and row in the table. Former members SHALL use greys distinct from one another and readable against the chart background in both themes. Vacant rosters (rosters with no owner in any stored season) SHALL NOT be drawn. A roster that inherits an earlier or later owner SHALL be drawn as part of that owner's line. Every drawn line SHALL be labelled with the manager's display name at its end.

#### Scenario: Former members
- **WHEN** the dynasty rating chart shows five former members
- **THEN** their five lines are five different greys, none of which matches a current member's colour

#### Scenario: Vacant roster hidden
- **WHEN** a season has a roster with no owner in any stored season
- **THEN** no line is drawn for it, though the other managers' ratings reflect its scores

#### Scenario: Inherited owner drawn
- **WHEN** dynasty roster 11 has no owner in 2023 and was DeekBurg's in 2022
- **THEN** DeekBurg's grey line continues through 2023

### Requirement: Rating history exported
Each league's site data SHALL include every manager's rating history (rating mean and career mean z per rated week, with season and week), display name and current or former status, and each current team's latest rating mean and its change over the last rated week. The export SHALL succeed when no rating file exists, leaving the table's ELO cells empty and the rating chart stating that ratings are not yet available.

#### Scenario: Ratings present
- **WHEN** the export runs after the ratings command
- **THEN** each team row carries its ELO and 1-week change and the league file carries the full rating history for current and former managers

#### Scenario: Ratings absent
- **WHEN** the export runs on a store without rating files
- **THEN** the league files are written with empty ELO cells and no rating history, and the page says ratings are not yet available

### Requirement: Fresh scripts after deploy
Every script and stylesheet the site's pages load, and every import between scripts, SHALL carry a stamp in its URL that every deploy replaces with a fingerprint of the site's code files (pages, scripts, stylesheet and bundled libraries, never the data files). The fingerprint SHALL depend only on the content of those files, so a deploy that changes only data keeps the same stamp. Every deploy SHALL publish the same fingerprint in a version file beside the pages and SHALL produce the stamp and version file with one shared stamping command. The source files SHALL carry a placeholder in its place so the site runs unchanged from a local server.

#### Scenario: New deploy
- **WHEN** a visitor whose browser cached the previous deploy's scripts opens the site after a deploy that changed site code
- **THEN** the page references script and stylesheet URLs with the new stamp and the browser fetches the new files

#### Scenario: Data-only deploy
- **WHEN** an hourly refresh deploys new data and no site code changed
- **THEN** the stamp and the published fingerprint are the same as the previous deploy's and browsers reuse their cached scripts

#### Scenario: Local server
- **WHEN** the site is served from the repository checkout
- **THEN** the pages load with the placeholder in the script and stylesheet URLs and work as before

#### Scenario: Reference without a stamp
- **WHEN** a script or stylesheet reference or module import in the site files lacks the placeholder
- **THEN** the test suite fails naming the file

#### Scenario: Deploy without the stamping command
- **WHEN** a workflow that deploys the site does not run the shared stamping command before the upload
- **THEN** the test suite fails naming the workflow

### Requirement: ELO columns before week one
After a season's draft and before its first scored week, the ELO cell SHALL show the preseason (reverted) rating and the change cell SHALL be empty; from week 1 the change SHALL be measured from that preseason rating. A manager with only one rated week SHALL show their rating and an empty change cell.

#### Scenario: Preseason rating shown
- **WHEN** a manager ended last season at 1300 and this season's draft is done but no week is scored
- **THEN** the ELO cell shows 1200 and the change cell is empty

#### Scenario: Change from the preseason rating
- **WHEN** the same manager's week-1 rating is 1240
- **THEN** the change cell shows +40

#### Scenario: Newcomer's first week
- **WHEN** a team's manager has only one rated week
- **THEN** the ELO cell shows their rating and the change cell is empty

### Requirement: ELO change fill
A positive 1-week ELO change SHALL render as black text on a green fill, a negative change as black text on a red fill, and no change as an empty cell.

#### Scenario: Positive change
- **WHEN** a team's 1-week change is +20
- **THEN** the change cell shows "+20" as black text on a green fill

#### Scenario: Negative change
- **WHEN** a team's 1-week change is -33
- **THEN** the change cell shows "-33" as black text on a red fill

### Requirement: Odds model explained
The calibration page SHALL explain, in plain language for league members, how the odds are made: projections, score noise from past seasons, best lineups with the replacement-level floor, and roster drift, with each league's current replacement levels and how much of a team's edge the model expects to survive weeks ahead. It SHALL state whether the replacement floor and roster drift were on for the shown report and the N used.

#### Scenario: Member reads the explanation
- **WHEN** a league member opens the calibration page
- **THEN** they can read what a replacement-level player is, see this week's replacement level per position for each league, and see how much of a 20-point edge the model expects a team to keep two and twelve weeks out, computed from the published drift model

#### Scenario: Switches stated
- **WHEN** the calibration page shows a report
- **THEN** it states whether the replacement floor and roster drift were on for that report and the N used

### Requirement: Live odds on the Predictions page
While a week is live, the Predictions table SHALL show the live result's chances, labelled with how many of the week's NFL games are final, and its change tooltips SHALL compare with the as-of result the live run started from. The odds-over-time chart SHALL keep plotting only stored as-of results.

#### Scenario: Saturday of week 11
- **WHEN** a visitor opens the Predictions page on Saturday of week 11
- **THEN** the table shows the live chances labelled "Live: 1 of 14 games final" and the chart's last point is still as of week 10

### Requirement: Deploy on code push
A push to the main branch that changes site code (anything under the site folder other than its data files) SHALL run the tests and the layout check and, when they pass, deploy the site with the current data. It SHALL never run at the same time as a data refresh.

#### Scenario: Code pushed
- **WHEN** a commit changing the Games page script is pushed
- **THEN** the site deploys with it within a few minutes, without waiting for the next data refresh

#### Scenario: Data-only push
- **WHEN** the data refresh pushes its data commit
- **THEN** no code-push deploy runs
