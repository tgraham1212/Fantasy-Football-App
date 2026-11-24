# layout-checks Specification

## Purpose

Catches layout and accessibility faults before they ship: every page is loaded in real browsers at phone, tablet and desktop widths, every control is driven through its states, and every page is checked against WCAG 2.2 AA and Material Design 3's touch targets. It verifies need 9, Usable by Every Manager.

## Requirements

### Requirement: 9.4 Layout check
A browser test SHALL load each page in Chromium at 360, 390, 414, 440, 768, 1000 and 1280 px, and in WebKit and Firefox at 440 and 1280 px, failing when a page scrolls sideways and naming the page, engine and width.

**Rationale:** Two widths for the other engines keep the code-push run under 20 minutes.
**Traces to:** 9; 9.5
**Verified by:** Test: `tests/layout/test_layout.py::test_wide_fonts_do_not_scroll_sideways`; Test: `tests/layout/test_layout.py::test_control_keeps_the_layout`

#### Scenario: Overflowing note
- **WHEN** a message under a button runs past the right edge at 1000 px
- **THEN** the layout check fails naming the page and the width

#### Scenario: Safari-only fault
- **WHEN** a pinned table column works in Chromium but drifts in WebKit at 440 px
- **THEN** the layout check fails naming WebKit and 440 px

### Requirement: 9.4.1 Controls keep the layout
For every control on every page, the layout check SHALL drive the control through each of its states and fail when an element outside the control's declared effect moves or changes size, naming the control, state, element and width.

**Traces to:** 9.4
**Verified by:** Test: `tests/layout/test_layout.py::test_control_keeps_the_layout`

#### Scenario: Designed movement
- **WHEN** "Full Lineup" opens on a game card
- **THEN** the cards below may move and the check passes

#### Scenario: Squeezed button
- **WHEN** a state change makes a button's label wrap onto two lines
- **THEN** the check fails naming the button and the width

### Requirement: 9.4.1.1 Services simulated
The layout check SHALL simulate the refresh relay, the version file and the data index, so that it starts no refresh.

**Traces to:** 9.4.1; 11
**Verified by:** Inspection: `tests/layout/conftest.py`, the simulated relay and the stamped local copy of the site

#### Scenario: Refresh started
- **WHEN** the check clicks the refresh button
- **THEN** the simulated relay answers and no workflow starts

### Requirement: 9.4.2 Every control covered
Every button, toggle, selector and expander on the site SHALL be listed in the layout check with its states and declared effect, an unlisted control failing the check.

**Traces to:** 9.4; 9.4.1
**Verified by:** Test: `tests/layout/test_layout.py::test_every_control_is_listed`

#### Scenario: New button
- **WHEN** a change adds a button and does not add it to the layout check
- **THEN** the layout check fails naming the unlisted button

### Requirement: 9.4.3 Runs on code pushes
The layout check SHALL run on every push of site code, before that code deploys, and never in the data refresh.

**Traces to:** 9.4; 5.6
**Verified by:** Test: `tests/test_workflows.py::test_cold_run_has_no_gate_or_test_suite_and_deploys_on_change`; Inspection: `.github/workflows/site.yml`, the tests run with `LAYOUT_REQUIRED` before the deploy

#### Scenario: Failing layout on push
- **WHEN** a push changes site code and the layout check fails
- **THEN** that push does not deploy and the failure names the control and width

### Requirement: 9.4.3.1 No browser locally
Without a browser on the machine, the layout check SHALL be skipped with a message, except where `LAYOUT_REQUIRED` is set, where it fails.

**Traces to:** 9.4.3
**Verified by:** Inspection: `tests/layout/conftest.py`, the skip and the `LAYOUT_REQUIRED` failure

#### Scenario: Laptop without Chrome
- **WHEN** the tests run on a machine without Chrome
- **THEN** the layout check is skipped with a message naming what to install

### Requirement: 9.4.4 Accessibility check
A browser test SHALL run axe-core's WCAG 2.2 A and AA rules on every page and its main views, in Chromium at a phone and a desktop width, in light and dark mode, failing on any violation not in a committed baseline and naming the rule, page, mode and element.

**Traces to:** 9.4; 9
**Verified by:** Test: `tests/layout/test_accessibility.py::test_accessibility_wcag_22_aa`

#### Scenario: Dark mode problem
- **WHEN** a button's label passes contrast in light mode but fails in dark mode
- **THEN** the accessibility check fails naming dark mode and the button

### Requirement: 9.4.4.1 Baselines only shrink
A baselined finding that no longer occurs SHALL fail its check until it is removed from the baseline.

**Traces to:** 9.4.4; 10
**Verified by:** Test: `tests/test_baselines.py::test_compare_both_ways`

#### Scenario: Fixed finding
- **WHEN** a follow-up change fixes a baselined violation
- **THEN** the check fails until that entry is removed from the baseline

### Requirement: 9.4.5 Touch targets
At the phone widths, a browser test SHALL probe a 48 × 48 px square, or the control's own box where larger, centred on every visible interactive control, failing when a probe point lands outside it or on a neighbour, unless the control is in a committed baseline.

**Traces to:** 9.4; 9.6
**Verified by:** Test: `tests/layout/test_accessibility.py::test_touch_targets_on_phones`

#### Scenario: Small new button
- **WHEN** a change adds a 30 px-tall button on the Games page
- **THEN** the touch-target check fails naming the button and its size

#### Scenario: Compact chip with a tap area
- **WHEN** a 32 px-tall chip has a transparent tap area extending it to 48 px
- **THEN** the touch-target check passes it
