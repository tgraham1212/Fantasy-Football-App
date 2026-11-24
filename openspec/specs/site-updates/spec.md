# site-updates Specification

## Purpose

Keeps an open page current without a manual reload: it checks for newer data, swaps it in while keeping the visitor's place, and says when newer site code is live; and every deploy stamps the site's scripts so browsers fetch new code. It delivers need 5, Current Data, on the page; how it fits with the runs is in `docs/refresh-modes.md`.

## Requirements

### Requirement: 5.3 Update check
While a page is visible, it SHALL check whether the deployed data, the live bundle or the site code is newer than what it shows, every 30 seconds while a game is in progress and once a minute otherwise.

**Traces to:** 5
**Verified by:** Test: `tests/layout/test_update_check.py::test_checks_once_a_minute_while_quiet`; Test: `tests/layout/test_update_check.py::test_checks_every_thirty_seconds_while_live`

#### Scenario: Visible tab
- **WHEN** a visitor keeps the Games page open and visible for five minutes in Quiet
- **THEN** the page checks five times (±1)

#### Scenario: Live checks
- **WHEN** a visitor keeps the Games page open for five minutes during Live
- **THEN** the page checks ten times (±1)

### Requirement: 5.3.1 Hidden tab
A page SHALL make no checks while its tab is hidden, and check once when the tab is shown again.

**Rationale:** A background tab should not spend the relay's or the visitor's resources.
**Traces to:** 5.3; 11
**Verified by:** Test: `tests/layout/test_update_check.py::test_no_checks_while_hidden_and_one_when_shown`

#### Scenario: Hidden tab
- **WHEN** the tab is in the background for an hour and then shown
- **THEN** the page made no checks while hidden and checks once when shown

### Requirement: 5.3.2 Local copy
A page served without a code fingerprint SHALL check the deployed data only, without reading the live bundle.

**Traces to:** 5.3
**Verified by:** Inspection: `site/updates.js`, an unstamped page skips the version and bundle checks

#### Scenario: Local server
- **WHEN** the site is served from the repository checkout
- **THEN** the page checks `data/index.json` only

### Requirement: 5.3.3 In-place data swap
When newer deployed data arrives under unchanged site code, the page SHALL redraw the open view in place, keeping the league, sub-tab, Games week, each card's view, open full lineups, table sort, highlighted team, and an open full list with its sort.

**Traces to:** 5.3; 9
**Verified by:** Test: `tests/layout/test_layout.py::test_data_swap_keeps_the_visitors_place`; Test: `tests/layout/test_layout.py::test_positions_data_swap_keeps_the_season`

#### Scenario: Live week update
- **WHEN** a cold run deploys while a visitor views week 11 with one card on Model and its lineups open
- **THEN** the cards show the new scores, week 11 is still selected, and that card is still on Model with its lineups open

### Requirement: 5.3.3.1 Updated note after a swap
After any data swap, scheduled or started by the visitor, the refresh note SHALL read "Updated just now".

**Traces to:** 5.3.3; 5.4.4
**Verified by:** Test: `tests/layout/test_layout.py::test_data_swap_keeps_the_visitors_place`

#### Scenario: Scheduled refresh lands
- **WHEN** a scheduled cold run's data is swapped in
- **THEN** the note reads "Updated just now"

### Requirement: 5.3.3.2 Week gone from the new data
When the new data no longer has the selected week, the page SHALL show its default week, as on a fresh load.

**Traces to:** 5.3.3
**Verified by:** Inspection: `site/games.js`, a missing week falls back to the index's current week

#### Scenario: A week that no longer exists
- **WHEN** the new data no longer has the selected week
- **THEN** the page shows its default week

### Requirement: 5.3.4 Live bundle swap
When the live bundle is newer than the data the page shows, under unchanged site code, the page SHALL use the bundle's Forecasts and this week's game cards in place of the static files, redrawing in place as for newer deployed data.

**Traces to:** 5.3; 5.3.3
**Verified by:** Test: `tests/layout/test_layout.py::test_live_bundle_swap_keeps_the_visitors_place`

#### Scenario: Hot run lands
- **WHEN** a hot run writes a bundle while a visitor views week 11 with a card on Model
- **THEN** within 30 seconds the cards show the new scores, week 11 and the Model view are kept, and the note reads "Updated just now"

### Requirement: 5.3.4.1 Older bundle or relay down
The page SHALL ignore a bundle older than the deployed static files, and keep what it shows when the relay cannot be reached.

**Traces to:** 5.3.4; 11.1.1
**Verified by:** Test: `tests/layout/test_layout.py::test_older_bundle_and_relay_down_are_ignored`

#### Scenario: Cold deploy after the bundle
- **WHEN** a cold run deploys static files newer than the latest bundle
- **THEN** the page shows the static files and ignores the older bundle

