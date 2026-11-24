# project-standards Specification

## Purpose

Records the standards every change to the project follows (browsers, phone sizes, accessibility, Material Design usability, colour, Player names, nomenclature, writing style, calculation and feature documentation, and requirements) where planned work and everyday work both see them, and checks the ones that can be checked. It serves needs 9, Usable by Every Manager, and 10, Maintainable Project; the terms are in `openspec/glossary.md`.

## Requirements

### Requirement: 10.14 Standards recorded
The project standards SHALL be written in the `openspec/config.yaml` context and summarised in `CLAUDE.md`, covering browsers, phone widths, accessibility, Material Design, colour, Player names, nomenclature, style, and calculation and feature documentation.

**Rationale:** Planned changes read the context; every session reads `CLAUDE.md`.
**Traces to:** 10
**Verified by:** Inspection: `openspec/config.yaml` (context) and `CLAUDE.md`, each listed standard is present

#### Scenario: Quick fix outside a change
- **WHEN** a small fix is made without a planned change
- **THEN** the standards in `CLAUDE.md` apply to it

### Requirement: 9.5 Supported browsers
Every change SHALL work in Chrome, Safari, Edge and Firefox on desktop, and in Chrome and Safari on phones, at the tested phone widths.

**Traces to:** 9
**Verified by:** Test: `tests/layout/test_layout.py::test_control_keeps_the_layout`; Test: `tests/layout/test_layout.py::test_wide_fonts_do_not_scroll_sideways`

#### Scenario: Safari on a phone
- **WHEN** a change ships a new page
- **THEN** the page works in Safari's engine at the tested phone widths

### Requirement: 9.5.1 Phone widths from statistics
The tested phone widths SHALL cover StatCounter's top six US mobile screen widths, reviewed at least once a year and whenever a new width enters the top six.

**Rationale:** October 2026 statistics: 414, 390, 384, 360, 402 and 393 px; tested at 360, 390, 414 and 440 px.
**Traces to:** 9.5
**Verified by:** Inspection: `openspec/config.yaml`, the dated StatCounter figures, next due 2027-10

#### Scenario: Width list from statistics
- **WHEN** the yearly review finds a new width in the top six
- **THEN** the tested widths are updated to cover it

### Requirement: 9.6 Material Design 3 usability
Interactive controls SHALL follow Material Design 3's usability rules, touch targets of at least 48 × 48 px on phones, visible focus and pressed states, and a consistent type scale, while the site keeps its own visual style.

**Traces to:** 9
**Verified by:** Test: `tests/layout/test_accessibility.py::test_touch_targets_on_phones`; Inspection: the live site, focus and pressed states and the type scale

#### Scenario: New control
- **WHEN** a change adds a button
- **THEN** it has a visible focus state and, on phones, a touch target of at least 48 × 48 px

### Requirement: 9.7 Colour standard
Site colours SHALL be chosen and adjusted in OKLCH, a contrast fix changing only lightness and keeping hue and chroma, and a new colour derived from an existing hue where one fits.

**Rationale:** Tokens are stored as hex, each adjusted one noting its OKLCH lightness (`tools/team_palette.py` has the helpers).
**Traces to:** 9
**Verified by:** Inspection: `site/styles.css`, adjusted tokens carry their OKLCH note

#### Scenario: Grey text too light
- **WHEN** a grey text colour fails its contrast ratio
- **THEN** the fix lowers its OKLCH lightness and keeps its hue and chroma

### Requirement: 9.7.1 Colour contrast check
For light and dark mode, a test SHALL check each text colour token against its backgrounds at 4.5:1, and focus rings and chart lines against the page and card backgrounds at 3:1, naming the mode, both tokens and the ratio on failure.

**Traces to:** 9.7; 9
**Verified by:** Test: `tests/test_colour_contrast.py::test_colour_tokens_meet_contrast`; Test: `tests/test_colour_contrast.py::test_check_catches_dark_only_failure`

#### Scenario: Chart text too light
- **WHEN** a change sets chart axis text to a grey of 3.5:1 on cards in light mode
- **THEN** the check fails naming light mode, the two tokens and 3.5:1

### Requirement: 9.7.1.1 Every colour token classified
Every colour token SHALL be checked as a text, line or background colour, or exempted with a reason.

**Traces to:** 9.7.1
**Verified by:** Test: `tests/test_colour_contrast.py::test_unclassified_token_fails`

#### Scenario: New token
- **WHEN** a change adds a colour token without classifying it
- **THEN** the contrast test fails naming the token

### Requirement: 9.8 Player name standard
Wherever the site shows a Player's name in a limited space, it SHALL show the full name, switching to first initial and last name ("A. St. Brown") only when the full name does not fit, a defence by its team nickname, with the full name in a tooltip and never cut off.

**Traces to:** 9
**Verified by:** Test: `tests/layout/test_layout.py::test_phone_lineups_show_full_names`; Test: `tests/layout/test_managers_page.py::test_cards_cut_nothing_and_never_scroll_sideways`

#### Scenario: Name does not fit
- **WHEN** "Amon-Ra St. Brown" is wider than its space
- **THEN** "A. St. Brown" shows, with the full name on hover

### Requirement: 10.10.1 Nomenclature
Everything people read, site text, documentation and specs, SHALL use the glossary's terms: Managers, Team Names, Players, Forecasts for the simulation's output, and Projections only for Sleeper's inputs.

**Traces to:** 10.10
**Verified by:** Test: `tests/test_nomenclature.py::test_site_copy_uses_project_nomenclature`; Test: `tests/test_requirements.py::test_no_banned_terms`

#### Scenario: Forecast wording
- **WHEN** a change adds a note describing the simulation's playoff numbers
- **THEN** the note calls them Forecasts

### Requirement: 10.10.1.1 Nomenclature check
A test SHALL flag each `site-copy.txt` entry using a retired term (`owner`, `odds`, `chances`, or `prediction` for a Forecast) that is not in a committed baseline, code and data identifiers exempt.

**Traces to:** 10.10.1; 10.16
**Verified by:** Test: `tests/test_nomenclature.py::test_site_copy_uses_project_nomenclature`; Test: `tests/test_nomenclature.py::test_flagged_terms`

#### Scenario: Retired term in new copy
- **WHEN** a change adds site text reading "the owner's odds"
- **THEN** the check fails naming the entry and the terms

### Requirement: 10.15 Writing style
Writing SHALL follow APA style, with titles and headings in title case.

**Traces to:** 10
**Verified by:** Inspection: `openspec/inspection-checklist.md`, each spec's standard review

#### Scenario: New heading
- **WHEN** a change adds a section titled "how it works"
- **THEN** the review corrects it to "How It Works"
