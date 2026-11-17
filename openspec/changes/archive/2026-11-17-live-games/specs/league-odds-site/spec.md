# Spec Delta

## ADDED Requirements

### Requirement: Live odds on the Predictions page
While a week is live, the Predictions table SHALL show the live result's chances, labelled with how many of the week's NFL games are final, and its change tooltips SHALL compare with the as-of result the live run started from. The odds-over-time chart SHALL keep plotting only stored as-of results.

#### Scenario: Saturday of week 11
- **WHEN** a visitor opens the Predictions page on Saturday of week 11
- **THEN** the table shows the live chances labelled "Live: 1 of 14 games final" and the chart's last point is still as of week 10

## MODIFIED Requirements

### Requirement: Static and public
The site SHALL be static files that need no server code, login or calls to Sleeper from the visitor's browser. Anyone with the link SHALL be able to view it. The optional refresh button MAY call the refresh relay; every page SHALL work fully when the relay is not configured or not reachable.

#### Scenario: Visitor loads page
- **WHEN** a visitor opens a league page
- **THEN** all data comes from files published with the site

#### Scenario: Relay down
- **WHEN** the refresh relay does not answer
- **THEN** the pages show their data as usual and the button reports that a refresh could not be started
