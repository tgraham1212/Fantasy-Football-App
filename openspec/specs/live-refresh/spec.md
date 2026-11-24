# live-refresh Specification

## Purpose

Keeps the current week's live scores, Forecasts and game cards within a minute or two of Sleeper without committing to git or deploying the site: a hot run computes them on GitHub Actions, and the refresh relay stores and serves them as one bundle. It delivers need 5, Current Data, within need 11's free limits; how it fits together is in `docs/refresh-modes.md`.

## Requirements

### Requirement: 5.2 Hot run
A hot run SHALL fetch the current week's matchups and the NFL scoreboard, simulate the live week with the cold run's model and run count, and build this week's game cards for every league.

**Traces to:** 5; 1.1.12; 2.3
**Verified by:** Test: `tests/test_hot.py::test_hot_run_builds_one_bundle_and_leaves_data_unchanged`

#### Scenario: During the 1:00 pm games
- **WHEN** a hot run finishes during Live
- **THEN** its bundle holds new scores, win probabilities and cards for both leagues

### Requirement: 5.2.1 Hot runs change nothing published
A hot run SHALL leave git and the published site unchanged, running in its own concurrency group with read-only access.

**Rationale:** Its own group means it never waits behind a cold run or a code deploy.
**Traces to:** 5.2
**Verified by:** Test: `tests/test_workflows.py::test_hot_run_never_commits_pushes_or_deploys`

#### Scenario: Live hot run
- **WHEN** a hot run finishes during Live
- **THEN** git and the published site are unchanged

### Requirement: 5.2.2 Hot run inputs
A hot run SHALL start from the committed records plus the latest cold run's build cache, rebuilding the derived data offline when no cache exists.

**Traces to:** 5.2; 6
**Verified by:** Test: `tests/test_storage_tiers.py::test_build_from_committed_records_alone`; Inspection: `.github/workflows/hot.yml`, the cache restore and the offline build when it misses

#### Scenario: Cache evicted
- **WHEN** no build cache exists for any recent commit
- **THEN** the hot run rebuilds the derived data offline and still writes a bundle

### Requirement: 5.2.3 One bundle per run
Each hot run SHALL make at most one write to Cloudflare KV: a bundle holding each league's Forecast file and this week's game cards in the page's format, each game's state, the base cold commit and the run's time.

**Rationale:** An unchanged bundle is not written at all.
**Traces to:** 5.2
**Verified by:** Test: `tests/test_relay.py::test_one_bundle_per_hot_run`; Test: `tests/test_hot.py::test_hot_command_writes_the_bundle_and_its_meta`

#### Scenario: Bundle contents
- **WHEN** a hot run writes its bundle
- **THEN** the bundle holds both leagues' files, each game's state, the cold commit and the run's time

### Requirement: 5.2.3.1 Failed hot run
A failed hot run SHALL leave the previous bundle in place.

**Traces to:** 5.2.3
**Verified by:** Inspection: `.github/workflows/hot.yml`, the bundle is sent only after every step succeeds

#### Scenario: Run fails mid-way
- **WHEN** the scoreboard fetch fails in a hot run
- **THEN** no KV write happens and the page keeps the previous bundle

### Requirement: 5.2.4 Bundle served
The relay SHALL answer the site's `GET /live` with the latest bundle, or an empty answer when none is newer than the time the page gives.

**Traces to:** 5.2; 5.2.3; 5.3.4
**Verified by:** Test: `tests/test_relay.py::test_page_gets_the_newer_bundle`

#### Scenario: Nothing newer
- **WHEN** the page already shows the latest bundle's data
- **THEN** the relay answers with no content

### Requirement: 5.2.4.1 Writes need the secret
The relay SHALL accept a bundle only with the hot run's secret, which the site never sees.

**Traces to:** 5.2.4; 12
**Verified by:** Test: `tests/test_relay.py::test_bundle_writes_need_the_secret`

#### Scenario: Write from elsewhere
- **WHEN** a request without the hot run's secret tries to write a bundle
- **THEN** the relay refuses it and the stored bundle is unchanged

### Requirement: 5.2.4.2 Bundle expiry
A stored bundle SHALL expire 7 days after its last write.

**Traces to:** 5.2.4
**Verified by:** Inspection: `relay/worker.js`, the bundle is written with a 7-day expiry

#### Scenario: Off-season
- **WHEN** no hot run has written for 7 days
- **THEN** the relay holds no bundle

### Requirement: 11.2 KV write budget
Hot runs SHALL stop at a daily cap below Cloudflare's free allowance of 1,000 KV writes, while cold runs carry on.

**Rationale:** Measured on 2026-11-22: a full Sunday took about half the allowance.
**Traces to:** 11; 5.2.3
**Verified by:** Test: `tests/test_relay.py::test_hot_runs_stop_at_the_write_cap`

#### Scenario: Full Sunday
- **WHEN** games run from 1:00 pm to the end of the Sunday night game
- **THEN** the hot runs write about 450 times, within the allowance
