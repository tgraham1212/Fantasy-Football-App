# Tasks

## 1. History Records and History WAR

- [x] 1.1 In a new `src/ffapp/pick_values.py`, add `HistoryStore(Store)` rooted at `data/history/`:
  - `read_crosswalk` returns the real crosswalk;
  - `read_season("dynasty", s)` returns a synthetic `SeasonData` from the latest dynasty `league.json` (season set, complete, `last_scored_leg` 14, no rosters);
  - `espn_weeks` returns empty.

  Verify with `test_history_records_apart` in a new `tests/test_pick_values.py`: the error pools and stats season walks are unchanged with history files present (4.12.2.1).
- [x] 1.2 The slimmer for history stat records (name, position, team, played fields, and the stat keys the dynasty scoring weights or `war.STAT_KEYS` reads). Verify points and WAR are equal for slimmed and full records on a fixture week.
- [x] 1.3 The `history-fetch` command in `src/ffapp/cli.py`: Sleeper stats for 2013–2021 weeks 1–14 via `stats.fetch_week`, slimmed, into `data/history/stats/`, and ESPN season snapshots via `slim_snapshot(espn.players(s))` into `data/history/espn/`. It skips present files and is never part of a cold run. Verify with fixtures and `test_commands_not_in_cold_runs` (checks `refresh.yml` and `hot.yml`).
- [x] 1.4 The history-only matching fallback (normalised name + position among the season's stat lines) for ESPN Players `match()` leaves unmatched. Verify with a fixture holding a retired Player missing from the crosswalk.
- [x] 1.5 History WAR: `build_war(HistoryStore, config, "dynasty", s)` in memory. Verify with `test_history_war_matches_stored_war`: the history path run on a 2023 copy equals stored `data/war/dynasty/2023.json` to 0.0001 (4.12.2).

## 2. Rookie Order

- [x] 2.1 A new `src/ffapp/mizelle.py`:
  - `rookie-adp-fetch` downloads `mizelle.net/mfl/<year>/` for 2013–2021 into `.cache/third-party/mizelle/<year>.html`, 2 s apart, skipping present files;
  - the `playerArr` parser handles `var`, `const` and `let`;
  - add `.cache/` to `.gitignore`.

  Verify with `test_third_party_cache_not_committed` (gitignore entry, nothing under `.cache/` tracked) and a parser test on a trimmed fixture page (4.12.1.2).
- [x] 2.2 The DLF rookie order: `status` "R", QB/RB/WR/TE, mean May–August pick, ties by lower MFL id, top 36 to slots; MFL to Sleeper through DynastyProcess `db_playerids.csv` (GPL-3.0), downloaded by `rookie-adp-fetch` into the same local cache and never committed. Unmapped rookies keep their slot and are flagged. Verify with `test_dlf_rookie_order` (4.12.1.1).
- [x] 2.3 League rookie orders for 2022 onward from stored drafts (2022: startup rookies in pick order). Verify with `test_rookie_order_sources` (4.12.1).
- [x] 2.4 `rookie-adp-fetch` writes the committed record `data/pick-values/rookie-order.json`: each 2013–2021 class's slots with Sleeper id, name, position, mean pick and flagged rookies. Verify with `test_rookie_order_record`: the model built with the cache removed equals the model built with it (4.12.1.3).

## 3. Model, Unused Picks and Record

- [x] 3.1 Group values: Early/Middle/Late per round; per-season means over classes that reached the season; the 8-season sum; the 80% bootstrap range (2,000 draws, fixed seed). Verify with `test_pick_groups` and `test_eight_season_value` (4.12.3, 4.12.3.1).
- [x] 3.2 Pool-adjacent-violators over the nine groups in pick order, keeping measured values beside model values. Verify with `test_values_never_rise` (round 2 example to −0.75) (4.12.3.2).
- [x] 3.3 The `pick-values` command reads only committed records and writes `data/pick-values/model.json`: model and measured values, ranges, per-group per-season means, per-slot means, n, sources, flagged rookies and `built_at`. Cold runs only read it. Add `data/history/` and `data/pick-values/` to `docs/refresh-modes.md`. Verify with `test_model_values`, `test_model_record_not_rewritten` and `pytest tests/test_storage_tiers.py` (4.12, 4.12.5, 6.1).
- [x] 3.4 `pick_value(season, round, original_roster, as_of)` with basis `slot` / `forecast` / `round_average`; the Forecast order by (playoff, semifinal, final, title shares, projected wins) ascending. Verify with `test_unused_pick_value` and `test_next_draft_from_forecast` (4.12.4, 4.12.4.1).
- [x] 3.5 Run the fetches and the `pick-values` command locally. Report to the owner the nine model values with ranges and n, and the flagged rookies, and confirm they match the explore curves (1st Early +3.38) before the page goes live.

## 4. Export and Page

- [x] 4.1 Export `site/data/pick-values.json` in `src/ffapp/export.py` from the record. Absent record means no file and the export carries on. Run `python -m ffapp build`. Verify with `test_export_writes_pick_values_file` (4.12.6).
- [x] 4.2 `site/pick-values.html` and `site/pick-values.js` (`?v=__BUILD__`), built like `calibration.html`. Add the link "How Pick Values Work" on the league pages' header line (copy ID). Verify with `test_page_is_titled_and_linked` in a new `tests/layout/test_pick_values_page.py` (8.3).
- [x] 4.3 The group table (slots, measured value with 80% range, picks, model value). Verify with `test_group_table` (8.3.1).
- [x] 4.4 The three charts (total WAR by season per group, WAR per season by round, mean WAR by slot) with legends, hover values and table views. Add round colours as tokens (hex with OKLCH notes, both modes) and their contrast pairs in `tests/test_colour_contrast.py`. Register any new controls in `tests/layout/controls.py`. Verify with `test_charts_and_table_views` (8.3.2).
- [x] 4.5 The method section with copy IDs, crediting Dynasty League Football and mizelle.net; the "not built" message; then `python -X utf8 -m ffapp site-copy`. Ask the owner before `--apply`. Verify with `test_method_and_credits`, `test_not_built_message` and `pytest tests/test_site_copy.py` (8.3.3, 8.3.5).
- [x] 4.6 Phone layout. Verify with `test_phone_widths` at 360, 390, 414 and 440 px, and the layout check in Chromium, WebKit and Firefox with axe-core clean in both modes (8.3.4).

## 5. Docs

- [x] 5.1 `Calculations.txt` section 27 "Rookie Pick Values" (rookie order, history WAR, 8-season value, groups, never-rising rule, unused-pick value). Register `pick_values.py` in `tests/test_calculations_doc.py`. Add the glossary terms Pick value and Pick group. Verify with `pytest tests/test_calculations_doc.py tests/test_requirements.py`.
- [x] 5.2 Write `docs/pick-values.md` and `tools/pick_values_diagram.py`, and register them in `tests/test_feature_docs.py` for `src/ffapp/pick_values.py` and `site/pick-values.js`. Verify with `pytest tests/test_feature_docs.py`.

## 6. Requirements and Final Checks

- [x] 6.1 Run `python -X utf8 tools/requirements_impact.py 6.1` and cover what it lists (6.1.5 offline build: the export reads only the committed model; 6.1.7: `docs/refresh-modes.md` lists the new paths). Redraw the requirement diagrams. Confirm `pytest tests/test_requirements.py` reports no findings for 4.12.x and 8.3.x.
- [x] 6.2 Run the full suite and a local build, then check the page in the browser at 1280 and 360 px against the curves artifact.

## Workflow follow-up

- At archive: sync the specs, add standard reviews for `rookie-pick-values` and `pick-values-page`, and redo `data-storage-tiers` (owner's approval).
- Commit, push and archive only when the owner asks.
