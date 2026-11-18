# Spec Delta

## MODIFIED Requirements

### Requirement: Fresh scripts after deploy
Every script and stylesheet the site's pages load, and every import between scripts, SHALL carry a stamp in its URL that every deploy replaces with a fingerprint of the site's code files (pages, scripts, stylesheet and bundled libraries, never the data files). The fingerprint SHALL depend only on the content of those files, so a deploy that changes only data keeps the same stamp. Every deploy SHALL publish the same fingerprint in a version file beside the pages and SHALL produce the stamp and version file with one shared stamping command. The source files SHALL carry a placeholder in its place so the site runs unchanged from a local server.

#### Scenario: New deploy
- **WHEN** a visitor whose browser cached the previous deploy's scripts opens the site after a deploy that changed site code
- **THEN** the page references script and stylesheet URLs with the new stamp and the browser fetches the new files

#### Scenario: Data-only deploy
- **WHEN** an hourly refresh deploys new data and no site code changed
- **THEN** the stamp and the published fingerprint are the same as the previous deploy's and browsers reuse their cached scripts

#### Scenario: Local server
- **WHEN** the site is served from the repository checkout
- **THEN** the pages load with the placeholder in the script and stylesheet URLs and work as before

#### Scenario: Reference without a stamp
- **WHEN** a script or stylesheet reference or module import in the site files lacks the placeholder
- **THEN** the test suite fails naming the file

#### Scenario: Deploy without the stamping command
- **WHEN** a workflow that deploys the site does not run the shared stamping command before the upload
- **THEN** the test suite fails naming the workflow

## ADDED Requirements

### Requirement: Deploy on code push
A push to the main branch that changes site code (anything under the site folder other than its data files) SHALL run the tests and the layout check and, when they pass, deploy the site with the current data. It SHALL never run at the same time as a data refresh.

#### Scenario: Code pushed
- **WHEN** a commit changing the Games page script is pushed
- **THEN** the site deploys with it within a few minutes, without waiting for the next data refresh

#### Scenario: Data-only push
- **WHEN** the data refresh pushes its data commit
- **THEN** no code-push deploy runs
