## ADDED Requirements

### Requirement: 6.6.5 Past injury reports
For each season from 2021, the store SHALL hold each fantasy Player's weekly IR, PUP and Out statuses from nflverse, keyed by Sleeper Player id.

**Rationale:** Saved Sleeper statuses begin in 2026; the draft grades need injuries for every season.
**Traces to:** 6.6; 4.11.2.3
**Verified by:** Test: `tests/test_injury_reports.py::test_statuses_from_rosters_and_reports`

#### Scenario: Rashee Rice 2024
- **WHEN** the 2024 injury reports are stored
- **THEN** Rashee Rice is on IR in weeks 5 to 18 and has no status in weeks 1 to 4

### Requirement: 6.6.5.1 Injury report fetch schedule
A completed season's injury reports SHALL be fetched once, and the current season's at most once every 20 hours.

**Rationale:** nflverse's weekly roster file is about 15 MB a season and changes daily at most, while cold runs come every 15 minutes in season.
**Traces to:** 6.6.5
**Verified by:** Test: `tests/test_injury_reports.py::test_fetch_schedule`

#### Scenario: Backfill
- **WHEN** the 2023 injury reports are not stored
- **THEN** the next cold run fetches them once, and later runs do not

### Requirement: 6.6.5.2 Injury report failure
A failed injury report fetch SHALL keep the file stored last time, with a warning naming the season, while the cold run carries on.

**Traces to:** 6.6.5; 5.5.4
**Verified by:** Test: `tests/test_injury_reports.py::test_failure_keeps_file_and_only_warns`

#### Scenario: nflverse unreachable
- **WHEN** the nflverse request fails during a cold run
- **THEN** the stored injury reports stay as they were, a warning names the season, and the run continues
