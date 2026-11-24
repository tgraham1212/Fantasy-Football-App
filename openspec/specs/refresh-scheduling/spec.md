# refresh-scheduling Specification

## Purpose

When the data is refreshed: the three refresh modes and how the relay's Worker moves between them, the hot and cold run cadence in each, the run after each slate, what a cold run does, and the deploy after a code push. It delivers need 5, Current Data; how it all fits together is in `docs/refresh-modes.md`.

## Requirements

### Requirement: 5.1 Refresh modes
The refresh SHALL always be in exactly one of three modes: Off-season, when both leagues' seasons are over and the NFL's week 1 has not begun; Live, when an NFL game has kicked off and is not final; and Quiet, any other time in season.

**Traces to:** 5
**Verified by:** Test: `tests/test_relay.py::test_modes_follow_the_games`

#### Scenario: Sunday afternoon
- **WHEN** the 1:00 pm games are in progress
- **THEN** the mode is Live

#### Scenario: March
- **WHEN** both leagues' championship weeks were scored in January
- **THEN** the mode is Off-season

### Requirement: 5.1.1 Worker clock
The relay's Worker SHALL work out the mode once a minute and start the runs that mode makes due.

**Traces to:** 5.1
**Verified by:** Test: `tests/test_relay.py::test_live_cadence`; Inspection: `relay/wrangler.toml`, the cron trigger runs every minute

#### Scenario: Each minute
- **WHEN** the Worker's clock fires
- **THEN** it decides the mode and starts any run that is due

### Requirement: 5.1.2 Mode transitions
The mode SHALL change from Off-season to Quiet when Sleeper reports the season's week 1, from Quiet to Live when a game's kickoff passes, from Live to Quiet when every game that kicked off is final, and from Quiet to Off-season when both leagues' championship weeks are scored.

**Traces to:** 5.1
**Verified by:** Test: `tests/test_relay.py::test_modes_follow_the_games`

#### Scenario: Kickoff
- **WHEN** the clock runs at 1:00 pm with 1:00 pm games scheduled
- **THEN** the mode becomes Live and a hot run starts

#### Scenario: Last game final
- **WHEN** the latest bundle shows the Sunday night game final and no other game in progress
- **THEN** the mode becomes Quiet

### Requirement: 5.1.2.1 Inputs to the mode
The Worker SHALL decide the mode from the schedule summary the cold run stores in KV and the game states in the latest live bundle.

**Traces to:** 5.1.2
**Verified by:** Test: `tests/test_relay.py::test_schedule_summary_stored`; Test: `tests/test_schedule_summary.py::test_summary_lists_this_and_next_weeks_games`

#### Scenario: Next kickoff known
- **WHEN** the stored schedule summary lists Thursday's 8:15 pm kickoff
- **THEN** the Worker switches to Live at 8:15 pm

### Requirement: 5.1.2.2 Stuck game status
A game not seen final 6 hours after its kickoff SHALL count as final.

**Rationale:** A missed final status would otherwise keep the mode Live for days.
**Traces to:** 5.1.2
**Verified by:** Test: `tests/test_relay.py::test_stuck_game_counts_as_final_after_six_hours`

#### Scenario: Stuck status
- **WHEN** a game kicked off 6 hours ago and no bundle has shown it final
- **THEN** it counts as final for the mode

### Requirement: 5.1.3 Live cadence
In Live, a hot run SHALL start each minute when none is queued or running, and a cold run every 15 minutes.

**Rationale:** Back-to-back hot runs keep the data within 2 minutes of Sleeper (need 5).
**Traces to:** 5.1
**Verified by:** Test: `tests/test_relay.py::test_live_cadence`

#### Scenario: Back-to-back hot runs
- **WHEN** a hot run finishes 70 seconds after it started during Live
- **THEN** the next minute's clock starts another hot run

### Requirement: 5.1.4 Quiet cadence
In Quiet, hot and cold runs SHALL each start every 15 minutes.

**Traces to:** 5.1
**Verified by:** Test: `tests/test_relay.py::test_quiet_cadence`

#### Scenario: Wednesday in season
- **WHEN** no game is in progress on a Wednesday in week 11
- **THEN** a hot run and a cold run start every 15 minutes

### Requirement: 5.1.5 Off-season cadence
In the off-season, the Worker SHALL start no runs, leaving the daily scheduled cold run.

**Traces to:** 5.1
**Verified by:** Test: `tests/test_relay.py::test_offseason_clock_starts_nothing`

#### Scenario: March
- **WHEN** the Worker's clock fires in March
- **THEN** it starts nothing

### Requirement: 5.1.6 Daily fallback
GitHub's schedule SHALL start a cold run daily at 11:00 UTC in every mode.

**Rationale:** The site still refreshes daily if the Worker stops.
**Traces to:** 5.1; 5
**Verified by:** Test: `tests/test_workflows.py::test_cold_run_has_no_gate_or_test_suite_and_deploys_on_change`

#### Scenario: Worker down
- **WHEN** the Worker's clock has not run for a day
- **THEN** the 11:00 UTC cold run still starts from GitHub's schedule

### Requirement: 5.1.7 Slate-final run
When every game of a slate is final, the Worker SHALL start one cold run in slate mode, which stores the slate Forecast.

**Traces to:** 5.1; 1.2.5
**Verified by:** Test: `tests/test_relay.py::test_final_slate_starts_one_cold_run`

