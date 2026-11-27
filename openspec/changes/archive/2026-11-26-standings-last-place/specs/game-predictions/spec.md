## MODIFIED Requirements

### Requirement: 2.7.3 Live week views
During the live week, the Actual view SHALL be simulated from the starters each Manager set, locked starters at their results and the others at their latest Projections with no free-agent fills, while the Model view stays the model lineup at frozen pre-kickoff projections.

**Rationale:** The Actual view shows the Manager's own lineup (2.7.2); free-agent fills and the model's picks belong to the Model view.
**Traces to:** 2.7
**Verified by:** Test: `tests/test_live.py::test_live_forecast_rows_and_log_keep_pre_kickoff_projections`; Test: `tests/test_views.py::test_live_actual_view_uses_set_starters`

#### Scenario: Saturday of week 11
- **WHEN** a visitor opens week 11 on Saturday
- **THEN** the Actual view shows the live probabilities and the Model view the model's pre-kickoff Forecast

#### Scenario: Starter projected below replacement level
- **WHEN** a Manager starts a quarterback projected 12.0 and the quarterback replacement level is 14.2
- **THEN** the Actual view shows that quarterback at 12.0 and no free agent

#### Scenario: Better-projected Player left on the bench
- **WHEN** a Manager benches a receiver projected 11.4 and starts one projected 9.0 whose game has not kicked off
- **THEN** the Actual view has the 9.0 receiver in that slot and the Model view marks the 11.4 receiver benched
