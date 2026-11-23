## Purpose

States what the app is for, as top-level needs. Every requirement in every other spec traces, directly or through parent requirements, to one of these needs. A need is verified through its child requirements, and a need with no children is a need nothing delivers.

## ADDED Requirements

### Requirement: 1 Season Forecasts
The site SHALL show each team's Forecast for the rest of its league's season and how that Forecast changed week by week.

**Rationale:** The app began as a playoff Forecast for the two leagues; it is the reason Managers visit.
**Verified by:** Children

#### Scenario: Mid-season visit
- **WHEN** a Manager opens the Forecasts page in week 11
- **THEN** every team's probability of each season outcome and its weekly history are shown

### Requirement: 2 Game Forecasts
The site SHALL show a Forecast for every game of a league's season before, during and after it is played, and how the result compared with the Forecast.

**Rationale:** Weekly matchups are what Managers follow most closely during the season.
**Verified by:** Children

#### Scenario: Sunday afternoon
- **WHEN** a Manager opens the Games page while games are in progress
- **THEN** each game shows its current win probability and the players still to play

### Requirement: 3 Player Value
The site SHALL show how much each Player is worth to a league, by position and season, measured against what a free agent would provide.

**Rationale:** Managers decide trades, pickups and lineups by comparing Players.
**Verified by:** Children

#### Scenario: Comparing receivers
- **WHEN** a Manager opens the Player WAR or Positional Rankings page
- **THEN** each Player's value is shown against the replacement level for that position

### Requirement: 4 Manager History
The site SHALL show each Manager's history in a league: results, honours, skill rating, moves and news.

**Rationale:** The leagues are social; their history is part of what keeps Managers engaged.
**Verified by:** Children

#### Scenario: Looking up a rival
- **WHEN** a Manager opens another Manager's page
- **THEN** that Manager's finishes, head-to-head record, rating, moves and news are shown

### Requirement: 5 Current Data
The site SHALL reflect Sleeper's league data within a stated delay: within 2 minutes for live scores while games are in progress, and within 20 minutes for other data in season.

**Rationale:** A Forecast is only as useful as the data behind it; stale scores during games defeat the purpose.
**Verified by:** Children

#### Scenario: A touchdown on Sunday
- **WHEN** a Player scores while a Manager has the Games page open
- **THEN** the page shows the new score and win probability within 2 minutes

### Requirement: 6 Durable Record
The project SHALL keep a complete, lasting copy of each league's history and of the Player data the Forecasts use, so every past figure can be reproduced without Sleeper or ESPN.

**Rationale:** Sleeper and ESPN serve only current versions of some data; history that is not stored is lost.
**Verified by:** Children

#### Scenario: Rebuilding from a fresh clone
- **WHEN** someone clones the repository and builds the site without network access
- **THEN** every past season's figures are produced from the stored records

### Requirement: 7 Checked Forecasts
The project SHALL measure how often its Forecasts matched what happened, across every completed season of both leagues.

**Rationale:** Managers trust a probability only if its accuracy is checked against real results.
**Verified by:** Children

#### Scenario: Questioning a probability
- **WHEN** a Manager doubts a 90% win probability
- **THEN** the calibration page shows how often 90% Forecasts were right

### Requirement: 8 Open Methods
The project SHALL publish how every figure on the site is calculated: its formula, inputs, assumptions and decisions.

**Rationale:** A Manager who can see the method can judge a figure for themselves.
**Verified by:** Children

#### Scenario: Asking where a number comes from
- **WHEN** a Manager asks how Player WAR is calculated
- **THEN** `Calculations.txt` and the page's own explanation show the formula and its inputs

### Requirement: 9 Usable by Every Manager
The site SHALL be usable by every Manager: on the supported browsers and phone widths, and to WCAG 2.2 AA.

**Rationale:** Managers check the site on their phones as often as on computers, and every Manager should be able to use it.
**Verified by:** Children

#### Scenario: Checking on a phone
- **WHEN** a Manager opens any page on a 390 px wide phone in Safari
- **THEN** the page fits without sideways scrolling and every control can be used

### Requirement: 10 Maintainable Project
The project SHALL stay understandable and safe to change: its standards, text, calculations, features and requirements documented and checked automatically.

**Rationale:** The project is maintained by one owner with an AI assistant across many sessions; what is not written down and checked drifts.
**Verified by:** Children

#### Scenario: A change in a new session
- **WHEN** a later session changes a feature
- **THEN** the checks fail until its docs, copy and requirements are updated with it
