# Spec Delta

## MODIFIED Requirements

### Requirement: League pages
The site SHALL have a page for each configured league that shows that league's current season. Visitors SHALL be able to switch between leagues. Each league page SHALL have five sub-tabs in this order: "Forecasts" (the forecast table and charts), "Games", "Positions", "Managers" and "Player WAR". The selected sub-tab SHALL be kept in the page URL, so a link opens on that sub-tab, and SHALL be kept when switching league.

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
- **WHEN** a visitor picks "Positions", which sits between "Games" and "Managers"
- **THEN** the league's Positional Rankings page is shown and the URL identifies the league and the Positions sub-tab

#### Scenario: Open the Managers sub-tab
- **WHEN** a visitor picks "Managers", which sits between "Positions" and "Player WAR"
- **THEN** the league's Managers page is shown and the URL identifies the league, the Managers sub-tab and the manager
