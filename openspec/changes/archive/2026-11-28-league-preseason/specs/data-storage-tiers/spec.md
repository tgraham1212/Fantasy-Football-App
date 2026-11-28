## MODIFIED Requirements

### Requirement: 6.1 Records committed
Git SHALL hold the records: league data, drafts and transactions; stats for played weeks, injury statuses, Player details, trending, ADP and ESPN snapshots; nflverse injury reports; current and earlier weeks' Projections; as-of, slate and preseason Forecasts; each game file's log and Forecast of record; the NFL schedule; and the calibration report.

**Traces to:** 6
**Verified by:** Test: `tests/test_storage_tiers.py::test_every_data_folder_is_listed_in_the_document`

#### Scenario: Fresh clone
- **WHEN** someone clones the repository
- **THEN** every record listed is in it
