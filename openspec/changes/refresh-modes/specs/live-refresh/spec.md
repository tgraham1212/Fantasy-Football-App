## Purpose

Keeps the current week's live scores, forecast and game cards up to date within a minute or two, without committing to git or deploying the site: a hot run computes them on GitHub Actions and the refresh relay stores and serves them as one bundle.

## ADDED Requirements

### Requirement: Hot run
A hot run SHALL:
- fetch the current week's matchups and the NFL scoreboard;
- simulate the live week with the same model and number of runs as the cold run;
- build this week's game cards for every league.

It SHALL run on its own concurrency group, so it never waits behind a cold run or a code deploy. It SHALL NOT commit, push or deploy anything.

#### Scenario: During the 1:00 pm games
- **WHEN** a hot run finishes during Live
- **THEN** the bundle holds new scores, win probabilities and cards for both leagues, and git and the published site are unchanged

### Requirement: Hot run inputs
A hot run SHALL start from the checked-out committed records plus the latest cold run's build cache: ratings, replacement levels, WAR, future-week projections and the exported site. When no cache exists, it SHALL rebuild those offline from the committed records before simulating.

#### Scenario: Cache evicted
- **WHEN** no build cache exists for any recent commit
- **THEN** the hot run rebuilds the derived data offline and still writes a bundle

### Requirement: One bundle per run
Each hot run SHALL make exactly one write to Cloudflare KV. That write SHALL be a bundle holding:
- for every league, the forecast file and this week's game cards, in the same format the page reads from the static files;
- each game's status;
- the base cold commit;
- the run's time.

A failed hot run SHALL leave the previous bundle in place.

#### Scenario: Run fails mid-way
- **WHEN** the scoreboard fetch fails in a hot run
- **THEN** no KV write happens and the page keeps the previous bundle

### Requirement: Bundle served
The relay SHALL answer `GET /live` from the published site with the latest bundle, or with an empty answer when there is none or none newer than the time the page gives. It SHALL accept a bundle only from the hot run, using a secret the site never sees. The bundle SHALL expire 7 days after its last write.

#### Scenario: Write from elsewhere
- **WHEN** a request without the hot run's secret tries to write a bundle
- **THEN** the relay refuses it and the stored bundle is unchanged

### Requirement: Write budget
The hot cadence SHALL keep KV writes under Cloudflare's free allowance of 1,000 a day, with one write per hot run and no other per-run writes. If the allowance is reached, hot runs SHALL end without failing the cold runs, and the page SHALL keep the latest bundle or static files.

#### Scenario: Full Sunday
- **WHEN** games run from 1:00 pm to the end of the Sunday night game
- **THEN** about 450 hot runs write about 450 times, within the allowance
