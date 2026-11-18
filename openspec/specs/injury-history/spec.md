# injury-history Specification

## Purpose

Keeps each fantasy player's injury status per NFL week, so game cards can say who was not expected to play, and infers it for weeks played before statuses were saved.

## Requirements

### Requirement: Weekly status saved
Each run during the regular season or playoffs SHALL save, for the current NFL week, every fantasy-position player whose Sleeper injury status is set, with that status, replacing the week's earlier save so the last save before the week ends is kept. Earlier weeks SHALL never be overwritten.

#### Scenario: Status changes during the week
- **WHEN** a player is Questionable on Thursday's run and Out on Saturday's
- **THEN** the week's saved status for him is Out

#### Scenario: Week rolls over
- **WHEN** the current week moves from 11 to 12
- **THEN** week 11's saved statuses stay as they were and week 12 is saved

### Requirement: Not-playing status for a week
For a team in a given week, the system SHALL list each rostered player expected not to play: on bye when his NFL team has no game, otherwise his saved status when it is an out status. The out statuses SHALL be one list shared by the whole system: Out, Doubtful, IR, PUP, Sus, NA and DNR, labelled Out, Doubtful, IR, PUP, Suspended, Not active and Did not report. Doubtful counts as out because such players almost never play. For a week after the latest saved week, the latest saved statuses SHALL be used. For a week before statuses were first saved, a player SHALL be listed as inferred out when he was on the roster that week, had a projection of 0 or none, and his NFL team played.

#### Scenario: Saved status
- **WHEN** week 12 has a saved status of Doubtful for a rostered receiver whose team plays
- **THEN** he is listed as Doubtful

#### Scenario: Inferred for an early week
- **WHEN** week 5 has no saved statuses and a rostered running back had no projection while his team played
- **THEN** he is listed as inferred out

#### Scenario: Upcoming week
- **WHEN** week 11's statuses are the latest saved and a rostered player is Out in them
- **THEN** he is listed as Out for week 15, and players without week-15 projections yet are not inferred out

#### Scenario: Bye
- **WHEN** a rostered player's team has no game in week 9
- **THEN** he is listed as on bye regardless of any status

#### Scenario: Not active
- **WHEN** week 11 has a saved status of NA for a rostered quarterback whose team plays
- **THEN** he is listed as Not active

#### Scenario: Suspended
- **WHEN** week 11 has a saved status of Sus for a rostered receiver
- **THEN** he is listed as Suspended
