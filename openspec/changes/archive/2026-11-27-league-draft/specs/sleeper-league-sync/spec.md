## ADDED Requirements

### Requirement: 6.2.9 Drafts stored
For each league-season, the sync SHALL store the draft named in that season's league settings, with its settings, every pick and every traded pick.

**Rationale:** The dynasty league's 2022 startup draft, which only moved rosters over from Yahoo, is not the season's named draft and is never stored.
**Traces to:** 6.2; 4.11
**Verified by:** Test: `tests/test_sync.py::test_league_draft_stored`

#### Scenario: Dynasty 2022
- **WHEN** the 2022 dynasty season is synced
- **THEN** its stored draft is the 3-round rookie draft with 36 picks, and the 19-round startup draft is not stored

### Requirement: 6.2.9.1 Draft fetch schedule
A complete draft SHALL be fetched once, and an incomplete draft on every sync.

**Traces to:** 6.2.9
**Verified by:** Test: `tests/test_sync.py::test_complete_draft_fetched_once`

#### Scenario: Backfill
- **WHEN** the 2023 redraft season is stored as complete with no draft
- **THEN** the next sync fetches its draft once, and later syncs do not

### Requirement: 6.2.9.2 Draft failure
A failed draft fetch SHALL keep the files stored last time, with a warning naming the league and season, while the sync and the cold run carry on.

**Traces to:** 6.2.9; 5.5.4
**Verified by:** Test: `tests/test_sync.py::test_draft_failure_keeps_files_and_only_warns`

#### Scenario: Sleeper unreachable
- **WHEN** the draft request fails during a cold run
- **THEN** the stored draft stays as it was, a warning names the league and season, and the run continues

### Requirement: 6.2.10 ADP stored
For each season whose league drafts are all complete, the sync SHALL store Sleeper's preseason half-PPR and dynasty half-PPR ADP for every Player once.

**Rationale:** ADP fixed when the drafts end is the draft-day market the picks are judged against.
**Traces to:** 6.2; 4.11.1
**Verified by:** Test: `tests/test_sync.py::test_adp_stored_once_after_drafts`

#### Scenario: Drafts finish
- **WHEN** both 2027 drafts become complete
- **THEN** the next sync stores the 2027 ADP, and later syncs leave it unchanged

### Requirement: 6.2.10.1 ADP failure
A failed ADP fetch SHALL leave the season's ADP unstored, with a warning naming the season, while the sync and the cold run carry on.

**Traces to:** 6.2.10; 5.5.4
**Verified by:** Test: `tests/test_sync.py::test_adp_failure_only_warns`

#### Scenario: Retry next run
- **WHEN** the 2027 ADP request fails
- **THEN** a warning names 2027, the run continues and the next sync tries again
