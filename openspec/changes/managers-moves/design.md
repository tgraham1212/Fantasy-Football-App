# Design

## Context

See proposal.md (Why). The pieces this builds on:

- **Sync:** `sync.py` fetches whole league-seasons. Completed seasons are skipped, and the current season is fetched again on every refresh. `SleeperClient` has no transactions call yet.
- **Move windows:** `managers.py` already builds them from weekly matchup rosters with `windows()`. Added runs and departed runs carry WAR per week, redraft runs stop at the season's end, and dynasty runs carry across seasons. `faab_by_season()` reads spent and budget from the rosters.
- **News:** `news.py` exports stories as data, and `site/managers.js` renders each type from a template with a copy ID. Player stories are capped at three a week in `order_stories()`.
- **What the data shows:** an exploration probe of every stored season found:
  - about 320–415 completed transactions per league-season;
  - won and failed waiver claims, all carrying `settings.waiver_bid`;
  - trades carrying `draft_picks` (season, round, previous and new owner) and `waiver_budget` (FAAB sent);
  - 1–2 commissioner moves a season.
  - Failed claims share `status_updated` with the winning claim of the same waiver run.

## Goals / Non-Goals

**Goals:**
- Store transactions once per past season, and keep the current season fresh.
- Turn transactions into Added, Dropped and Trade moves with WAR, reusing the existing windows.
- Show waiver overpay and the five Moves stories.

**Non-Goals:**
- Draft block and grades, ESPN headlines, trade trees (pick history and the player a pick became), and keepers. These are later changes.
- WAR for picks.
- Changes to how move windows or WAR are calculated.

## Decisions

1. **Storage beside the matchups.**
   - **Where:** `data/leagues/<league>/<season>/transactions/week_NN.json`, the raw Sleeper list for each week (Sleeper's "round" or leg). `Store` gains `read_transactions(league, season)` and `write_transactions(...)`.
   - **Which weeks:** the season's weeks, the same range as the matchups. Apply checks once whether round 0 holds offseason moves, and includes it if so.
   - **Why raw:** keeping the raw list keeps failed claims and pick details for later changes such as trade trees.
2. **A separate sync step that cannot fail the season.**
   - **When it runs:** after a season is written, or when a completed season has no `transactions/` folder, which backfills the 11 stored seasons once.
   - **What it fetches:** every week's transactions.
   - **On failure:** a failed request logs a warning naming the league and season and leaves the stored files alone. It is not added to `SyncReport.errors`, so a Sleeper hiccup on transactions never blocks matchups or the refresh.
   - **Why the whole season:** fetching every week of the current season, not just the latest two, costs about 18 calls and keeps the logic the same as matchups. Late corrections are picked up too.
3. **Moves builder in `managers.py`.**
   - **Input:** completed transactions only.
   - **Waiver, free agent, commissioner:** one row per player in `adds` and `drops` for each roster involved.
   - **Dropped "how" line:**
     - "Claimed by X" when another manager's next completed add of that player falls inside the departed window;
     - otherwise "To waivers".
   - **Trade:** one entry per roster, with:
     - Got and Gave player ids;
     - picks as `{season, round}`, labelled "2027 2nd" by the page;
     - FAAB from `waiver_budget` sender and receiver amounts.
     - Players in a trade are kept out of the add and drop rows.
   - **Excluded:** drafted players never appear, because transactions do not include the draft.
4. **WAR of a move from the existing windows.**
   - **Week:** a move's week is its Sleeper leg, or week 1 of the next season for an offseason move.
   - **Which window:** the player's window of the matching kind (added for adds and got, departed for drops and gave) that starts at the first matchup week at or after the move's week.
   - **No games:** when no such window exists, or no week inside the window had a game for the player, the move exports `war: null`, which the page shows as "no games".
   - This reuses the WAR sums that Best Player All-Time already uses, so the numbers agree.
5. **Overpay.**
   - **Matching:** a won claim is grouped with the failed claims for the same player (key in `adds`) and the same `status_updated`, which is the waiver run.
   - **Amount:** overpay = bid − highest failed bid. With no failed bid, overpay = bid. When the two are equal, the claim is tied and has no overpay.
   - **Why the run:** failed claims from other runs, which happened in 6 dynasty 2025 cases, are ignored.
   - **Season totals:** each season's FAAB entry gains `biggest` (bid, player, week) and `overpaid` (the sum).
   - The rule goes into `Calculations.txt`.
6. **Export shape.**
   - **Where moves go:** each manager gains `moves: {<season>: {added, dropped, trades}}`.
   - **Rows:** each row holds the player id, name, position, how, week, bid, overpay or tied, the other manager's id and WAR.
   - **Size:** the current manager files are 220 KB (redraft) and 317 KB (dynasty). Moves add roughly 2,000–2,400 rows per league, under about 150 bytes each in compact keys. That keeps each file under about 700 KB, which is acceptable for a page that already loads them.
   - **If it gets too big:** if a file passes 1 MB, the moves move to a separate `moves.json` loaded with the Managers page. This is recorded here and not built now.
7. **Moves stories in `news.py`.**
   - **New types:** `trade`, `big_bid`, `pays_off`, `got_away` and `outbid`, built from the same moves and windows.
   - **Thresholds:** a share of each season's `waiver_budget`, because dynasty's budget went from $100 to $150 in 2025:
     - big bid: 25% or more, or the season's biggest;
     - outbid big: 20% or more;
     - outbid close: within $3 or on priority, with a bid of 5% or more.
   - **Pays off and got away:** fire in the week the window's running WAR first passes +1.0.
   - **Cap:** `order_stories()` caps the Moves set at three a week, separately from `PLAYER_TYPES`.
   - **Feature story:** these types never outrank the feature story's existing order.
   - **Text:** headlines get `/*copy:NEWS-…*/` templates.
8. **Page.**
   - **Card:** `renderMoves()` replaces the skeleton with the meter, the lists, the trade blocks and the Players block, as in the change-2 mockup.
   - **Season picker:** adds "All seasons", which joins every season's lists newest first and sums the meter's spent, overpaid and biggest across seasons.
   - **Filter:** live, showing All moves, Waivers, Free agents or Trades.
   - **Names:** follow the name standard (`shortName` and `fitNames`).
   - **New controls:** the "All seasons" option and the live filter go into `tests/layout/controls.py` under the existing `managers-moves` view.

## Risks / Trade-offs

- [Sleeper changes a transaction's shape] → the builder reads only the documented fields (`type`, `status`, `adds`, `drops`, `draft_picks`, `waiver_budget`, `settings.waiver_bid`, `status_updated`, `leg`), and a test covers each type with real samples.
- [Waiver runs share `status_updated` only by convention] → the probe matched every redraft contested claim this way. A unit test with stored samples guards it, and an unmatched failed claim simply adds no overpay.
- ["Claimed by" can name a manager who picked him up weeks later] → this is accepted. The window already covers that span, and the row's week tells the story.
- [All seasons in dynasty is a long list] → about 150 rows for a busy manager. It scrolls inside the card like the other lists, and the filter narrows it.
- [The first sync after deploy backfills 11 seasons] → about 200 extra requests at Sleeper's throttle, once, which adds a minute or two to one refresh.
