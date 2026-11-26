## MODIFIED Requirements

### Requirement: 2.1.14 Lineup choices shown
On live and finished cards, in both views, each team SHALL show "Lineup choices: +N" or "-N" beneath the forecasted line of its score block: its points against starting its highest Sleeper Projections, explained on hover, green when positive and red when negative.

**Rationale:** Calculations.txt section 11.
**Traces to:** 2.1; 2.1.3.2
**Verified by:** Test: `tests/test_views.py::test_lineup_choices_examples_and_live_rule`

#### Scenario: Positive choices
- **WHEN** a team's lineup choices are +7.4
- **THEN** "Lineup choices: +7.4" shows in green beneath its forecasted line, never over the scores, and hovering explains that it is the starters' points minus what the roster's highest Sleeper projections would have scored
