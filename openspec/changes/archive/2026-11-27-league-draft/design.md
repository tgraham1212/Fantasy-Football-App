# Design

## Context

See proposal.md (Why). Current state the design builds on:

- **Sync:** `src/ffapp/sync.py` walks each league's season chain, stores complete seasons once and syncs transactions as a side fetch: once for complete seasons, every run for the current one, and a failure only warns. Each season's `league.json` already carries `draft_id`.
- **Sleeper drafts (probed 2026-11-27):**
  - `GET /v1/draft/<id>` returns settings, `slot_to_roster_id`, type (snake or linear) and status.
  - `/v1/draft/<id>/picks` returns 36 to 228 picks, each with `pick_no`, `round`, `draft_slot`, `roster_id` (who made the pick), `picked_by`, `is_keeper` and player metadata (position, team, `years_exp`).
  - `/v1/draft/<id>/traded_picks` returns the traded picks.
  - **Dynasty 2022:** the league has two drafts. `draft_id` names the 3-round rookie draft. The 19-round startup draft (the Yahoo transfer) is the other one.
  - **Redraft:** 14-round snake drafts. Keepers in 2022 to 2024 are flagged `is_keeper`.
- **ADP:** Sleeper's season projections (`{PROJECTIONS_BASE}/<season>?season_type=regular&position[]=…`) carry `adp_half_ppr` and `adp_dynasty_half_ppr` for every season back to 2021, with preseason values (2024 starts McCaffrey 1.5, Hill 2.1). Rookie-only ADP exists only for 2021.
- **WAR:**
  - `data/war/<league>/<season>.json` holds every Player's WAR, free agents included, for regular-season weeks 1 to 14.
  - Each Player has `weekly[].played` flags and `through_week`, so the games a Player played can be counted.
  - The NFL schedule in `data/nfl/` gives each team's games.
- **League tab:**
  - `site/league.js` owns the League tabs (Records, Strength of Schedule), the route and `setTab`.
  - `site/schedule.js` is the pattern for a tab in its own module with its own export file.

## Goals / Non-Goals

**Goals:**
- Store each season's draft and ADP as committed records, fetched once when final.
- Grade every pick both ways (draft day and results), plus the Managers summaries, in one export file per league built offline by `python -m ffapp build`.
- A Draft tab matching the canvas mockups, built from the site's existing patterns: segmented controls, sortable tables, the pinned first column on phones, position colours and `fitNames`.

**Non-Goals:**
- The Preseason tab, its preseason Forecast and the A to F grades (a separate later change).
- Trade trees, and showing draft picks in trade lists (the Trades tab).
- Draft grades for the dynasty startup draft, or for any draft other than the season's named draft.
- Live draft-day updates while a draft is in progress (the board shows whatever picks are stored).

## Decisions

1. **Which draft counts: the one named by `league.json` `draft_id`.**
   - This drops the dynasty startup draft without a special case and matches how Sleeper ties a draft to a season.
   - *Alternatives:* a config list of excluded draft ids, or "skip drafts over N rounds". The config list adds a setting to maintain for one historical draft. The size rule would misfire if the league ever changes its draft length.

2. **Storage.**
   - **Draft:** `data/leagues/<league>/<season>/draft.json` = `{draft, picks, traded_picks}`, as fetched.
   - **ADP:** `data/adp/<season>.json` = `{player_id: {position, adp_half_ppr, adp_dynasty_half_ppr}}`, only the fields used, values below 999.
   - **Why:** a draft is league data, so it sits beside the season. ADP is shared by both leagues, so it sits beside the other per-season shared records.
   - *Alternative:* keep the whole projections response. That is about 3 MB per season to read two numbers.

3. **Fetch rules.**
   - **Drafts:** follow the transactions pattern. A complete season gets its draft once; the current season fetches until `status == "complete"`, then stops.
   - **ADP:** fetched once per season, as soon as every configured league's draft for that season is complete.
     - For past seasons that is now, and Sleeper's stored values are preseason ones.
     - For future seasons it is the first sync after the last draft, which captures draft-day ADP.
   - A failed fetch warns and retries next run, as transactions do.

