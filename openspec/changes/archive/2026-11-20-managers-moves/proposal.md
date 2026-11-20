# Proposal

## Why

The Managers tab shipped with the Moves card as a placeholder, because the app did not store Sleeper's transactions. Managers want to see their adds, drops and trades, what each move was worth in WAR, and how much they overpaid at waivers. This is the second of the two Managers changes.

## What Changes

- **Transactions sync.** Each league-season's transactions are saved by week (waivers, free agents, trades and commissioner moves, including failed waiver claims). Past seasons are fetched once. The current season is fetched again on every sync. A failed fetch warns and keeps the stored files.
- **Moves card.** The placeholder is replaced by the real card:
  - **Added and Dropped:** waivers, free agents and commissioner moves, one row per player. Each row has a "how" line and a WAR chip on the existing move windows. A move whose window holds no game for the player shows "no games".
  - **Overpay:** each waiver row shows a red "+$29" tag for the amount paid above the next bid in the same waiver run. A bid nobody else made counts in full. A tie won on waiver priority reads "tied".
  - **Trades:** a block per trade with Got and Gave sides listing players (with WAR chips), picks ("2027 2nd") and FAAB sent ("$5 FAAB"). Traded players never repeat in Added or Dropped. Picks carry no WAR.
  - **FAAB meter:** spent of budget, biggest bid and the season's overpaid total.
  - **Controls:** the season picker gains "All seasons". The filter (All moves, Waivers, Free agents, Trades) becomes live.
- **Moves stories in Team News.** There are five new story types: trade, big bid, pickup pays off, got away and outbid. They have their own cap of three a week per team, separate from the player stories.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sleeper-league-sync`: stores each league-season's transactions.
- `manager-history`: builds moves from transactions (rows, trades, overpay, FAAB totals) and adds them to the manager file.
- `manager-pages`: the Moves card replaces its placeholder.
- `team-news`: adds the five Moves story types and their weekly cap.

## Impact

- **Code:**
  - `src/ffapp/sleeper.py`: a `transactions()` call.
  - `src/ffapp/sync.py` and `src/ffapp/store.py`: fetch and save transactions.
  - `src/ffapp/managers.py`: the moves builder.
  - `src/ffapp/news.py`: the Moves stories.
  - `site/managers.js` and `site/styles.css`: the Moves card.
- **Data:** a new `data/leagues/<league>/<season>/transactions/week_NN.json`. `site/data/<league>/managers.json` grows by the moves for each season, about 400 moves per league-season.
- **Docs and checks:**
  - `Calculations.txt` gains the overpay rule.
  - New text gets copy IDs (`site-copy`).
  - The live filter and "All seasons" go into the layout check registry.
- **Later changes, not here:** draft block and grades, ESPN headlines, trade trees (pick history and the player a pick became), and keepers. Redraft keepers are handled by hand, so Sleeper's keeper flags are not used.
