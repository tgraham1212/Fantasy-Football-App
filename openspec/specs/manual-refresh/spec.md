# manual-refresh Specification

## Purpose

Lets Managers start a data refresh from the site through the refresh relay, which holds the GitHub credential and limits how often a refresh can start. It serves need 5, Current Data, under need 12, Secure Operation; how it fits with the scheduled runs is in `docs/refresh-modes.md`.

## Requirements

### Requirement: 5.4 Refresh relay
The refresh relay SHALL accept refresh requests from the published site only.

**Traces to:** 5; 12
**Verified by:** Test: `tests/test_relay.py::test_other_origins_refused`

#### Scenario: Request from elsewhere
- **WHEN** a request comes from another origin
- **THEN** the relay refuses it without starting anything

### Requirement: 5.4.1 Relay credential
The relay SHALL start the refresh workflows with a credential limited to running this repository's workflows, held as a relay secret outside the repository and the site.

**Traces to:** 5.4; 12
**Verified by:** Inspection: `relay/README.md` and the relay's secrets, the token's scope and that no token is in the repository or `site/`

#### Scenario: Searching the repository
- **WHEN** someone searches the repository and the published site for the token
- **THEN** it is in neither

### Requirement: 5.4.2 What a refresh starts
A refresh request SHALL start a hot run and a cold run in Quiet, and a cold run in the off-season.

**Traces to:** 5.4; 5.1
**Verified by:** Test: `tests/test_relay.py::test_button_refresh_and_hold`

#### Scenario: Request from the site
- **WHEN** a visitor on the published site requests a refresh in Quiet and none is held
- **THEN** the relay starts a hot run and a cold run and answers that a refresh started

### Requirement: 5.4.3 Refresh held
The relay SHALL refuse a refresh in Live, while a hot run is queued or running, and within 5 minutes of the last refresh it started from the button, answering with the reason and the minutes until one is available.

**Traces to:** 5.4; 11
**Verified by:** Test: `tests/test_relay.py::test_button_refused_in_live`; Test: `tests/test_relay.py::test_button_held_while_a_hot_run_is_going`

#### Scenario: Too soon
- **WHEN** the last button refresh started 2 minutes ago in Quiet and its hot run has finished
- **THEN** the relay refuses and answers that a refresh is available in 3 minutes

### Requirement: 5.4.3.1 Button refreshes start the hold
Only a refresh the button successfully started SHALL start the 5-minute hold.

**Traces to:** 5.4.3
**Verified by:** Test: `tests/test_relay.py::test_button_refresh_and_hold`; Test: `tests/test_relay.py::test_failed_dispatch_does_not_hold`

#### Scenario: Failed dispatch
- **WHEN** GitHub refuses the relay's request to start the runs
- **THEN** the button is not held

### Requirement: 5.4.3.2 Two clicks at once
Requests arriving together SHALL start one refresh, the others refused with the time until one is available.

**Traces to:** 5.4.3
**Verified by:** Test: `tests/test_relay.py::test_two_clicks_start_one_refresh`

#### Scenario: Two clicks at once
- **WHEN** two visitors request a refresh a few seconds apart
- **THEN** one refresh starts and the second request is refused with the time until available

### Requirement: 5.4.4 Refresh button
Each page SHALL show a "Refresh Data" button in the header, aligned with the other header buttons and on one line, when the relay's address is configured.

**Traces to:** 5.4; 9
**Verified by:** Test: `tests/layout/test_layout.py::test_refresh_note_by_relay_status`; Test: `tests/test_export.py::test_index_carries_the_refresh_url_and_last_refresh`

#### Scenario: Not configured
- **WHEN** the site is published without a relay address
- **THEN** no refresh button appears and every page works as before

### Requirement: 5.4.4.1 Refresh note
Under the button, beside it on phones, the page SHALL show, updated every minute: "Updated N min ago" while a refresh is available, "Available in N min" while held, "Live updates on" in Live with the button disabled, and a short confirmation once a refresh starts.

**Traces to:** 5.4.4
**Verified by:** Test: `tests/layout/test_layout.py::test_refresh_note_by_relay_status`; Test: `tests/layout/test_layout.py::test_started_refresh_says_back_in_a_minute`

#### Scenario: Held
- **WHEN** the last button refresh started 2 minutes ago
- **THEN** the button is disabled with "Available in 3 min" under it

#### Scenario: Started
- **WHEN** a visitor clicks "Refresh Data" in Quiet and the relay starts the runs
- **THEN** the note says "Started, back in ~1 min" with the full explanation as its tooltip

### Requirement: 5.4.4.2 Note keeps its space
The refresh note SHALL keep a fixed space within the screen, so that no message moves the button or any other element, with any longer explanation as its tooltip.

**Traces to:** 5.4.4; 5.4.4.1; 9.2
**Verified by:** Test: `tests/layout/test_layout.py::test_control_keeps_the_layout`

#### Scenario: Aligned
- **WHEN** the header shows the button with its note
- **THEN** the button lines up with the league buttons and the note stays within the screen at every tested width

### Requirement: 5.4.4.3 Refresh that never lands
If no new data has arrived 10 minutes after a refresh the visitor started, the note SHALL say the refresh did not finish.

**Traces to:** 5.4.4; 5.4.4.1
**Verified by:** Inspection: `site/refresh.js`, the 10-minute give-up timer and its message

#### Scenario: Run never lands
- **WHEN** 10 minutes pass after a started refresh with no new data
- **THEN** the note says the refresh did not finish
