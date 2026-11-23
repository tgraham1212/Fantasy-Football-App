# project-standards Specification

## Purpose

Records the standards every change to the project follows (browsers, phone sizes, accessibility, Material Design usability, nomenclature, writing style and calculation documentation) where planned work and everyday work both see them, and checks the ones that can be checked.

## Requirements

### Requirement: Standards recorded
The project standards SHALL be written in the `openspec/config.yaml` project context, which reaches every planned change, and summarised in a `CLAUDE.md` file at the project root, which reaches every working session. The standards SHALL state:
- the supported browsers and devices;
- the phone widths tested and their source;
- WCAG 2.2 AA;
- which Material Design 3 rules are followed and which are not;
- the nomenclature and APA style rules;
- the calculation documentation rule.

#### Scenario: Planning a change
- **WHEN** a new change is proposed
- **THEN** its planning context includes the standards, and its design addresses any that apply

#### Scenario: Quick fix outside a change
- **WHEN** a small fix is made without a planned change
- **THEN** the standards in `CLAUDE.md` apply to it

### Requirement: Supported browsers and devices
Every change SHALL work in Chrome, Safari, Edge and Firefox on desktop, and in Chrome and Safari on phones, at the most common US mobile screen widths. Those widths SHALL come from StatCounter's US mobile screen-resolution statistics and SHALL be re-checked at least yearly.

#### Scenario: Width list from statistics
- **WHEN** the yearly review finds a new width in the top six US mobile widths
- **THEN** the tested widths are updated to cover it

### Requirement: Material Design 3 usability
Interactive controls SHALL follow Material Design 3's usability rules: touch targets of at least 48 × 48 px on phones, visible focus and pressed states, and a consistent type scale. Material Design 3's visual system (its components, colour roles, shapes and elevation) is not adopted, and the site keeps its own look.

#### Scenario: New control
- **WHEN** a change adds a button
- **THEN** it has a visible focus state and, on phones, a touch target of at least 48 × 48 px

### Requirement: Nomenclature and style
Everything people read (site text, documentation and specs) SHALL use these terms:
- **Managers** for league members
- **Team Names** for managers' yearly team names
- **Players** for NFL players
- **Forecasts** for anything the simulation produces
- **Projections** only for Sleeper's player projections, which are inputs

Titles and headings SHALL use APA title case, and prose SHALL follow APA style. Code and data identifiers are exempt.

#### Scenario: Forecast wording
- **WHEN** a change adds a note describing the simulation's playoff numbers
- **THEN** the note calls them forecasts, not odds, chances or predictions

### Requirement: Nomenclature check
A test SHALL fail when `site-copy.txt` uses a retired term ("owner", "odds", "chances", or "prediction" where it means the forecast) in an entry not listed in a committed baseline. The baseline SHALL only shrink.

#### Scenario: Retired term in new copy
- **WHEN** a change adds site text reading "the owner's odds"
- **THEN** the nomenclature check fails naming the entry and the terms

#### Scenario: Identifier unaffected
- **WHEN** the code keeps a field named `owner_id`
- **THEN** the nomenclature check does not flag it

### Requirement: Colour standard
Site colours SHALL be defined and adjusted in OKLCH (reference: https://oklch.fyi/). A contrast fix SHALL change a colour's lightness and keep its hue and chroma. A new colour SHALL be derived from an existing hue where one fits. The rule SHALL be written in the `openspec/config.yaml` project context and summarised in `CLAUDE.md`.

#### Scenario: Grey text too light
- **WHEN** a grey text colour fails its contrast ratio
- **THEN** the fix lowers its OKLCH lightness and keeps its hue and chroma

#### Scenario: New control colour
- **WHEN** a change needs a new fill colour for a control
- **THEN** it is derived from an existing hue in OKLCH, not picked freely

### Requirement: Colour contrast check
A test SHALL read the colour tokens in `site/styles.css` for light and dark mode, then check each text colour against the backgrounds it is used on at 4.5:1. Focus rings and chart lines SHALL be checked against the page and card backgrounds at 3:1. A failure SHALL name the mode, both tokens and the ratio. Gridlines, axis lines and the animated live signal are exempt, because they are decorative or paired with text.

#### Scenario: Chart text too light
- **WHEN** a change sets chart axis text to a grey of 3.5:1 on cards in light mode
- **THEN** the colour contrast check fails naming light mode, the two tokens and 3.5:1

#### Scenario: Dark mode only
- **WHEN** a colour passes in light mode but fails in dark mode
- **THEN** the colour contrast check fails naming dark mode

### Requirement: Player name standard
Wherever the site shows a player's name in a limited space, it SHALL show the full name, switch to the first initial and last name ("A. St. Brown") only when the full name does not fit, show a defence by its team nickname, keep the full name in a tooltip, and never cut a name off. The rule SHALL be written in the `openspec/config.yaml` project context and summarised in `CLAUDE.md`.

#### Scenario: Name fits
- **WHEN** "Amon-Ra St. Brown" fits its space
- **THEN** the full name shows

#### Scenario: Name does not fit
- **WHEN** "Amon-Ra St. Brown" is wider than its space
- **THEN** "A. St. Brown" shows, with the full name on hover

#### Scenario: New page
- **WHEN** a change adds a page that lists players
- **THEN** its names follow this standard
