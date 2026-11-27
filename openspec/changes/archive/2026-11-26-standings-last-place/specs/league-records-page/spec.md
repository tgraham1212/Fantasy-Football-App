## ADDED Requirements

### Requirement: 4.9.2.2.2 Player games from this season
A Best Games or Best Bench Games entry from the current season SHALL carry the blue "This season" tag, on its card and in its top 25, at every width.

**Traces to:** 4.9.2.2; 4.9.3
**Verified by:** Test: `tests/layout/test_league_records_page.py::test_player_games_this_season`

#### Scenario: Top 25 on a phone
- **WHEN** a visitor at 360 px opens the Best Bench Games top 25 and its 3rd entry is from week 7 of the current season
- **THEN** that entry carries "This season" and no entry from an earlier season does
