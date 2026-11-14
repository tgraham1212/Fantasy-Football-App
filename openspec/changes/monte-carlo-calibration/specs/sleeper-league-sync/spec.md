# Spec Delta

## MODIFIED Requirements

### Requirement: Configured leagues
The system SHALL read the leagues to track from a configuration file. Each entry gives a league's current Sleeper league ID and a short display key. The file MAY also carry an optional simulation section with a residual scale, a positive number that defaults to 1.0 when absent; any other value SHALL be rejected as a configuration error.

#### Scenario: Both leagues configured
- **WHEN** the configuration lists dynasty league `1339662153812025344` and redraft league `1389347876550770688`
- **THEN** a sync pulls data for both leagues and for no others

#### Scenario: New season for the redraft league
- **WHEN** the redraft league renews and the configuration is changed to the new season's league ID
- **THEN** the next sync follows the history chain back through all prior seasons, and the league keeps its display key and earlier history

#### Scenario: Residual scale configured
- **WHEN** the configuration's simulation section sets the residual scale to 0.9
- **THEN** the configuration loads with a residual scale of 0.9

#### Scenario: Invalid residual scale
- **WHEN** the residual scale is set to 0, a negative number or text
- **THEN** loading the configuration fails with an error naming the residual scale
