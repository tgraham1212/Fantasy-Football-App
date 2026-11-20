## ADDED Requirements

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
