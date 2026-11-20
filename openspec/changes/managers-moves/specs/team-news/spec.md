## ADDED Requirements

### Requirement: Moves story types
The Moves story types SHALL be:
- **trade:** every trade, naming what each side got;
- **big bid:** a won bid of at least 25% of the season budget, or the team's biggest bid of the season, with the next bid;
- **pickup pays off:** once, when an added window passes +1.0 WAR;
- **got away:** once, when a departed window passes +1.0 WAR for another team;
- **outbid:** a notable lost bid, as defined below.

#### Scenario: Pickup pays off
- **WHEN** Rico Dowdle, picked up in week 3, passes +1.0 WAR for the team in week 7
- **THEN** a pickup-pays-off story appears in week 7, and not again when he passes +2.0

### Requirement: Outbid stories
An outbid story SHALL appear for a lost waiver bid of at least 20% of the season budget, or for one lost by $3 or less, or on waiver priority, with a bid of at least 5% of the budget. It SHALL name the player, the winner and both bids.

#### Scenario: Big outbid
- **WHEN** a manager's $40 bid on Bucky Irving loses to KingDso's $55 in a $100 league
- **THEN** an outbid story reads that the $40 lost to KingDso's $55

#### Scenario: Small loss
- **WHEN** a manager's $2 bid loses to a $4 bid in a $100 league
- **THEN** no outbid story appears

### Requirement: Moves stories per week
At most three Moves stories per week per team SHALL be kept, counted apart from the player stories, so a busy trade week cannot push out injury news.

#### Scenario: Busy trade week
- **WHEN** a dynasty manager makes four trades in one week and a starter is ruled out
- **THEN** three trade stories and the injury story appear
