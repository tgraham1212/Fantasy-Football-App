## 1. Transactions Sync

- [x] 1.1 `SleeperClient.transactions(league_id, week)` for `/league/<id>/transactions/<week>`
- [x] 1.2 `Store.read_transactions` / `write_transactions` under `data/leagues/<league>/<season>/transactions/week_NN.json`
- [x] 1.3 Sync step: fetch every week's transactions after a season is written, and once for completed seasons with no `transactions/` folder; check whether round 0 holds offseason moves and include it if so; a failure warns, keeps stored files and never fails the season or refresh
- [x] 1.4 Tests: backfill once, current season refetched, failure keeps files and only warns
- [x] 1.5 Run the sync locally to backfill every stored season and check the counts against the exploration probe

## 2. Moves Builder

- [x] 2.1 `managers.py`: build added and dropped rows (waiver, free agent, commissioner) and per-side trade entries (players, picks, FAAB) from completed transactions, keeping traded players out of the rows
- [x] 2.2 Dropped "how": "Claimed by X" when another manager's next add falls inside the departed window, else "To waivers"
- [x] 2.3 WAR of each move from the matching window starting at or after its week (offseason moves from week 1); `null` when no week in the window had a game; picks carry none
- [x] 2.4 Overpay per won claim (same player, same waiver run), ties, and each season's overpaid total and biggest bid in the FAAB entry
- [x] 2.5 Export `moves` by season in `managers.json`; check the file sizes stay under 1 MB
- [x] 2.6 Tests with real transaction samples: each type, add+drop in one move, trade with pick and FAAB, contested / uncontested / tied overpay, a failed claim from another run ignored, no-games mark, dynasty trade window across seasons
- [x] 2.7 Document the overpay rule and move WAR in `Calculations.txt`

## 3. Moves Stories

- [x] 3.1 `news.py`: trade, big bid, pays off, got away and outbid stories with budget-share thresholds
- [x] 3.2 `order_stories()`: cap Moves stories at three a week, apart from the player stories
- [x] 3.3 `managers.js`: a headline template with a copy ID for each new type
- [x] 3.4 Tests: thresholds (big and close outbid, small loss skipped, $150 budget), pays off fires once, cap with a busy trade week plus an injury

## 4. Moves Card

- [x] 4.1 `renderMoves()`: FAAB meter with biggest bid and overpaid, Added and Dropped lists with the red overpay tag, "tied" and "no games", trade blocks with pick and FAAB tags, Players block
- [x] 4.2 Season picker with "All seasons" and the live filter (All moves, Waivers, Free agents, Trades)
- [x] 4.3 Styles for rows, tags, chips and trade blocks in OKLCH, derived from existing hues; new colour tokens added to `tests/test_colour_contrast.py`
- [x] 4.4 Add the filter and "All seasons" to `tests/layout/controls.py`; layout tests for the card at every width, including the wide-font pass
- [x] 4.5 Copy IDs on all new text; run `python -m ffapp site-copy`

## 5. Verify

- [x] 5.1 Python test suite and the full layout check (accessibility and touch, light and dark)
- [x] 5.2 Check the card against real data for a redraft and a dynasty manager at 360, 768 and 1280 px, including All seasons and each filter
