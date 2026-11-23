# site-updates Specification

## Purpose

Keeps an open page current without a manual reload: it swaps in newer data while keeping the visitor's place, and tells the visitor when newer site code is live.

## Requirements

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

### Requirement: In-place data swap
When the deployed data is newer and the site code is unchanged, the page SHALL replace its data and redraw the open view without reloading, keeping the selected league, page, Games week, each game card's Model or Actual view, open full lineups, table sort, highlighted team, and an open full list overlay with its sort. The refresh note SHALL then read "Updated just now". This SHALL apply to refreshes the visitor started and to scheduled refreshes alike.

#### Scenario: Live week update
- **WHEN** a scheduled refresh deploys during a live week while a visitor views week 11 with one card on Model and its lineups open
- **THEN** the cards show the new scores and probabilities, week 11 is still selected, that card is still on Model and its lineups are still open

#### Scenario: Full list open
- **WHEN** new data arrives while the RB full list is open sorted by points scored
- **THEN** the overlay stays open, sorted by points scored, with the new numbers

#### Scenario: A week that no longer exists
- **WHEN** the new data no longer has the selected week
- **THEN** the page shows its default week as on a fresh load

### Requirement: New version note
When the deployed site code differs from the page's code, the page SHALL show a note pinned to the bottom of the screen saying a new version is available, with a Refresh button that reloads the page, and SHALL NOT swap in new data. The note SHALL stay until the page reloads and SHALL NOT move any other element.

#### Scenario: Code pushed
- **WHEN** a new version of the site deploys while a visitor has the page open
- **THEN** within about a minute of the tab being visible the note appears and stays until the visitor reloads

#### Scenario: Reload
- **WHEN** the visitor clicks Refresh in the note
- **THEN** the page reloads on the same league, page and Games week with the new code and data

### Requirement: Place kept across reloads
The page's address SHALL carry the league, page and Games week, so a reload or a shared link opens the same view.

#### Scenario: Shared link
- **WHEN** a visitor opens a link to the Taco Tuesdays Games page at week 9
- **THEN** the page opens on Taco Tuesdays, Games, week 9

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
