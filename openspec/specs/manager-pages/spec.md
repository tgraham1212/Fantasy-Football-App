# manager-pages Specification

## Purpose

The Managers sub-tab: one page per league manager, inspired by Football Manager's club page, with a team info bar, a current season info bar and four cards (Roster, Team History, Moves, Team News), laid out for desktop and phones.

## Requirements

### Requirement: Manager picker
The Managers page SHALL show one manager at a time, chosen from a dropdown flanked by previous and next arrows. The list SHALL show current managers first, then a "Retired" group of managers no longer in the league. The chosen manager SHALL be kept in the page URL and kept when switching league if that manager is in the other league, otherwise the league's first manager is shown.

#### Scenario: Step to the next manager
- **WHEN** a visitor on tg1212's page presses the next arrow
- **THEN** the next manager in the list is shown and the URL names that manager

#### Scenario: Link to a manager
- **WHEN** a visitor opens a link naming the redraft league, the Managers sub-tab and kjern17
- **THEN** kjern17's redraft page is shown

### Requirement: Manager names link to their page
Every manager name shown in the site's tables and lists (Forecasts, Games, Positions, Player WAR, and the Managers page itself) SHALL link to that manager's page in the same league.

#### Scenario: Name in the forecast table
- **WHEN** a visitor selects "djernberg" in the Forecasts table
- **THEN** djernberg's Managers page opens

### Requirement: Team info bar
The page SHALL open with a team info bar showing:
- the crest: the team logo, else the Sleeper avatar, else the initials in the team colour (light fill, darker letters and outline, letters at least 4.5:1);
- the current team name;
- champion banners, and after a wider gap toilet bowl banners, which stack when one row does not fit;
- Form, Founded (or Seasons for retired managers), All-Time, Rating and Rival, separated by light dividers.

#### Scenario: Champion and toilet bowl
- **WHEN** a manager won the 2023 title and the 2022 toilet bowl
- **THEN** a gold 2023 banner hangs on the left rod and a brown 2022 banner on a second rod after a gap

#### Scenario: No banners
- **WHEN** a manager has neither
- **THEN** the banner space stays empty

#### Scenario: Retired manager
- **WHEN** TateFM's dynasty page is shown
- **THEN** Form is hidden and the bar reads "Seasons 2022–2023" instead of "Founded"

### Requirement: Form bars
Form SHALL show the five most recent results of the current season as bars from a centre line, oldest on the left: a win rises (+1, green), a loss drops (−1, red), and a draw or a week with no game is a short grey dash on the line (0). Before week 1 all five SHALL be draws. The bars SHALL carry the sequence as text for screen readers.

#### Scenario: Pre-season
- **WHEN** no game of the season has been played
- **THEN** Form shows five grey dashes

### Requirement: Season info bar
Below the team info bar the page SHALL show seven tiles:
1. Current League Position, with the record and points for;
2. Last Result, with both crests and the score;
3. Next Matchup, with the win forecast and a Rivalry Week badge in rivalry week;
4. Manager, with the Win Rate;
5. Top Scorer;
6. Best Player All-Time, with WAR and seasons on the team;
7. Playoff Forecast, with the change since the previous week.

#### Scenario: Rivalry week
- **WHEN** the next game is against the manager's rival in rivalry week
- **THEN** the Next Matchup tile carries a Rivalry Week badge

#### Scenario: Before week 1
- **WHEN** no game has been played
- **THEN** Top Scorer shows the roster's highest projected scorer labelled "Top Scorer (Projected)"

#### Scenario: Retired manager tiles
- **WHEN** a retired manager's page is shown
- **THEN** the tiles show their last season, labelled with its year, and Next Matchup and Playoff Forecast read "Retired"

### Requirement: Season tile layout
Every tile SHALL share one layout: a fixed first line holding a 32 px image or a large number, then a detail line, so images and numbers line up across the bar. Tile text SHALL scale with the tile's width; on the narrowest tiles label icons SHALL hide first. The Last Result score SHALL never wrap and both crests SHALL stay inside the tile, the score shrinking first. Each tile SHALL link to the page its number comes from. On phones the tiles SHALL form two columns, the seventh spanning both.

#### Scenario: Narrow tile
- **WHEN** the Last Result tile is at its narrowest
- **THEN** the score text shrinks and both crests stay inside the tile

#### Scenario: Wide system font
- **WHEN** the page is drawn at 360 px and 1280 px with a wide font like the Linux defaults
- **THEN** no tile's text is cut

### Requirement: Long names on tiles and cards
Player names on the tiles and cards SHALL follow the player name standard: the full name when it fits, otherwise the first initial and last name ("A. St. Brown"), with the full name as a tooltip, fitted again when the width changes or a hidden card is shown. They SHALL fit without being cut at every tested width.

#### Scenario: Longest name on a phone
- **WHEN** Jaxon Smith-Njigba is the top scorer on a 360 px phone
- **THEN** the tile shows "J. Smith-Njigba" in full

#### Scenario: Room for the full name
- **WHEN** a roster card at 1280 px has room for "Amon-Ra St. Brown"
- **THEN** the full name shows

### Requirement: Card layout
The four cards SHALL sit side by side on desktop with the Roster card widest, all the same height, each scrolling vertically inside itself and never sideways. On phones (below 600 px) a tab row (Roster, History, Moves, News) SHALL show one card at a time; a phone card SHALL never scroll inside itself, SHALL share one minimum height, and SHALL grow when its content is longer.

#### Scenario: Phone card switch
- **WHEN** a phone visitor taps "History"
- **THEN** only the Team History card is shown, with no scrollbar of its own

