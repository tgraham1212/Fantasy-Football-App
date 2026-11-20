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
Every tile SHALL share one layout: a fixed first line holding a 32 px image or a large number, then a detail line, so images and numbers line up across the bar. The Last Result score SHALL never wrap and both crests SHALL stay inside the tile, the score shrinking first. Each tile SHALL link to the page its number comes from. On phones the tiles SHALL form two columns, the seventh spanning both.

#### Scenario: Narrow tile
- **WHEN** the Last Result tile is at its narrowest
- **THEN** the score text shrinks and both crests stay inside the tile

### Requirement: Long names on tiles and cards
Player names on the tiles and cards SHALL show the first initial and last name ("A. St. Brown") with the full name as a tooltip, and SHALL fit without being cut at every tested width.

#### Scenario: Longest name on a phone
- **WHEN** Jaxon Smith-Njigba is the top scorer on a 360 px phone
- **THEN** the tile shows "J. Smith-Njigba" in full

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

### Requirement: Moves card placeholder
Until transactions are synced, the Moves card SHALL keep its final layout: season picker with arrows, filter, a FAAB meter (spent of budget, biggest bid), skeleton rows where the added and dropped lists go with one line saying they are coming, and a live Players block (most seasons on this team, the one that got away).

#### Scenario: Before the transactions sync
- **WHEN** the Moves card is shown in this change
- **THEN** the FAAB meter and Players block show real figures and the lists show skeleton rows

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
