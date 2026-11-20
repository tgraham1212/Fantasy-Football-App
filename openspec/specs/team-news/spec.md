# team-news Specification

## Purpose

Team News: short stories about each manager's season, generated from stored data with editable sentence templates, for the Managers page's news card.

## Requirements

### Requirement: Team story types
Stories SHALL be generated for the current season only. The team story types SHALL be:
- **result:** with the top scorer;
- **forecast move:** when the playoff forecast changes by at least 10 points in a week;
- **record:** a team record, or a league top-3, broken;
- **streak:** three or more wins or losses in a row;
- **rivalry:** the rivalry-week preview and result.

#### Scenario: Forecast jump
- **WHEN** a team's playoff forecast rises from 53% to 71% after a week
- **THEN** a forecast story reads that it is up 18 to 71%

### Requirement: Player story types
The player story types SHALL be:
- **injury:** a rostered player newly given an out status, with the body part;
- **practice report:** a rostered starter limited or not practising;
- **depth chart move:** a rostered player's depth-chart order changing;
- **trending add:** a rostered player among Sleeper's 10 most-added players;
- **player milestone:** WAR passing each whole number;
- **Team of the Week:** the league's best lineup that week, shown only when one of the manager's players is in it.

#### Scenario: Team of the Week without their players
- **WHEN** none of a manager's players is in that week's Team of the Week
- **THEN** no Team of the Week story appears on their page

#### Scenario: Practice report
- **WHEN** a rostered starter is listed as not practising on Thursday
- **THEN** a practice report story names him and the day

### Requirement: Templates are editable
Every headline and story sentence SHALL come from a template with a copy ID in `site-copy.txt`, with named placeholders for the data, so the owner can reword any story type through the site-copy workflow.

#### Scenario: Reworded template
- **WHEN** the owner edits the result headline template and applies it
- **THEN** every result story uses the new wording at the next export

### Requirement: Feature story and order
Stories SHALL be ordered newest first. The feature story SHALL be the most important story of the latest week: a result, unless a record or a forecast move of 20 points or more outranks it. Each story SHALL carry its time, category and a link to the page its data comes from.

#### Scenario: Record beats result
- **WHEN** the latest week has a result and a new league-high score
- **THEN** the feature story is the record

### Requirement: Retired managers' news
A retired manager's news SHALL show their last season's stories, ending with a final-season story.

#### Scenario: Retired
- **WHEN** TateFM's dynasty page is shown
- **THEN** the news card shows his 2023 stories

### Requirement: Trending adds saved
Each refresh SHALL save Sleeper's trending adds (the most-added players over the last 24 hours) with the time saved. A failed fetch SHALL skip the step with a warning and never stop the refresh.

#### Scenario: Sleeper unreachable
- **WHEN** the trending request fails during a refresh
- **THEN** the refresh completes, logs a warning, and no trending stories are added for that refresh
