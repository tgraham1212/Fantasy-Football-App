# layout-checks Specification

## Purpose

Catches layout faults before they ship: every page is loaded in a real browser at phone, tablet and desktop widths and every control is driven through its states.

## Requirements

### Requirement: Layout check
A browser test SHALL load each page of the site in three browser engines and SHALL fail when the page scrolls sideways at any width, naming the page, engine and width:
- **Chromium** (Chrome and Edge) at widths of 360, 390, 414, 440, 768, 1000 and 1280 px;
- **WebKit** (Safari's engine) and **Firefox** at least at 390, 440 and 1280 px.

The phone widths SHALL follow the most common US mobile screen widths reported by StatCounter. They SHALL be reviewed at least once a year and whenever a new phone size enters the top six.

#### Scenario: Overflowing note
- **WHEN** a message under a button runs past the right edge at 1000 px
- **THEN** the layout check fails naming the page and the width

#### Scenario: Large phone width
- **WHEN** a Games card is cramped side by side at 440 px
- **THEN** the layout check fails at 440 px

#### Scenario: Safari-only fault
- **WHEN** a pinned table column works in Chromium but drifts in WebKit at 390 px
- **THEN** the layout check fails naming WebKit and 390 px

#### Scenario: Most common phone
- **WHEN** a layout breaks only at 414 px, the most common US mobile width
- **THEN** the layout check fails at 414 px

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

### Requirement: Accessibility check
A browser test SHALL run the axe-core accessibility engine with its WCAG 2.2 A and AA rules on every page and its main views, in Chromium at a phone and a desktop width. It SHALL fail on any violation not listed in a committed baseline, naming the rule, the page and the element. A listed violation that no longer occurs SHALL also fail the test until it is removed from the baseline, so the baseline only shrinks.

#### Scenario: New contrast problem
- **WHEN** a change adds grey text that fails the AA contrast ratio
- **THEN** the accessibility check fails naming the color-contrast rule, the page and the element

#### Scenario: Fixed finding
- **WHEN** a follow-up change fixes a baselined violation
- **THEN** the check fails until that entry is removed from the baseline

### Requirement: Touch targets
A browser test SHALL measure every visible interactive control at the phone widths. It SHALL fail when a control is smaller than 48 × 48 px (Material Design 3's touch target), counting the control's own box plus any padding that responds to taps, unless the control is listed in a committed baseline. The baseline SHALL only shrink.

#### Scenario: Small new button
- **WHEN** a change adds a 30 px-tall button on the Games page
- **THEN** the touch-target check fails naming the button and its size