### Requirement: Roster card
The Roster card SHALL list the current roster (a retired manager's final roster) in lineup order, then bench, IR and taxi, with columns for:
- **Slot:** a pill in the position colour. FLEX shows RB, WR and TE in thirds; BN is outlined; IR is red; Taxi is gold.
- **Status:** a badge, red for the site's out statuses and grey for Questionable.
- **Player, Position and PPG.**

A footer SHALL show this week's starter and bench points.

#### Scenario: Doubtful player
- **WHEN** a bench player is Doubtful
- **THEN** his status badge is red, like Out

### Requirement: PPG chip colours
The PPG chip SHALL be coloured against the position's replacement level R:
- dark green at 1.5R or more;
- light green at 1.2R or more;
- grey from 0.9R to 1.2R;
- light red below 0.9R;
- red below 0.7R.

#### Scenario: Weak bench player
- **WHEN** a receiver averages 4.9 against a WR replacement level of 8.8
- **THEN** his chip is red

### Requirement: Team History card
The Team History card SHALL have three tabs:
- **History:** an About sentence, the League History chart, Honours (years only, no counts), and Luck (numbers right-aligned).
- **Head to Head:** one row per opponent, rival first, with the record, points and a last result that never wraps.
- **Records:** values centred on their rows, then team name history.

#### Scenario: Head to head order
- **WHEN** the Head to Head tab is opened
- **THEN** the rival is the first row, followed by the other opponents by games played

### Requirement: League History chart
The chart SHALL plot each season's final finish, 1st at the top, with the playoff places shaded. A gold trophy SHALL mark a title, 💩 a toilet bowl, a green dot a playoff season and a grey dot a miss. The current season SHALL be a hollow dot at the forecast finish, joined by a dashed line. The legend SHALL fit on one line.

#### Scenario: Current season
- **WHEN** the season is under way with a forecast finish of 3rd
- **THEN** a hollow dot sits at 3rd in the current season's column

#### Scenario: Records with ranks
- **WHEN** a manager's highest score is the league's highest ever
- **THEN** the record carries a gold "#1 All Time" tag

### Requirement: Team News card
The Team News card SHALL show the most important story of the latest week as a feature story, with a picture drawn from the data (for a result, both crests and the score, sized to fit the card). Below it, "More Stories" SHALL list the rest, newest first, each with a thumbnail, headline, time, category and a link to its source page. On phones the first seven stories SHALL show, with a "Show more" button.

#### Scenario: Feature result
- **WHEN** the latest week's main story is a win
- **THEN** the feature shows both crests and the score inside the card at every width

### Requirement: Managers page checked
Every new control SHALL be registered in the layout check, and the page SHALL pass the layout, accessibility (WCAG 2.2 AA, 48 px touch targets, colour tokens) and copy checks at every tested width and engine.

#### Scenario: New tile control
- **WHEN** the change adds the manager picker arrows
- **THEN** they are listed in the layout check's control registry and pass the touch-target check

### Requirement: Moves card
The Moves card SHALL show, for the chosen season or all seasons, a FAAB meter (spent of budget, biggest bid, overpaid total), then Added, Dropped and Trades lists, then the Players block (most seasons on this team, the one that got away). A season picker with arrows SHALL offer each season and "All seasons". A filter SHALL offer All moves, Waivers, Free agents and Trades.

#### Scenario: Season shown
- **WHEN** a manager's 2026 moves are shown
- **THEN** the FAAB meter, the Added, Dropped and Trades lists and the Players block show that season's figures

#### Scenario: Filter
- **WHEN** the visitor chooses Trades
- **THEN** only the Trades list shows

### Requirement: Move rows
Each added or dropped row SHALL show the player's name (following the player name standard), how the move happened and its week on a second line, and a WAR chip in the roster card's colours, or "no games" ("no games yet" while nothing after the move is scored). A won waiver row SHALL show its bid and its overpay as a red "+$29" tag, whose tooltip says whether it was against the next bid or no other bids; a tie SHALL read "tied".

#### Scenario: Overpay tag
- **WHEN** Rico Dowdle was won for $41 against a next bid of $12
- **THEN** his row reads "Waiver · $41 +$29 · week 3" with the tag in red

#### Scenario: Never played
- **WHEN** a dropped player had no game while away from the team
- **THEN** his chip reads "no games"

### Requirement: Moves list headers
Each Moves list header SHALL give its count; Added SHALL also give its FAAB spent and total WAR, and Dropped its WAR elsewhere.

#### Scenario: Added header
- **WHEN** a manager added five players for $75 worth +1.5 WAR in total
- **THEN** the header reads "Added (5)" with "$75 · +1.5 WAR"

### Requirement: Moves text never cut
On the Moves card, a row's second line SHALL wrap rather than be cut, and a player name too wide for its space even when shortened SHALL wrap to a second line, at every tested width and with wide system fonts.

#### Scenario: All seasons on a narrow card
- **WHEN** "Claimed by Gixxersean1 · week 17, 2024" is wider than the desktop card
- **THEN** it wraps onto a second line

#### Scenario: Long name in a trade
- **WHEN** "C. Edwards-Helaire" is still wider than its trade column
- **THEN** the name wraps instead of ending in an ellipsis

### Requirement: Trade blocks
Each trade SHALL be one block naming the other manager (linked to their page) and the week, with Got and Gave sides. Players SHALL show with their WAR chips; picks SHALL show as season and round ("2027 2nd") and FAAB as "$5 FAAB", without WAR.

#### Scenario: Trade with a pick
- **WHEN** a trade sent T. Etienne Jr. for J. Smith-Njigba and a 2027 2nd
- **THEN** the block shows Got: J. Smith-Njigba with his chip and "2027 2nd"; Gave: T. Etienne Jr. with his chip
