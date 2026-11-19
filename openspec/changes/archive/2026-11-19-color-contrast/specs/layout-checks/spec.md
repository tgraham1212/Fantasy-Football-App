# Spec Delta

## MODIFIED Requirements

### Requirement: Accessibility check
A browser test SHALL run the axe-core accessibility engine with its WCAG 2.2 A and AA rules on every page and its main views. It SHALL run in Chromium at a phone and a desktop width, in light and dark mode. It SHALL fail on any violation not listed in a committed baseline, naming the rule, the page, the mode and the element. A listed violation that no longer occurs SHALL also fail the test until it is removed from the baseline, so the baseline only shrinks.

#### Scenario: New contrast problem
- **WHEN** a change adds grey text that fails the AA contrast ratio
- **THEN** the accessibility check fails naming the color-contrast rule, the page and the element

#### Scenario: Fixed finding
- **WHEN** a follow-up change fixes a baselined violation
- **THEN** the check fails until that entry is removed from the baseline

#### Scenario: Dark mode problem
- **WHEN** a button's label passes contrast in light mode but fails in dark mode
- **THEN** the accessibility check fails naming dark mode and the button
