## MODIFIED Requirements

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

### Requirement: Usable on phones
League pages SHALL be readable on a 375px-wide screen without horizontal page scrolling. The odds table MAY scroll horizontally inside its own container. When the sub-tabs do not fit the screen width, the sub-tab menu SHALL scroll sideways inside its own strip with a swipe:

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
