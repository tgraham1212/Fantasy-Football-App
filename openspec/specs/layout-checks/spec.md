# layout-checks Specification

## Purpose

Catches layout faults before they ship: every page is loaded in a real browser at phone, tablet and desktop widths and every control is driven through its states.

## Requirements

### Requirement: Layout check
A browser test SHALL load each page of the site at widths of 375, 440, 768, 1000 and 1280 px (440 standing for current large phones) and SHALL fail when the page scrolls sideways at any width, naming the page and width.

#### Scenario: Overflowing note
- **WHEN** a message under a button runs past the right edge at 1000 px
- **THEN** the layout check fails naming the page and the width

#### Scenario: Large phone width
- **WHEN** a Games card is cramped side by side at 440 px
- **THEN** the layout check fails at 440 px

### Requirement: Controls keep the layout
For every control on every page, the layout check SHALL drive the control through each of its states and SHALL fail when an element outside the control's declared effect moves or changes size, naming the control, state, element and width. A control's declared effect SHALL list what it is designed to change (for example, an expander may move what sits below it). External services SHALL be simulated so the check starts no refresh.

#### Scenario: Refresh started
- **WHEN** the refresh button is clicked and the simulated relay answers that a refresh started
- **THEN** the header, the page tabs and the button itself keep their positions and sizes at every width

#### Scenario: Designed movement
- **WHEN** "Full Lineup" opens on a game card
- **THEN** the cards below may move and the check passes

#### Scenario: Squeezed button
- **WHEN** a state change makes a button's label wrap onto two lines
- **THEN** the check fails naming the button and the width

### Requirement: Every control covered
Every button, toggle, selector and expander the site adds SHALL be listed in the layout check with its states and declared effect, and the check SHALL fail when a page has a control it does not list.

#### Scenario: New button
- **WHEN** a change adds a button and does not add it to the layout check
- **THEN** the layout check fails naming the unlisted button

### Requirement: Runs on code changes only
The layout check SHALL run when site code is pushed and before that code deploys, and SHALL NOT run in or block the data refresh. When no browser is available locally it SHALL be skipped with a message rather than fail.

#### Scenario: Data refresh
- **WHEN** the hourly refresh runs
- **THEN** the layout check does not run and cannot stop the refresh

#### Scenario: Failing layout on push
- **WHEN** a push changes site code and the layout check fails
- **THEN** that push does not deploy and the failure names the control and width
