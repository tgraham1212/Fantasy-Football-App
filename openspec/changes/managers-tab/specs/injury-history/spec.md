# Spec Delta

## ADDED Requirements

### Requirement: Weekly player details saved
Alongside each week's statuses, each run SHALL save, for every fantasy-position player on a league roster, Sleeper's injury body part, practice participation and depth-chart order when set, replacing the week's earlier save so the last save before the week ends is kept. Earlier weeks SHALL never be overwritten.

#### Scenario: Practice report
- **WHEN** a rostered receiver is listed as limited in practice on Thursday's run
- **THEN** the week's saved details record his practice participation as limited

#### Scenario: Depth chart change
- **WHEN** a running back's depth-chart order moves from 2 to 1 between weeks 10 and 11
- **THEN** week 10's saved details keep 2 and week 11's record 1
