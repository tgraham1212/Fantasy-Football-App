# Spec Delta

## MODIFIED Requirements

### Requirement: Refresh button
Each page SHALL show a "Refresh Data" button beside "How good are these odds?" when the relay's address is configured, and no button otherwise, aligned with the other header buttons. Its label SHALL never wrap. Under it (beside it on phones) the page SHALL show "Updated N min ago" while a refresh is available and "Available in N min" while it is held, updating every minute, and a short confirmation after a refresh starts. The note SHALL keep a fixed space so no message moves the button or any other element, SHALL stay within the screen, and SHALL show any longer explanation as a tooltip. After a refresh the visitor started, the note SHALL say "Updated just now" when the new data arrives, or that the refresh did not finish if no new data has arrived after 20 minutes.

#### Scenario: Not configured
- **WHEN** the site is published without a relay address
- **THEN** no refresh button appears and every page works as before

#### Scenario: Held
- **WHEN** the last refresh started 6 minutes ago
- **THEN** the button is disabled with "Available in 9 min" under it

#### Scenario: Started
- **WHEN** a visitor clicks "Refresh Data" and the relay starts a run
- **THEN** the note says "Started, back in ~5 min" with the full explanation as its tooltip, and nothing on the page moves

#### Scenario: Data arrives
- **WHEN** the started run deploys new data four minutes later
- **THEN** the page shows the new data in place and the note reads "Updated just now"

#### Scenario: Run never lands
- **WHEN** 20 minutes pass after a started refresh with no new data deployed
- **THEN** the note says the refresh did not finish

#### Scenario: Aligned
- **WHEN** the header shows the button with its note
- **THEN** the button lines up with the league and calibration buttons and the note hangs below it within the screen at every width