#### Scenario: Early games end
- **WHEN** the last 1:00 pm game goes final while the 4:05 pm games are in progress
- **THEN** one cold run starts and stores the Forecast as of the end of the 1:00 pm slate

### Requirement: 5.1.8 Refresh modes document
`docs/refresh-modes.md`, linked from the README, SHALL show the diagram, the modes, transitions and cadences, the steps of a hot and a cold run, the data tiers, the limits and budgets, and what happens on failure.

**Traces to:** 5.1; 10.13
**Verified by:** Test: `tests/test_feature_docs.py::test_doc_structure`; Inspection: `docs/refresh-modes.md` holds each listed part

#### Scenario: Reading the README
- **WHEN** a reader follows the README's refresh section
- **THEN** it links to `docs/refresh-modes.md`, which shows the diagram and every mode, transition, run step and data tier

### Requirement: 5.1.8.1 Refresh modes diagram
The diagram `docs/images/refresh-modes/diagram.svg` SHALL be drawn by `tools/refresh_modes_diagram.py` and match what it draws.

**Traces to:** 5.1.8
**Verified by:** Test: `tests/test_feature_docs.py::test_diagrams_are_generated_and_current`

#### Scenario: Cadence changed
- **WHEN** the Quiet cadence changes from 15 to 10 minutes
- **THEN** the document and the generator change together and the diagram is redrawn

### Requirement: 5.5 Cold run
Each cold run SHALL update the league data, Projections, stats, NFL schedule, injury statuses and start-percentage snapshot, then rebuild the ratings, replacement levels, WAR, the as-of Forecast, and the game logs and records.

**Rationale:** What is committed and deployed is in `data-storage-tiers`.
**Traces to:** 5; 6
**Verified by:** Test: `tests/test_refresh.py::test_refresh_runs_every_step_when_sources_work`; Test: `tests/test_refresh.py::test_refresh_steps_in_order`

#### Scenario: Day after Monday night
- **WHEN** a cold run happens the day after Monday night's game ends and week 10 is final in Sleeper
- **THEN** the published site shows the Forecast as of week 10

### Requirement: 5.5.1 Started by hand
The cold run SHALL be startable by hand from GitHub.

**Traces to:** 5.5
**Verified by:** Inspection: `.github/workflows/refresh.yml` has a `workflow_dispatch` trigger

#### Scenario: Manual run
- **WHEN** the maintainer starts the refresh workflow from GitHub
- **THEN** a cold run runs

### Requirement: 5.5.2 Live cold runs
A cold run in Live SHALL skip the simulation, which the hot runs own.

**Traces to:** 5.5; 5.2
**Verified by:** Test: `tests/test_refresh.py::test_live_mode_skips_the_simulation`

#### Scenario: Sunday cold run
- **WHEN** a cold run happens during the 1:00 pm games
- **THEN** it syncs and rebuilds everything except the simulation

### Requirement: 5.5.3 Failed step
A failed required step SHALL stop the cold run before it commits or deploys, leaving the stored data and the published site unchanged and the run marked failed.

**Traces to:** 5.5; 6
**Verified by:** Test: `tests/test_refresh.py::test_refresh_stops_at_projections_failure_and_leaves_data_unchanged`; Test: `tests/test_refresh.py::test_war_failure_stops_the_refresh`

#### Scenario: Failed refresh
- **WHEN** the projections step fails
- **THEN** the published site stays online unchanged, nothing is committed, and the run is marked failed

### Requirement: 5.5.4 Optional steps
A failed snapshot, schedule or trending step SHALL let the cold run carry on with the data already stored, ending with a warning naming the step, shown as an annotation on the run.

**Traces to:** 5.5
**Verified by:** Test: `tests/test_refresh.py::test_refresh_continues_past_a_snapshot_failure_with_a_warning`; Test: `tests/test_refresh.py::test_schedule_failure_continues_with_a_warning_and_games_failure_stops`

#### Scenario: ESPN unavailable
- **WHEN** the snapshot capture fails during a cold run
- **THEN** the remaining steps run with the snapshots already stored, the Forecasts are still refreshed and published, and the run ends with a warning naming the snapshot step

### Requirement: 5.6 Deploy on code push
A push to main that changes site code SHALL build the site data from the latest build cache or offline, run the tests and the layout check, and deploy the site only when they pass.

**Traces to:** 5; 10
**Verified by:** Test: `tests/test_site_files.py::test_every_deploy_stamps_through_the_shared_command`; Inspection: `.github/workflows/site.yml`, the build, test and deploy steps

#### Scenario: Code pushed
- **WHEN** a commit changing the Games page script is pushed
- **THEN** the site deploys with it after the tests pass, without waiting for the next refresh

### Requirement: 5.6.1 Deploys never overlap a cold run
The code-push deploy SHALL share the cold run's concurrency group, so the two never run at once.

**Traces to:** 5.6
**Verified by:** Inspection: `.github/workflows/site.yml` and `.github/workflows/refresh.yml` share the `refresh-odds` concurrency group

#### Scenario: Push during a cold run
- **WHEN** code is pushed while a cold run is deploying
- **THEN** the code deploy waits for the cold run to finish

### Requirement: 5.6.2 Data pushes deploy nothing
A push that changes only data SHALL start no code-push deploy.

**Traces to:** 5.6
**Verified by:** Inspection: `.github/workflows/site.yml`, its path filter excludes the data folders

#### Scenario: Data-only push
- **WHEN** the cold run pushes its data commit
- **THEN** no code-push deploy runs
