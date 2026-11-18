## MODIFIED Requirements

### Requirement: Manager colours on the rating chart
A current member's line SHALL use the same colour as their team's line on the odds chart and row in the table. Former members SHALL use greys distinct from one another and readable against the chart background in both themes. Vacant rosters (rosters with no owner in any stored season) SHALL NOT be drawn. A roster that inherits an earlier or later owner SHALL be drawn as part of that owner's line. Every drawn line SHALL be labelled with the manager's display name at its end.

#### Scenario: Former members
- **WHEN** the dynasty rating chart shows five former members
- **THEN** their five lines are five different greys, none of which matches a current member's colour

#### Scenario: Vacant roster hidden
- **WHEN** a season has a roster with no owner in any stored season
- **THEN** no line is drawn for it, though the other managers' ratings reflect its scores

#### Scenario: Inherited owner drawn
- **WHEN** dynasty roster 11 has no owner in 2023 and was DeekBurg's in 2022
- **THEN** DeekBurg's grey line continues through 2023
