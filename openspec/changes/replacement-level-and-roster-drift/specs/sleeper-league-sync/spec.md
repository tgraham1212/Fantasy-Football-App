# Spec Delta

## MODIFIED Requirements

### Requirement: Configured leagues
The system SHALL read the leagues to track from a configuration file. Each entry gives a league's current Sleeper league ID and a short display key. The file MAY also carry an optional simulation section with a residual scale (positive number, default 1.0), a replacement top-N (positive integer, default 3) and prior weeks for the season replacement value (non-negative number, default 4); any other value SHALL be rejected as a configuration error.

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

#### Scenario: Replacement settings configured
- **WHEN** the simulation section sets the replacement top-N to 5 and prior weeks to 2
- **THEN** the configuration loads with those values, and absent keys keep the defaults 3 and 4

#### Scenario: Invalid replacement settings
- **WHEN** the replacement top-N is 0 or a fraction, or prior weeks is negative
- **THEN** loading the configuration fails with an error naming the key
