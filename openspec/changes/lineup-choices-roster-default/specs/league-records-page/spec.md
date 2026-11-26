## ADDED Requirements

### Requirement: 4.9.2.1.3.4 Lineup choices explained
The lineup-choices records SHALL explain on hover, on keyboard focus and atop their pop-ups that the figure is the starters' points minus those of the roster's highest Sleeper projections.

**Rationale:** The figure is set against Sleeper's projections, not the best lineup in hindsight, so it can be positive.
**Traces to:** 4.9.2.1.3; 2.8
**Verified by:** Test: `tests/layout/test_league_records_page.py::test_lineup_choices_explained`

#### Scenario: Hover
- **WHEN** a visitor hovers over "Most Points Gained by Lineup Choices"
- **THEN** "Your starters' points minus what starting your roster's highest Sleeper projections would have scored; following the projections scores 0." is shown