4. **Steal/Reach in picks against ADP.**
   - **Redraft:** `pick_no − ADP`.
   - **Rookie drafts:** `pick_no − ADP rank` within the draft's Players, by dynasty ADP.
   - **Thresholds:** 12 picks (redraft) and 6 picks (rookie). Kept as constants in `src/ffapp/draft.py`, with `Calculations.txt` section 25 explaining them.
   - **RB/WR exception:** "Still available" means not yet picked and not a keeper. The pool is every Player with an ADP (redraft) or the draft's Players (rookie).
   - **Analysis (2026-11-27):** about 21 steals and 35 reaches per redraft draft after the exception, and 2 to 7 of each per rookie draft. The extra reaches reflect how this league really drafts (late RBs, kickers and defences taken earlier than ADP), as the owner accepted.

5. **Hit/Bust in WAR against slot WAR, not rank differences.**
   - **Why not ranks:** rank differences were rejected after analysis. The WAR pack near zero spans about 24 ranks per 0.2 WAR. Early picks could only bust, and late kickers and defences became "hits".
   - **Slot WAR:** the mean window WAR of picks within ±6 slots (redraft) or ±3 slots (rookie), over the league's drafts with a complete window. Keepers are left out.
   - **Window in progress:** slot WAR is scaled by the share of the window's regular-season weeks played, using `through_week` against the regular weeks in the window.
   - **Thresholds:** 0.75 WAR (redraft) and 1.0 WAR (rookie), giving about 19 of each per redraft draft and 4 to 7 per rookie draft.
   - *Alternative:* a slot curve fitted across all drafts (smoothing). The moving window is simpler to explain, and close enough at roughly 1,000 redraft picks.

6. **Rookie grading window = draft season + next season.**
   - The table's WAR column shows the same window, and the grade uses it, so drafts of different ages compare like for like.
   - Slot WAR for rookie drafts uses only drafts whose two seasons are complete: 2022 to 2024 today.
   - *Alternative:* all seasons since the draft. That favours older drafts, and slot WAR would need one curve per draft age.

7. **Unlucky.**
   - **Games possible:** the regular-season weeks in the window, through `through_week`, in which the Player's NFL team had a game. A team's games are the weeks in which any of its Players has a stats line with a game played. The Player's team each week is his own stats line's team, else his nearest week's, else his team at the draft, so a mid-season trade counts the right team. (The WAR file holds one team per season, and the NFL schedule is stored for 2026 only.)
   - **Unlucky:** played games below half of games possible.
   - **Grade:** Unlucky replaces Bust, never Hit.

8. **Export shape (`site/data/<league>/draft.json`):**
   - `{league_key, generated_at, latest, managers{…as schedule.json}, thresholds{steal, hit}, seasons{s: {type, rounds, slots[{slot, user}], picks[...], summary[...]}}, all_drafts_summary[...]}`.
   - **Each pick:** `{no, round, slot, label, user, slot_user, keeper, player{id, name, first, last, pos, team, exp}, adp, adp_rank, adp_pos_rank, adp_diff, steal_reach, war, war_rank, war_pos_rank, slot_war, war_gap, hit_bust, games, games_possible}`.
   - The page only renders. All grades are decided in Python.

9. **Page module: a new `site/draft.js`** mirroring `site/schedule.js`.
   - **`league.js`:** adds the third tab and routes `#<league>/league/draft/<board|table>/<season>`.
   - **Grade switch:** the Draft Day | Results switch is board-only page state (not in the URL), like Records' expanded rows.
   - **Board cells:** player names go through the existing `fitNames` (full name, else "A. St. Brown", wrapping at a hyphen rather than cutting off).
   - **Phones:** the board uses the same sticky-left pattern as the Strength of Schedule tables, applied to the round column.

10. **Colours:** new tokens, as hex with an OKLCH note, in light and both dark blocks:
    - `--draft-steal-f/i` (light blue) and `--draft-reach-f/i` (light orange), derived from the existing blue and orange hues.
    - `--draft-hit-f/i` (dark blue, light blue text) and `--draft-bust-f/i` (dark red, light red text).
    - `--war-pos` and `--war-neg` for WAR text.
    - Each pair goes into `tests/test_colour_contrast.py`. A failing pair is fixed by changing lightness only.

