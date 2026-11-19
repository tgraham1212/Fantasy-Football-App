## MODIFIED Requirements

### Requirement: League pages
The site SHALL have a page for each configured league that shows that league's current season. Visitors SHALL be able to switch between leagues. Each league page SHALL have four sub-tabs in this order: "Forecasts" (the forecast table and charts), "Games", "Positions" and "Player WAR". The selected sub-tab SHALL be kept in the page URL, so a link opens on that sub-tab, and SHALL be kept when switching league.

#### Scenario: Switch league
- **WHEN** a visitor on the dynasty page picks the redraft league
- **THEN** the redraft league's forecasts are shown

#### Scenario: Open the WAR sub-tab
- **WHEN** a visitor on the redraft Forecasts sub-tab picks "Player WAR"
- **THEN** the redraft Player WAR page is shown and the URL identifies both the league and the sub-tab

#### Scenario: Link to a sub-tab
- **WHEN** a visitor opens a link whose URL names the dynasty league and the Player WAR sub-tab
- **THEN** the page opens on the dynasty Player WAR page

#### Scenario: Open the Games sub-tab
- **WHEN** a visitor picks "Games", which sits between "Forecasts" and "Positions"
- **THEN** the league's Games page is shown and the URL identifies the league and the Games sub-tab

#### Scenario: Open the Positions sub-tab
- **WHEN** a visitor picks "Positions", which sits between "Games" and "Player WAR"
- **THEN** the league's Positional Rankings page is shown and the URL identifies the league and the Positions sub-tab

### Requirement: Grouped chance headers
The four chance columns SHALL sit under a single "Playoff Forecast" group header, and every column header SHALL use small uppercase labels that wrap to two lines where needed.

#### Scenario: Header layout
- **WHEN** a visitor views the table on a desktop-width screen
- **THEN** a "Playoff Forecast" label spans exactly the four chance columns, above their individual headers

### Requirement: Live odds on the Predictions page
While a week is live, the Forecasts table SHALL show the live result's forecasts, labelled with how many of the week's NFL games are final, and its change tooltips SHALL compare with the as-of result the live run started from. The forecast-over-time chart SHALL keep plotting only stored as-of results.

#### Scenario: Saturday of week 11
- **WHEN** a visitor opens the Forecasts page on Saturday of week 11
- **THEN** the table shows the live forecasts labelled "Live: 1 of 14 games final" and the chart's last point is still as of week 10

### Requirement: Calibration page
The site SHALL have a calibration page, reachable from every league page, titled "How Good Are These Forecasts?", that shows how well past forecasts matched real outcomes: for each season outcome, forecast percentage against observed rate with the number of cases behind each point; observed against nominal coverage of the score intervals; the Brier skill against the baseline; the lineup gap per league; when the calibration was produced, how many seasons it covers and the residual scale used; and the known caveats.

#### Scenario: Visitor checks the odds
- **WHEN** a visitor opens the calibration page after a calibration report has been published
- **THEN** they can see, for the playoff forecast, how often teams shown at each forecast level actually made the playoffs

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
