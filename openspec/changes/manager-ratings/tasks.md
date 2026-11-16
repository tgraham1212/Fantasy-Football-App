# Tasks

## 1. Dependency and config

- [x] 1.1 Add `openskill>=6.2,<7` to `pyproject.toml` dependencies and verify `pip install -e ".[dev]"` then `python -c "from openskill.models import PlackettLuce"` succeed
- [x] 1.2 Add `RatingsConfig` (`revert`, `early_k`, `start_mu`, `start_sigma`, `ewma_weight`) with defaults and validation to `src/ffapp/config.py`, parsed from an optional `ratings` block, and verify new tests in `tests/test_config.py` cover the defaults, each rejected value and unknown keys
- [x] 1.3 Document the `ratings` block with its defaults and the reasoning (anchor to 1000, taper) as a commented example in `config/leagues.yaml` and verify `python -m ffapp sync --help` still loads the config without error

## 2. Rating engine

- [x] 2.1 Create `src/ffapp/ratings.py` with `weekly_results(store, league_key)` yielding `(season, week, {manager_id: points})` for scored regular-season weeks only, mapping rosters to owner user IDs and vacant entries, and verify tests on a fixture store skip playoff weeks, skip all-zero weeks and produce a vacant id for an ownerless roster
- [x] 2.2 Implement the Openskill update for one week (single-player teams, `scores=`), the preseason reversion toward 1000, and the early-season multiplier on the mean delta, and verify tests show a higher score raises `mu`, 1300 reverts to 1200, 700 to 800, week 1 doubles the model's delta and week 5 does not
- [x] 2.3 Implement weekly z (sample sd), career mean z, season-to-date z, EWMA z and the fresh-start rating, and verify tests reproduce the spec's 1.0 and 0.17 examples and that season-to-date z resets while career z does not
- [x] 2.4 Implement `build_ratings(store, config, league_key)` returning the file payload (parameters, seasons, managers with display names, current/vacant flags and ordered history) and `write_ratings` to `data/ratings/<league>.json`, and verify tests show every rated week present for every participant, current/former flags set by the latest season, and two runs identical apart from `generated_at`
- [x] 2.5 Add the `ratings` CLI command and insert a `ratings` step after `stats` in `cmd_refresh`, and verify `tests/test_refresh.py` lists the step in order and `python -m ffapp ratings` writes both league files from the real store

## 3. Export

- [x] 3.1 Populate `elo` and `elo_change` per current team from the rating file and add the `ratings` block (league-wide week list, per-manager `mu` and `career_z` series aligned with nulls, display name, current flag, roster_id for current members, vacant entries dropped), and verify `tests/test_export.py` checks the values, the alignment and a newcomer's null change
- [x] 3.2 Keep the export working without a rating file (null ELO fields, no `ratings` block) and verify a test on a store with no ratings directory passes and the real `python -m ffapp export` succeeds

## 4. Site: table and palette

- [x] 4.1 Make the ELO and 1-week change headers sortable in `site/app.js` (rating, signed change; unrated teams last) and render the values, and verify in the browser that one click sorts descending with the fill and arrow, and that the existing change pills render green and red
- [x] 4.2 Add a `--greys` mode to `tools/team_palette.py` producing six `--former-N` tokens per theme, run the dataviz validator on each grey set against its surface for the normal-vision floor and contrast, and add the tokens to the light, dark-preference and forced-dark blocks of `site/styles.css`; verify the validator output is recorded in the commit message or a comment in the tool

## 5. Site: rating chart

- [x] 5.1 Add the rating chart card to `site/index.html` (title, metric pills Rating | Z-score, range pills This season | Last 3 seasons | All time, canvas, hint) under the odds chart and verify it is hidden with a "ratings not yet available" note when the league file has no `ratings` block
- [x] 5.2 Render the chart in `site/app.js` from the exported series: current members in their team colour, former members in `--former-N`, direct labels, shared highlight with the table and odds chart, season-start tick labels and boundary grid lines, zero reference line on the z-score metric; verify by loading the dynasty page and checking 12 coloured and 5 grey lines with labels
- [x] 5.3 Implement the range switch by slicing the week list and verify "This season" shows only 2026 weeks and "Last 3 seasons" shows 2024–2026 on redraft, with colours unchanged
- [x] 5.4 Check both themes and the 375px harness for the new card (no horizontal page scroll, pills wrap) and verify with headless screenshots of light and dark modes

## 6. Integration

- [x] 6.1 Run `python -m ffapp refresh` end to end locally, then `pytest`, and verify the rating files, site data and all tests pass with no warnings from `openspec validate --change manager-ratings`
- [x] 6.2 Update the roadmap memory note and the hint text on the league page to state that ratings use end-of-season owners and regular-season weeks only, and verify the hint renders under the chart

## Workflow follow-up

- Commit, fetch and push; regenerate derived files if the daily refresh has committed since.
- Archive the change with spec sync after the user confirms the deployed site.
