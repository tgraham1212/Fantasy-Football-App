# Spec Delta

## ADDED Requirements

### Requirement: Preseason entry after the draft
For every stored season whose draft is done (league status in season or complete), the system SHALL store a week-0 entry for every member of that season holding their rating entering the season: the reverted mean for a returning manager, the start rating for a newcomer, the uncertainty unchanged, no weekly z-score, and the career mean z carried from earlier seasons. A season still before or during its draft SHALL have no week-0 entries.

#### Scenario: Returning manager after the draft
- **WHEN** a manager ended 2025 at 1300 and the 2026 league is in season with no week scored yet
- **THEN** their latest entry is 2026 week 0 with a rating mean of 1200 and no z-score

#### Scenario: Newcomer after the draft
- **WHEN** a manager first owns a roster in 2026 and the 2026 draft is done
- **THEN** their first entry is 2026 week 0 with a rating mean of 1000

#### Scenario: Before the draft
- **WHEN** the 2026 league is stored with status pre_draft
- **THEN** no 2026 entries exist and every manager's latest entry is from 2025

#### Scenario: Week list
- **WHEN** the ratings file is written for a league whose seasons are all past their drafts
- **THEN** its week list holds a week-0 item at the start of every season followed by that season's rated weeks
