# Spec Delta

## ADDED Requirements

### Requirement: Fresh scripts after deploy
Every script the site's pages load, and every import between those scripts, SHALL carry a build stamp in its URL that the deploy replaces with the commit identifier, so a browser that has cached an earlier deploy's scripts fetches the new ones with the new page. The source files SHALL carry a placeholder in its place so the site runs unchanged from a local server.

#### Scenario: New deploy
- **WHEN** a visitor whose browser cached the previous deploy's scripts opens the site after a new deploy
- **THEN** the page references script URLs with the new stamp and the browser fetches the new scripts

#### Scenario: Local server
- **WHEN** the site is served from the repository checkout
- **THEN** the pages load with the placeholder in the script URLs and work as before

#### Scenario: Reference without a stamp
- **WHEN** a script reference or module import in the site files lacks the placeholder
- **THEN** the test suite fails naming the file

### Requirement: ELO columns before week one
After a season's draft and before its first scored week, the ELO cell SHALL show the preseason (reverted) rating and the change cell SHALL be empty; from week 1 the change SHALL be measured from that preseason rating. A manager with only one rated week SHALL show their rating and an empty change cell.

#### Scenario: Preseason rating shown
- **WHEN** a manager ended last season at 1300 and this season's draft is done but no week is scored
- **THEN** the ELO cell shows 1200 and the change cell is empty

#### Scenario: Change from the preseason rating
- **WHEN** the same manager's week-1 rating is 1240
- **THEN** the change cell shows +40

#### Scenario: Newcomer's first week
- **WHEN** a team's manager has only one rated week
- **THEN** the ELO cell shows their rating and the change cell is empty

### Requirement: ELO change fill
A positive 1-week ELO change SHALL render as black text on a green fill, a negative change as black text on a red fill, and no change as an empty cell.

#### Scenario: Positive change
- **WHEN** a team's 1-week change is +20
- **THEN** the change cell shows "+20" as black text on a green fill

#### Scenario: Negative change
- **WHEN** a team's 1-week change is -33
- **THEN** the change cell shows "-33" as black text on a red fill

### Requirement: Odds model explained
The calibration page SHALL explain, in plain language for league members, how the odds are made: projections, score noise from past seasons, best lineups with the replacement-level floor, and roster drift, with each league's current replacement levels and how much of a team's edge the model expects to survive weeks ahead. It SHALL state whether the replacement floor and roster drift were on for the shown report and the N used.

#### Scenario: Member reads the explanation
- **WHEN** a league member opens the calibration page
- **THEN** they can read what a replacement-level player is, see this week's replacement level per position for each league, and see how much of a 20-point edge the model expects a team to keep two and twelve weeks out, computed from the published drift model

#### Scenario: Switches stated
- **WHEN** the calibration page shows a report
- **THEN** it states whether the replacement floor and roster drift were on for that report and the N used

## MODIFIED Requirements

### Requirement: ELO placeholder columns
The ELO and 1-week ELO change columns SHALL show each team's current manager rating mean, rounded to a whole number, and its signed change over the last rated week. While no rating data is exported, both columns SHALL render as empty cells.

#### Scenario: Before ELO exists
- **WHEN** the exported data carries no ELO values
- **THEN** every ELO and 1-week change cell is empty and the two headers are still shown

#### Scenario: Future ELO change rendering
- **WHEN** the exported data gives a team an ELO of 1676 and a 1-week change of +20
- **THEN** the ELO cell shows "1676" and the change cell shows "+20" as black text on a green fill

#### Scenario: First rated week of a newcomer
- **WHEN** a team's manager has only one rated week
- **THEN** the ELO cell shows their rating and the change cell is empty

#### Scenario: After the draft, before week 1
- **WHEN** a manager ended last season at 1300 and this season's draft is done but no week is scored
- **THEN** the ELO cell shows 1200 and the change cell is empty

#### Scenario: Week 1 change
- **WHEN** the same manager's week-1 rating is 1240
- **THEN** the change cell shows +40

### Requirement: Calibration page
The site SHALL have a calibration page, reachable from every league page, that shows how well past odds matched real outcomes: for each season outcome, predicted chance against observed rate with the number of cases behind each point; observed against nominal coverage of the score intervals; the Brier skill against the baseline; the lineup gap per league; when the calibration was produced, how many seasons it covers and the residual scale used; and the known caveats.

#### Scenario: Visitor checks the odds
- **WHEN** a visitor opens the calibration page after a calibration report has been published
- **THEN** they can see, for playoff chances, how often teams shown at each level of chance actually made the playoffs

#### Scenario: Calibration not yet run
- **WHEN** the site is published without a calibration report
- **THEN** the calibration page says calibration has not been run and the league pages work as before

#### Scenario: Data from published files
- **WHEN** the calibration page loads
- **THEN** all figures come from a file published with the site, with no server code

#### Scenario: Member reads how it works
- **WHEN** a league member opens the calibration page
- **THEN** they can read what a replacement-level player is, see this week's replacement level per position for each league, and see how many of a 20-point edge the model expects a team to keep two and twelve weeks out, computed from the published drift model

#### Scenario: Model switches shown
- **WHEN** the calibration page shows a report
- **THEN** it states whether the replacement floor and roster drift were on for that report and the N used
