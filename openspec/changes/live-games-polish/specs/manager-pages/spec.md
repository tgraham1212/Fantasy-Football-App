## MODIFIED Requirements

### Requirement: Season tile layout
Every tile SHALL share one layout: a fixed first line holding a 32 px image or a large number, then a detail line, so images and numbers line up across the bar. Tile text SHALL scale with the tile's width within set limits, and on the narrowest tiles the small label icons SHALL hide before any text is cut. The Last Result score SHALL never wrap and both crests SHALL stay inside the tile, the score shrinking first. Each tile SHALL link to the page its number comes from. On phones the tiles SHALL form two columns, the seventh spanning both.

#### Scenario: Narrow tile
- **WHEN** the Last Result tile is at its narrowest
- **THEN** the score text shrinks and both crests stay inside the tile

#### Scenario: Wide system font
- **WHEN** the page is drawn at 360 px and 1280 px with a wide font like the Linux defaults
- **THEN** no tile's text is cut

### Requirement: Long names on tiles and cards
Player names on the tiles and cards SHALL follow the player name standard: the full name when it fits, otherwise the first initial and last name ("A. St. Brown"), with the full name as a tooltip, fitted again when the width changes or a hidden card is shown. They SHALL fit without being cut at every tested width.

#### Scenario: Longest name on a phone
- **WHEN** Jaxon Smith-Njigba is the top scorer on a 360 px phone
- **THEN** the tile shows "J. Smith-Njigba" in full

#### Scenario: Room for the full name
- **WHEN** a roster card at 1280 px has room for "Amon-Ra St. Brown"
- **THEN** the full name shows
