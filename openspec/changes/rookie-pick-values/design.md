# Design

## Context

See proposal.md (Why). Current state the design builds on, from the 2026-11-28 explore spikes, all run in the scratchpad:

- **Player WAR (`src/ffapp/war.py`):**
  - **Entry point:** `build_war(store, config, league_key, season)` reads a `SeasonData` (league settings, rosters), the stored weekly stats, the ESPN season snapshot and the crosswalk.
  - **Cut:** every finished season uses the **yearly cut**: one season-long start-percentage ranking. Only 2026, still in progress, uses the merged cut.
  - **Rosters:** these only set owner attribution, not WAR.
- **The spike:** a scratch `Store` laid out like `data/` held:
  - Sleeper stats fetched with `stats.fetch_week` and `upsert_week`;
  - ESPN `slim_snapshot(espn.players(season))`;
  - a copy of the dynasty 2026 `league.json` with the season changed.

  Run unchanged through `build_war`, it reproduced the stored WAR for 2022–2025 exactly: 571 of 571 Players, correlation 1.0000, largest difference 0.00.
- **History availability:**
  - Sleeper weekly stats exist back to 2012.
  - ESPN season start percentages exist back to 2013 (2013: 3,314 Players, 563 started).
  - ESPN-to-Sleeper matching left 9 Players unmatched in 2013 (Tony Gonzalez among them), 3 in 2015, and none in other seasons.
- **League settings:** the dynasty league's scoring, lineup (QB/2RB/2WR/TE/FLEX/DEF), 12 teams and playoff start (week 15) are identical across 2022–2026.
- **mizelle.net:**
  - **Pages:** `mizelle.net/mfl/<year>/` embeds `playerArr` (`var` or `const`): each Player with `status` ("R" = rookie), `position`, the MFL `id`, and `stats.<month>.picks`, the pick numbers in each month's DLF mock drafts.
  - **Coverage:** 2013–2026, 50–71 rookies with post-draft picks per year, and nearly every top-36 rookie maps to Sleeper.
  - **Busts kept:** the pages were built at the time, so later busts are still present (2016: Treadwell, Doctson).
  - **Access:** the site has no robots.txt and posts no terms.
- **ID map:** DynastyProcess `db_playerids.csv` (GPL-3.0) maps `mfl_id` to `sleeper_id`. It's needed only to build the model, so it stays in the local cache.
- **Curves (published as the scratch artifact "Rookie Pick Value Curves"):** 465 picks from the 2013–2025 classes. First-round WAR per season peaks in season 3 (+0.36) and is −0.04 by season 8.

## Goals / Non-Goals

**Goals:**
- One pick value model, reproducible from committed records alone, and written as a record that cold runs only read. The local cache is needed only once, to make the 2013–2021 rookie order record.
- History WAR identical in method to league WAR, without touching `war.py`'s behaviour for league seasons.
- No third-party page in git, and no third-party request in any automated run.

**Non-Goals:**
- No change to league-season WAR, the Draft tab's slot WAR or its grades. The Draft tab may adopt pick values later.
- No FantasyPros data. The key stays set up for a later look at dynasty market values.
- No redraft pick values. Redraft picks in trades use the Draft tab's slot WAR (`league-trades`).
- No per-slot model values: single slots are too noisy (1.03 at +0.57 against 1.04 at +1.24 through 3 seasons).

## Decisions

1. **History store.**
   - **Layout:** a `HistoryStore(Store)` rooted at `data/history/`, so its stats and ESPN paths are `data/history/stats/<s>/week_NN.json` and `data/history/espn/<s>/season.json`.
   - **Overrides:**
     - `read_crosswalk` returns the real `data/espn/crosswalk.json`.
     - `read_season("dynasty", s)` returns a synthetic `SeasonData`: the dynasty league's latest `league.json` with `season = s`, `status = "complete"` and `last_scored_leg = 14`, and no rosters or matchups.
     - `espn_weeks` is empty, which forces the yearly cut.
   - **Result:** `build_war` runs unchanged, and anything that walks `data/stats/` (error pools, replacement levels, calibration) never sees history seasons.
   - **Alternative:** add 2013–2020 to `data/stats/`. Rejected: it silently widens the error pools and other season walks.
2. **Slimmed history stats.**
   - **What's kept:** each record keeps `player_id`, the name fields, `position`, `fantasy_positions`, `team`, `gp`/`gms_active` (for `played`), and only the stat keys the dynasty scoring settings weight or `STAT_KEYS` reads.
   - **Size:** about 1 MB a season, against 4.4 MB unslimmed. A test checks that slimmed records give the same points and WAR as full ones on a sample week.
3. **History WAR is not stored.** It's computed in memory by the `pick-values` command. Only the model it feeds is a record. This keeps `data/war/` holding league seasons only.
4. **Matching fallback for retired Players.** Where `match()` leaves an ESPN Player unmatched, a fallback matches on normalised name (the `preseason.norm_name` rule) and position among that season's stat lines. That recovers Gonzalez-type misses in 2013 and 2015. It applies to the history store only, so league WAR is unchanged.
5. **Rookie order.**
   - **2013–2021:** rookies (`status` "R", QB/RB/WR/TE) with any May–August picks, ranked by mean pick; ties broken by the lower MFL id. The top 36 become slots 1.01–3.12, and MFL id maps to Sleeper id.
   - **Unmapped rookies:** a rookie with no Sleeper id keeps his slot and counts 0 WAR, flagged in the record (three in 2013–2014). Dropping him would shift every later slot.
   - **2022 onward:** this league's drafts from `data/leagues/dynasty/<s>/draft.json`. 2022 uses the startup draft's `years_exp` = 0 Players in pick order (33 of them, so 3.10–3.12 are empty for 2022).