#### Scenario: Relay down
- **WHEN** the relay does not answer during Live
- **THEN** the page keeps showing the last bundle or static files without an error

### Requirement: 5.3.4.2 Updated time
The page's "Updated" time SHALL be the newer of the bundle's time and the static files' refresh time.

**Traces to:** 5.3.4; 1.3.12
**Verified by:** Test: `tests/test_build_last_refresh.py::test_last_commit_time_is_the_commit_in_utc`; Inspection: `site/updates.js`, the time given to the refresh note is the newer of the two

#### Scenario: Bundle newer
- **WHEN** the bundle was written at 2:05 pm and the static files at 1:50 pm
- **THEN** the page says it was updated at 2:05 pm

### Requirement: 5.3.5 New version note
When the deployed site code differs from the page's, the page SHALL pin a note to the bottom of the screen saying a new version is available, with a Refresh button that reloads it, and stop swapping in data until then.

**Rationale:** New data is never drawn by old code.
**Traces to:** 5.3; 10
**Verified by:** Test: `tests/layout/test_layout.py::test_control_keeps_the_layout`; Inspection: the live site, the note and its Refresh button after a code deploy

#### Scenario: Code pushed
- **WHEN** a new version of the site deploys while a visitor has the page open
- **THEN** within a minute of the tab being visible the note appears and stays until the visitor reloads

### Requirement: 5.3.5.1 Note moves nothing
The new version note SHALL leave every other element where it was.

**Traces to:** 5.3.5
**Verified by:** Test: `tests/layout/test_layout.py::test_control_keeps_the_layout`

#### Scenario: Note appears
- **WHEN** the note appears at 360 px
- **THEN** no other element moves

### Requirement: 5.3.6 Place kept across reloads
The page URL SHALL also carry the Games week, so that a reload or a shared link opens the same week.

**Traces to:** 5.3; 9.1.1.1
**Verified by:** Test: `tests/layout/test_layout.py::test_data_swap_keeps_the_visitors_place`

#### Scenario: Shared link
- **WHEN** a visitor opens a link to the Taco Tuesdays Games sub-tab at week 9
- **THEN** the page opens on Taco Tuesdays, Games, week 9

### Requirement: 5.3.7 Stamped scripts
Every script and stylesheet the pages load, and every import between scripts, SHALL carry in its URL a stamp that each deploy replaces with a fingerprint of the site's code files.

**Rationale:** Browsers then fetch new code after a code deploy instead of a cached copy.
**Traces to:** 5.3; 5.3.5
**Verified by:** Test: `tests/test_site_files.py::test_every_script_reference_carries_the_build_placeholder`; Test: `tests/test_site_files.py::test_stylesheets_carry_the_placeholder`

#### Scenario: New deploy
- **WHEN** a visitor whose browser cached the previous scripts opens the site after a deploy that changed site code
- **THEN** the page references the new stamp and the browser fetches the new files

### Requirement: 5.3.7.1 Fingerprint of code only
The fingerprint SHALL depend only on the content of the pages, scripts, stylesheet and bundled libraries, never the data files.

**Traces to:** 5.3.7
**Verified by:** Test: `tests/test_site_files.py::test_fingerprint_ignores_data_and_line_endings`; Test: `tests/test_site_files.py::test_fingerprint_changes_with_code`

#### Scenario: Data-only deploy
- **WHEN** a cold run deploys new data and no site code changed
- **THEN** the stamp is the same as the previous deploy's and browsers reuse their cached scripts

### Requirement: 5.3.7.2 One stamping command
Every deploying workflow SHALL produce the stamp and the version file with the shared `python -m ffapp stamp-site` command before the upload.

**Traces to:** 5.3.7
**Verified by:** Test: `tests/test_site_files.py::test_every_deploy_stamps_through_the_shared_command`

#### Scenario: Deploy without the stamping command
- **WHEN** a workflow that deploys the site does not run the stamping command before the upload
- **THEN** the test suite fails naming the workflow

### Requirement: 5.3.7.3 Version file
Every deploy SHALL publish the fingerprint in `version.json` beside the pages.

**Traces to:** 5.3.7; 5.3.5
**Verified by:** Test: `tests/test_site_files.py::test_stamp_site_writes_the_fingerprint_everywhere`

#### Scenario: After a deploy
- **WHEN** the site is deployed
- **THEN** `version.json` holds the same fingerprint as the stamped URLs

### Requirement: 5.3.7.4 Placeholder in the source
The source files SHALL carry a placeholder in place of the stamp, so that the site runs unchanged from a local server.

**Traces to:** 5.3.7
**Verified by:** Test: `tests/test_site_files.py::test_every_script_reference_carries_the_build_placeholder`; Test: `tests/test_site_files.py::test_a_stripped_reference_is_reported`

#### Scenario: Reference without a stamp
- **WHEN** a script or stylesheet reference or module import lacks the placeholder
- **THEN** the test suite fails naming the file
