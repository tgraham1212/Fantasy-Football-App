## ADDED Requirements

### Requirement: 4.4.6.5 Keeper eligible badge
On the redraft Roster card, a keeper-eligible Player SHALL show a gold "KE" badge after his name.

**Traces to:** 4.4.6; 4.11.6
**Verified by:** Test: `tests/layout/test_managers_page.py::test_keeper_eligible_badge`

#### Scenario: Kept receiver
- **WHEN** a visitor opens the redraft Manager whose roster holds Jaxon Smith-Njigba, keeper eligible for 2027
- **THEN** his row shows a gold "KE" badge after his name