6. **Model.**
   - **Season means:** for each group and season k = 1..8, the mean WAR over the picks whose class has reached season k (class + k − 1 ≤ the last finished season). The group value is the sum of those means.
   - **80% range:** bootstrap the mean within each season, 2,000 draws, seed fixed.
   - **Never-rising rule:** pool-adjacent-violators over the nine groups in pick order, equal weights. Measured values are kept beside model values.
   - **The model is fixed until rebuilt.** A rebuild uses the newest finished season, run by hand after each season, and changes the values a little each year.
7. **Unused pick value.**
   - **Lookup:** `pick_value(season, round, original_roster, as_of)` returns `{value, group, basis}`, with basis one of `slot`, `forecast` or `round_average`:
     - **slot:** the draft order is set (Sleeper `slot_to_roster_id` for that season's draft).
     - **forecast:** the pick is for the next draft and the order isn't set.
     - **round_average:** any later draft.
   - **Forecast order:** from the latest as-of Forecast, teams are sorted ascending by (playoff share, semifinal share, final share, title share, projected wins). Positions 1–4 are Early, 5–8 Middle and 9–12 Late.
   - **Alternative:** expected final place from the full bracket simulation. That's more exact, but the Forecast payload doesn't carry a place distribution, and a third of the round needs only a rough order.
8. **Commands and the cache.**
   - **The commands:**
     - **`history-fetch`:** Sleeper stats (126 weeks) and ESPN season snapshots (9) into `data/history/`, skipping files already present.
     - **`rookie-adp-fetch`:** the mizelle.net pages and the DynastyProcess ID map into `.cache/third-party/` (gitignored, outside `data/` so the tier test ignores it), 2 seconds apart, skipping present files. It then writes the committed record `data/pick-values/rookie-order.json`: for each 2013–2021 class, slots 1.01–3.12 with Sleeper id, name, position and mean pick, plus flagged rookies. It runs once, since those classes never change.
     - **`pick-values`:** reads only committed records (the rookie order record, league drafts, history records, league WAR) and writes `data/pick-values/model.json` with the model values, measured values, ranges, per-group per-season means, per-slot means, n, sources and the built-at time. A test checks that it gives the same model with no cache present.
   - **Never in a cold run (for now):** none of the three is in `refresh.yml` or `hot.yml`, and a test checks that.
   - **Automation later:** `pick-values` needs no third-party page, so a later "yearly tasks" change can run it in the cold run once per season: the first run with week-1 Projections, when the model predates the last finished season. That's on the backlog.
9. **Export and page.**
   - **Export:** `site/data/pick-values.json` from the record.
   - **Page:** `site/pick-values.html` and `site/pick-values.js`, built like `calibration.html`. Charts use the site's chart tokens: three round colours from the existing categorical tokens, validated for contrast.
   - **Link:** the header line beside "How Good Are These Forecasts?".
   - **Wording:** no "projected" anywhere; the term is "pick value".
10. **Feature docs.**
    - **New:** `docs/pick-values.md` and `tools/pick_values_diagram.py`, registered for `src/ffapp/pick_values.py` and `site/pick-values.js`.
    - **Touched:** `docs/requirements.md` (its diagram is redrawn for the new specs) and `docs/refresh-modes.md` (new committed paths in "Where Data Lives").
    - **Not touched:** `docs/draft.md` and `docs/simulation.md`.

## Risks / Trade-offs

- **[mizelle.net changes or disappears]** → Nothing after the first run needs it. The rookie order record holds what was read, and rebuilds use only that.
- **[The rookie order record publishes a ranking derived from DLF]** → It holds slots and Sleeper ids, not the pages or pick data, and the page credits the source. Only the raw pages and the GPL ID map stay local.
- **[DLF order differs from this league's drafting]** → Agreement is 0.79–0.90 where both exist, and groups (not single slots) absorb most of the difference.
- **[Small samples in late seasons]** → Season 8 rests on the 2013–2018 classes (about 24 picks per group). The page shows each range and n, and values are averaged across neighbours where the order breaks.
- **[The yearly cut ranks mid-season breakouts low]** → Same as every finished league season. It moves only the replacement level and slot means.
- **[A rebuild shifts values]** → It's expected and small. The record carries `built_at`, and the page shows it.

## Migration Plan

1. Run `history-fetch` and `rookie-adp-fetch` locally, then commit the history records and the rookie order record.
2. Run `pick-values` and commit the model record.
3. Deploy. Without the record, the page says pick values haven't been built and nothing else changes, so rollback is removing the record.

## Open Questions

- Whether the Draft tab should use pick values for its draft-day view of traded picks. It's a later change and doesn't affect this design.
