## MODIFIED Requirements

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

## ADDED Requirements

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