11. **Injury history from nflverse (owner's choice, 2026-11-27).**
    - **Source:** nflverse publishes, per season, `weekly_rosters/roster_weekly_<season>.csv` and `injuries/injuries_<season>.csv` as GitHub release files.
      - The weekly rosters carry each Player's `sleeper_id`, `status` and `status_description_abbr`: R01 injured reserve, R48 IR designated to return, R04 PUP.
      - The injury reports carry `report_status` (Out) by `gsis_id`, mapped to Sleeper ids through the same roster file.
    - **Stored:** `data/injury-reports/<season>.json` = `{week: {sleeper_id: "IR" | "PUP" | "Out"}}`, fantasy positions only, regular season and playoffs. That's a few KB per season, against 15 MB of source CSV.
    - **Fetch:** completed seasons once; the current season on every cold run. A failure keeps the file and warns.
    - **Separate from `data/injuries/`:** that folder holds the saved Sleeper statuses that Player WAR reads, so WAR doesn't change.
    - **Unlucky:** more than half of the team's games in the window missed while IR, PUP or Out. A game "missed" is a week the team played and the Player had no game played.
    - *Alternative:* only the saved Sleeper statuses, from 2026 week 11, which would leave every past pick without an Unlucky grade.

12. **Recorded keepers in the configuration.**
    - **Where:** `config/leagues.yaml` gains `keepers: {"<season>": [sleeper_id, ...]}` under the redraft league, starting with 2026's five. Names are given in comments.
    - **Validation:** the config loader checks that the season is four digits and the ids are strings of digits, failing with the field named as for every other setting.
    - **Earlier seasons:** 2022 to 2024 keep Sleeper's `is_keeper` flags, which followed earlier rules. No configured season before 2025 is used.
    - *Alternative:* names. Ids avoid ambiguity, for example Javonte Williams against Jamaal Williams.

13. **Keeper eligibility (latest redraft draft only).**
    - **Rule:** a pick is eligible when its roster made it and no completed transaction in the season moved the Player off that roster: a drop, a trade away, or a commissioner move. The Player must also be on that roster's stored roster, which for a completed season is the final one, through the championship week.
    - **Price:**
      - A Player kept this season (configured) costs Rd 1, unless he was also kept the season before, which makes him not eligible.
      - Otherwise the price is round minus one, so round 1 is not eligible.
    - **In season:** eligibility runs through the latest week played and is marked not final.
    - **Export:** `keepers: {for_season, final, rows: [{user, players: [{player, drafted_round, price_round, second_year}]}]}` on the latest redraft season only.

14. **KE badge on the Managers page.**
    - `src/ffapp/managers.py` reads the keeper-eligible ids from the draft figures (the same function as the export, no second rule) and sets `keeper_eligible: true` on those roster rows for the redraft league's current season.
    - `site/managers.js` adds a small gold badge (the `--rank1-*` gold tokens, already contrast-checked) after the name.

## Risks / Trade-offs

- **[Sleeper changes or drops the undocumented projections endpoint, or its ADP fields]** → ADP is stored once and kept. A season without ADP still shows its board, with no Steal/Reach grades, and the page note says so.
- **[ADP for a future season keeps moving after the draft]** → It is fetched at the first sync after both drafts complete, and never again.
- **[Few rookie drafts make slot WAR noisy]** → ±3 slots across every complete draft (21 picks per slot today), and it improves each year. Calculations section 25 says how many drafts each figure rests on.
- **[`draft_id` points at the wrong draft in some future season]** → The sync test pins the 2022 dynasty case. A mismatch between pick count and rounds × teams logs a warning.
- **[The redraft board is 14 rows by 12 columns, which is wide on phones]** → It scrolls sideways inside its card with rounds pinned, and the Table view's list rows are the phone-first reading.
- **[Players without a WAR entry (no games at all)]** → Their WAR counts as 0, with games played 0. Such a Player is Unlucky when his team played.

## Migration Plan

- **First sync after deploy:** it backfills every stored season's draft (11 drafts, one request set each) and ADP for 2021 to 2026. It's a one-time cost of about 40 requests at the client's existing throttle.
- **Records:** the new files are committed by the cold refresh like other records. `docs/refresh-modes.md` ("Where Data Lives") lists `data/adp/` and the draft files.
- **Rollback:** remove the tab and the export step. The stored records are harmless and can stay.
