# manual-refresh Specification

## Purpose

Lets league members start a data refresh from the site through a small relay that holds the GitHub credential and limits how often a refresh can start.

## Requirements

### Requirement: Refresh relay
A relay service SHALL accept refresh requests from the published site only, and SHALL start the repository's refresh workflow in manual mode using a credential limited to running that repository's workflows. The credential SHALL never appear in the repository or the site.

#### Scenario: Request from the site
- **WHEN** a visitor on the published site requests a refresh and none is held
- **THEN** the relay starts the refresh workflow and answers that a refresh started

#### Scenario: Request from elsewhere
- **WHEN** a request comes from another origin
- **THEN** the relay refuses it without starting anything

### Requirement: Refresh cooldown
The relay SHALL refuse to start a refresh within 15 minutes of the start of the last refresh run, scheduled or manual, including a run still queued or in progress, and SHALL answer with the minutes until a refresh is available. Hourly checks that did not refresh SHALL NOT count.

#### Scenario: Too soon
- **WHEN** the last refresh started 6 minutes ago
- **THEN** the relay refuses and answers that a refresh is available in 9 minutes

#### Scenario: Two clicks at once
- **WHEN** two visitors request a refresh a few seconds apart
- **THEN** one refresh starts and the second request is refused with the time until available

### Requirement: Refresh button
Each page SHALL show a "Refresh Data" button beside "How good are these odds?" when the relay's address is configured, and no button otherwise, aligned with the other header buttons. Its label SHALL never wrap. Under it (beside it on phones) the page SHALL show "Updated N min ago" while a refresh is available and "Available in N min" while it is held, updating every minute, and a short confirmation after a refresh starts. The note SHALL keep a fixed space so no message moves the button or any other element, SHALL stay within the screen, and SHALL show any longer explanation as a tooltip. After a refresh the visitor started, the note SHALL say "Updated just now" when the new data arrives, or that the refresh did not finish if no new data has arrived after 20 minutes.

#### Scenario: Not configured
- **WHEN** the site is published without a relay address
- **THEN** no refresh button appears and every page works as before

#### Scenario: Held
- **WHEN** the last refresh started 6 minutes ago
- **THEN** the button is disabled with "Available in 9 min" under it

#### Scenario: Started
- **WHEN** a visitor clicks "Refresh Data" and the relay starts a run
- **THEN** the note says "Started, back in ~5 min" with the full explanation as its tooltip, and nothing on the page moves

#### Scenario: Data arrives
- **WHEN** the started run deploys new data four minutes later
- **THEN** the page shows the new data in place and the note reads "Updated just now"

#### Scenario: Run never lands
- **WHEN** 20 minutes pass after a started refresh with no new data deployed
- **THEN** the note says the refresh did not finish

#### Scenario: Aligned
- **WHEN** the header shows the button with its note
- **THEN** the button lines up with the league and calibration buttons and the note hangs below it within the screen at every width
