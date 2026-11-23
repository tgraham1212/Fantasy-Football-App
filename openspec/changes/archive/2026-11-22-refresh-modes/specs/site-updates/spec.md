## MODIFIED Requirements

### Requirement: Update check
While a page of the published site is visible, it SHALL check whether the deployed data, the live bundle or the site code is newer than what it shows:
- every 30 seconds in Live;
- once a minute otherwise.

It SHALL make no checks while the tab is hidden, and SHALL check once when the tab becomes visible again. A page served without a code fingerprint (a local copy) SHALL check for data only and SHALL NOT read the live bundle.

#### Scenario: Visible tab
- **WHEN** a visitor keeps the Games page open and visible for five minutes in Quiet
- **THEN** the page has checked for updates about five times

#### Scenario: Hidden tab
- **WHEN** the tab is in the background for an hour and then shown
- **THEN** the page made no checks while hidden and checks once when shown

#### Scenario: Live checks
- **WHEN** a visitor keeps the Games page open for five minutes during Live
- **THEN** the page has checked about ten times

## ADDED Requirements

### Requirement: Live bundle swap
When the live bundle is newer than the data the page shows, and the site code is unchanged, the page SHALL use the bundle's forecast and this week's game cards in place of the static files. It SHALL redraw in place exactly as for newer deployed data, keeping the visitor's place.

#### Scenario: Hot run lands
- **WHEN** a hot run writes a bundle while a visitor views week 11 with a card on Model
- **THEN** within 30 seconds the cards show the new scores, week 11 and the Model view are kept, and the note reads "Updated just now"

### Requirement: Older or missing bundle
The page SHALL ignore a bundle older than the deployed static files, and SHALL keep what it shows when the relay cannot be reached. The "Updated" time SHALL be the newer of the bundle's time and the static files' refresh time.

#### Scenario: Cold deploy after the bundle
- **WHEN** a cold run deploys static files newer than the latest bundle
- **THEN** the page shows the static files and ignores the older bundle

#### Scenario: Relay down
- **WHEN** the relay does not answer during Live
- **THEN** the page keeps showing the last bundle or static files without an error
