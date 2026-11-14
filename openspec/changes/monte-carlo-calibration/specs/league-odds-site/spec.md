# Spec Delta

## ADDED Requirements

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

### Requirement: Calibration report exported
The export SHALL include the stored calibration report in the site data when one exists, and SHALL succeed without one.

#### Scenario: Report present
- **WHEN** the export runs after calibration has been run
- **THEN** the site data contains the calibration report that was stored

#### Scenario: Report absent
- **WHEN** the export runs on a store that has never been calibrated
- **THEN** the league files are written as usual and the export succeeds
