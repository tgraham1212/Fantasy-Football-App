# Tasks

Every spec task below means: rewrite the spec in `openspec/specs/<spec>/spec.md` to the standard against all 13 review findings (design.md, Context), giving each requirement its ID under its primary parent (design.md decision 12), then stop with a summary for the owner:
- requirements split, rewritten, added or cut, with their IDs;
- orphans, each with a proposed need or a cut;
- TBRs and verification gaps;
- any behavior fix needed.

Redraw the requirements diagrams (`python -X utf8 tools/requirements_diagram.py`) and include them in the summary. After the owner approves, record the approval as the spec's standard review in `openspec/inspection-checklist.md` (date and result), add any Inspection-verified requirements with their criteria, remove the spec's entries from `tests/baselines/requirements.json`, and commit. Verify: `tests/test_requirements.py` reports no findings for the spec, and `openspec validate --specs --strict` passes.

## 1. Foundation

- [x] 1.1 Confirm `refresh-modes` is archived with spec sync, then copy `openspec/specs/` to `openspec/specs-archive/pre-requirements-standard/` and tag the commit `specs-before-requirements-standard`. Verify: the folder matches `openspec/specs/` file for file, and `git tag --list` shows the tag
- [x] 1.2 Owner review of the twelve needs in this change's `specs/needs/spec.md`; revise until approved. Verify: owner approval recorded in the commit message
- [x] 1.3 Sync the needs delta to `openspec/specs/needs/spec.md` (`openspec-sync-specs`, narrowed to the needs delta). Verify: `openspec validate --specs --strict`
- [x] 1.4 Write `openspec/glossary.md`: project terms (Forecast, Forecast of record, Projection, as-of week, slate, FLEX, replacement level, residual, roster drift, live bundle, hot run, cold run and others found during the rewrite), the nomenclature rules and the Banned Terms list. Verify: every banned term from design.md decision 5 is listed
- [x] 1.5 Write `tests/test_requirements.py` (design.md decisions 2 and 5), with the test functions the `project-standards` delta names. Generate `tests/baselines/requirements.json` and `tests/baselines/requirements_open.json` from today's specs. Verify: the test passes against the baselines; fixture specs in the test cover an orphan, a cycle, two parents, four parents, a childless need, two SHALLs, SHALL NOT, a banned term, a missing test reference, a TBR, a duplicate ID, an ID that does not match its primary parent, and a reused retired ID
- [x] 1.6 Write `openspec/inspection-checklist.md` with its two tables (design.md decision 10), empty of reviews. The check's review-date rule applies only to specs already brought to the standard (listed in the baseline as not yet reviewed until then). Verify: `tests/test_requirements.py::test_inspection_checklist_covers_every_inspection` and `::test_every_spec_has_a_dated_review`
- [x] 1.6a Write `openspec/retired-requirements.md` (ID, name, date, reason), empty. Verify: `tests/test_requirements.py::test_retired_ids_are_not_reused`
- [x] 1.7 Write `tools/requirements_impact.py` (design.md decision 11). Verify: `tests/test_requirements.py::test_impact_report_lists_ancestors_and_descendants` on fixture specs with two parents and three levels, called by ID
- [x] 1.7a Write `tools/requirements_diagram.py` (design.md decision 13) from the mock-ups in `mockups/`, and `docs/requirements.md` (the standard, IDs, how to read the diagrams, Keeping This Document Current). Register the doc in `tests/test_feature_docs.py` with `openspec/specs/` as its code, and extend the currency check to generators with several outputs. Verify: `tests/test_feature_docs.py` passes, and the overview shows the twelve needs
- [x] 1.8 Add the requirements standard to the `openspec/config.yaml` context and a tasks rule, and summarise it in `CLAUDE.md`. Move the nomenclature rules' detail to the glossary and point to it. The tasks rule also tells authors to run the impact report before editing a requirement. Verify: `openspec instructions tasks` shows the rule, and the config parses

## 2. Worked Example

- [ ] 2.1 Playoff-size check (design.md decision 7) and `tests/test_simulate.py::test_unsupported_playoff_size_fails_loudly`. Add the six-team constraint to `docs/simulation.md`, step 5. Verify: the test, and `tests/test_feature_docs.py`
- [ ] 2.2 `playoff-odds-simulation`: fix the roster-drift statement (a random walk, per `Calculations.txt` section 6) and bring the spec to the standard, numbering it under need 1. Give "Supported playoff size" its ID under the bracket simulation requirement, in both the main spec and this change's delta (heading and Traces to), and close its TBR. Owner review, then commit

## 3. Site Page Specs

- [ ] 3.1 `league-odds-site`
- [ ] 3.2 `games-page`
- [ ] 3.3 `positional-rankings-page`
- [ ] 3.4 `war-leaderboard-page`
- [ ] 3.5 `manager-pages`

## 4. Model and Calculation Specs

- [ ] 4.1 `game-predictions`
- [ ] 4.2 `live-scoring`
- [ ] 4.3 `win-probability-added`
- [ ] 4.4 `game-card-states`
- [ ] 4.5 `odds-calibration`
- [ ] 4.6 `player-war`
- [ ] 4.7 `positional-rankings`
- [ ] 4.8 `replacement-level`
- [ ] 4.9 `manager-history`
- [ ] 4.10 `manager-ratings`
- [ ] 4.11 `team-news`

## 5. Refresh Specs

- [ ] 5.1 `site-updates`
- [ ] 5.2 `refresh-scheduling`
- [ ] 5.3 `live-refresh`
- [ ] 5.4 `manual-refresh`

## 6. Data Specs

- [ ] 6.1 `data-storage-tiers`
- [ ] 6.2 `sleeper-league-sync`
- [ ] 6.3 `nfl-schedule`
- [ ] 6.4 `player-projections`
- [ ] 6.5 `player-stats`
- [ ] 6.6 `injury-history`
- [ ] 6.7 `start-percentage-snapshots`

## 7. Project Specs

- [ ] 7.1 `calculation-docs`
- [ ] 7.2 `site-copy`
- [ ] 7.3 `layout-checks`
- [ ] 7.4 `project-standards`, including its new requirements from this change's delta
- [ ] 7.5 `needs`: revise any need the orphans showed was missing, and confirm every need has children. Owner review

## 8. Close-Out

- [ ] 8.0 Numbering sweep: give an ID to every requirement left unnumbered because its primary parent was rewritten later. Verify: `tests/test_requirements.py::test_ids_follow_the_primary_parent` has no baseline entries
- [ ] 8.1 `tests/baselines/requirements.json` is empty; `requirements_open.json` lists only the TBRs and verification gaps the owner accepted. Verify: the full test suite and `openspec validate --specs --strict`
- [ ] 8.1a Final requirements diagrams: every requirement numbered and placed. Verify: the overview shows no unnumbered requirements, and `tests/test_feature_docs.py` passes
- [ ] 8.2 Report the open-items list to the owner: each TBR and gap with its target. Verify: the owner has seen it

## Workflow follow-up

- Archive with spec sync when the owner asks (syncs the `project-standards` and `playoff-odds-simulation` deltas).
