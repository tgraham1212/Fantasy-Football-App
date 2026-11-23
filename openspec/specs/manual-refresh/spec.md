# manual-refresh Specification

## Purpose

Lets league members start a data refresh from the site through a small relay that holds the GitHub credential and limits how often a refresh can start.

## Requirements

### Requirement: Refresh relay
A relay service SHALL accept refresh requests from the published site only. It SHALL start the repository's refresh workflows using a credential limited to running that repository's workflows. The credential SHALL never appear in the repository or the site.

The relay SHALL also run the refresh clock and serve the live bundle (see `refresh-scheduling` and `live-refresh`). A refresh request SHALL start:
- in Quiet, a hot run and a cold run;
- in the off-season, a cold run.

#### Scenario: Request from the site
- **WHEN** a visitor on the published site requests a refresh in Quiet and none is held
- **THEN** the relay starts a hot run and a cold run and answers that a refresh started

#### Scenario: Request from elsewhere
- **WHEN** a request comes from another origin
- **THEN** the relay refuses it without starting anything

### Requirement: Refresh cooldown
The relay SHALL refuse a refresh in Live, and otherwise:
- while a hot run is queued or in progress;
- within 5 minutes of the last refresh it started from the button.

It SHALL answer with the reason and the minutes until a refresh is available. Scheduled runs SHALL NOT start the 5-minute hold.

#### Scenario: Too soon
- **WHEN** the last button refresh started 2 minutes ago in Quiet and its hot run has finished
- **THEN** the relay refuses and answers that a refresh is available in 3 minutes

#### Scenario: Two clicks at once
- **WHEN** two visitors request a refresh a few seconds apart
- **THEN** one refresh starts and the second request is refused with the time until available

### Requirement: Refresh button
Each page SHALL show a "Refresh Data" button in the header when the relay's address is configured, and no button otherwise, aligned with the other header buttons. Its label SHALL never wrap.

Under the button (beside it on phones) the page SHALL show, updating every minute:
- "Updated N min ago" while a refresh is available;
- "Available in N min" while it is held;
- "Live updates on" in Live, with the button disabled;
- a short confirmation after a refresh starts.

The note SHALL:
- keep a fixed space, so no message moves the button or any other element;
- stay within the screen;
- show any longer explanation as a tooltip.

After a refresh the visitor started, the note SHALL say "Updated just now" when the new data arrives. It SHALL say the refresh did not finish if no new data has arrived after 10 minutes.

#### Scenario: Not configured
- **WHEN** the site is published without a relay address
- **THEN** no refresh button appears and every page works as before

#### Scenario: Held
- **WHEN** the last button refresh started 2 minutes ago
- **THEN** the button is disabled with "Available in 3 min" under it

#### Scenario: Live
- **WHEN** a game is in progress
- **THEN** the button is disabled with "Live updates on" under it and the full explanation as its tooltip

#### Scenario: Started
- **WHEN** a visitor clicks "Refresh Data" in Quiet and the relay starts the runs
- **THEN** the note says "Started, back in ~1 min" with the full explanation as its tooltip, and nothing on the page moves

#### Scenario: Data arrives
- **WHEN** the started hot run writes its bundle a minute later
- **THEN** the page shows the new data in place and the note reads "Updated just now"

#### Scenario: Run never lands
- **WHEN** 10 minutes pass after a started refresh with no new data
- **THEN** the note says the refresh did not finish

#### Scenario: Aligned
- **WHEN** the header shows the button with its note
- **THEN** the button lines up with the league buttons and the note hangs below it within the screen at every width
