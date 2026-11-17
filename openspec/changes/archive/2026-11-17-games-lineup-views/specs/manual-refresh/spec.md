# Spec Delta

## MODIFIED Requirements

### Requirement: Refresh button
Each page SHALL show a "Refresh Data" button beside "How good are these odds?" when the relay's address is configured, and no button otherwise, aligned with the other header buttons. Under it the page SHALL show "Updated N min ago" while a refresh is available and "Available in N min" while it is held, updating every minute, and a confirmation after a refresh starts.

#### Scenario: Not configured
- **WHEN** the site is published without a relay address
- **THEN** no refresh button appears and every page works as before

#### Scenario: Held
- **WHEN** the last refresh started 6 minutes ago
- **THEN** the button is disabled with "Available in 9 min" under it

#### Scenario: Started
- **WHEN** a visitor clicks "Refresh" and the relay starts a run
- **THEN** the page says a refresh started and the site updates in about five minutes

#### Scenario: Aligned
- **WHEN** the header shows the button with its note
- **THEN** the button lines up with the league and calibration buttons and the note hangs below it
