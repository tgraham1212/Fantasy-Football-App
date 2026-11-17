# Spec Delta

## Purpose

The Games page of each league: this season's matchups week by week, with the model's forecast for each game, the players it is counting on and who is sitting out, and for finished weeks how the real scores compared with the forecast.

## ADDED Requirements

### Requirement: Week control
The Games page SHALL open on the current NFL week and offer a dropdown of every regular-season and playoff week of the current season, with previous and next arrows that step one week and are disabled at the first and last week.

#### Scenario: Default week
- **WHEN** a visitor opens the Games page on a Saturday during week 11
- **THEN** week 11 is shown and selected in the dropdown

#### Scenario: Step back
- **WHEN** the visitor clicks the previous arrow on week 11
- **THEN** week 10 is shown

### Requirement: Matchup cards
Each game SHALL be a card in a two-column layout (one column on phones, a lone last card centred), with the two teams stacked. Each team row SHALL show the owner's colour dot as on the Predictions table, the owner name with the team name beneath, the mean simulated points and the win probability. To the right of the rows, a chart SHALL overlay both teams' score distributions, each shaded in its owner colour.

#### Scenario: Card contents
- **WHEN** week 11's card for two teams is shown
- **THEN** each team row has its colour dot, owner and team name, mean points and win probability, and the chart overlays both distributions in the two owner colours

#### Scenario: Phone width
- **WHEN** the page is shown at 375px
- **THEN** cards stack in one column with no horizontal page scroll

### Requirement: Win probability fill
The win probability cell SHALL be filled on a diverging scale validated with the project's colour tool: neutral grey at 50%, a progressively stronger green toward 100% and red toward 0%, with text that keeps at least 4.5:1 contrast at every step, in both themes.

#### Scenario: Heavy favourite
- **WHEN** a team's win probability is 92%
- **THEN** its cell is a strong green and the other team's 8% cell a strong red

#### Scenario: Toss-up
- **WHEN** both teams are near 50%
- **THEN** both cells are close to the neutral grey

### Requirement: Key players
Below each card, each team SHALL list four key players from the model's lineup: the quarterback, the highest-projected running back, the highest-projected wide receiver, and the highest-projected remaining RB, WR or TE, each with projected points; a slot the model fills at replacement level is listed as a free agent. An expand control SHALL show the full lineup the simulation used, with free-agent fills labelled as replacement level.

#### Scenario: Key four
- **WHEN** a team's model lineup has RBs projected 18 and 11, WRs 16 and 13, and a TE at 9
- **THEN** its key players are the QB, the 18-point RB, the 16-point WR and the 13-point WR

#### Scenario: Full lineup
- **WHEN** the visitor expands a team's lineup
- **THEN** every lineup slot is listed with its player and projected points, and a replacement fill reads as a free agent at replacement level

### Requirement: Not playing
Below each card, each team SHALL list rostered players expected not to play that week (bye, Out, Doubtful, IR, or inferred out for weeks without saved statuses), each labelled with the reason.

#### Scenario: Injured starter
- **WHEN** a team's receiver is Out for week 11
- **THEN** he is listed under that team as Out

### Requirement: Finished weeks
For a finished week, each card SHALL show the prediction of record, a check mark in the winner's win probability cell, and a vertical line on each team's distribution at its actual score in the team's colour. A pre-week forecast used for a week before the log existed SHALL be labelled as such.

#### Scenario: Week 10 look-back
- **WHEN** a visitor selects week 10 after it is final
- **THEN** each card shows the record's probabilities, a check on the winner, and both actual scores as lines on the chart

### Requirement: Playoff weeks
Playoff weeks SHALL show the projected bracket until Sleeper sets real pairings: games ordered with the 1 seed's side at the top and the 2 seed's side at the bottom, each projected card labelled with how often that pairing happened in the simulations, a bye card for each team with a first-round bye, and toilet bowl games below the winners bracket where the league plays one.

#### Scenario: Projected first round
- **WHEN** a visitor selects week 15 before pairings are set
- **THEN** the 4 v 5 game appears above the 3 v 6 game, bye cards appear for seeds 1 and 2, and each projected game shows how often it occurred

### Requirement: Games data exported
Each league's site data SHALL include, per week of the current season, the cards' data: teams, owners, mean points, win probabilities, histograms, lineups, key players, not-playing lists, the forecast's run time and, for finished weeks, the record, actual scores and winner. The page SHALL load one week at a time. The export SHALL succeed without game data, and the page SHALL then say games are not yet available.

#### Scenario: No games yet
- **WHEN** the export runs on a store without game data
- **THEN** the site builds and the Games page says games are not yet available
