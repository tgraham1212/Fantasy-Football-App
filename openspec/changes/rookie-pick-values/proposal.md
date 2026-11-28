# Proposal

## Why

Trades in the dynasty league move rookie picks as often as Players: 133 picks in 104 trades. A pick carries no WAR until it is used, so a trade for a future 1st can't be valued, and the Trades tab (change `league-trades`) can't rank such trades. Thirteen years of rookie drafts, valued with the site's own Player WAR, give each pick an expected value grounded in history.

## What Changes

- **Rookie draft history:**
  - **2013–2021 classes:** the rookie order is each rookie's average pick in Dynasty League Football (DLF) startup mock drafts held May to August on MFL, ranked among QB/RB/WR/TE rookies. The source is mizelle.net's yearly pages. This order agrees with this league's own rookie drafts at 0.79–0.90 (rank correlation) for 2022–2026.
  - **2022 onward:** this league's own rookie drafts. For 2022, that's the startup draft's rookies in pick order.
- **History WAR:** WAR for 2013–2021 comes from the unchanged Player WAR method (Calc 16), with the dynasty league's scoring and lineup, weeks 1–14 and the season-long ESPN start-percentage cut. Run on 2022–2025, this method reproduces the stored WAR exactly.
- **History records (committed):** Sleeper weekly stats for 2013–2021, slimmed to the fields scoring and WAR use, and ESPN's season start percentages. Both go under `data/history/`, apart from the league seasons.
- **Third-party pages stay local:** a local command fetches the mizelle.net pages into a gitignored cache. They're never committed and never fetched by a cold run.
- **Rookie order record (committed):** the same command saves its result, each 2013–2021 class's slots with Sleeper IDs, as `data/pick-values/rookie-order.json`. Those classes never change, so the pages are needed only once. The model then rebuilds from committed data alone, ready for a later yearly automatic rebuild (backlog).
- **Pick value model:**
  - **Value:** a pick's value is the WAR its Player produces over the 8 seasons from his draft.
  - **Groups:** picks are grouped as Early (1–4), Middle (5–8) and Late (9–12) of each round.
  - **Calculation:** each group's value is averaged over every class 2013–2025, each class weighted equally.
  - **Never rising:** values are forced to fall from 1st Early to 3rd Late, by averaging neighbours that break that order.
  - **Today's values:** 1st +3.38 / +1.45 / +0.11, 2nd −0.75, 3rd −1.03 / −1.05 / −1.05.
  - **Storage:** the model is made by a command that reads only committed records, and committed as a record, `data/pick-values/model.json`.
- **Value of an unused pick:**
  - **Draft order known:** the pick's own group.
  - **Next draft, order not yet known:** the third the current Forecast's projected finish puts the original team in.
  - **Drafts further away:** the round average.
- **Page:** a "How Pick Values Work" page, like the calibration page, linked from the league pages. It shows:
  - the group values;
  - total WAR over 8 seasons by group;
  - WAR in each season by round;
  - value by slot;
  - how the values are made, crediting DLF and mizelle.net.
- **Docs:** a Calculations section, glossary terms, a feature doc with its diagram, and the requirement diagrams.

## Capabilities

### New Capabilities
- `rookie-pick-values`: the rookie pick value model. It covers the rookie order sources and record, the history WAR and its records, the 8-season value, the pick groups and the never-rising rule, the value of an unused pick, the model record, and the export.
- `pick-values-page`: the "How Pick Values Work" page. It covers its link, group table, charts, method and source credits, and phone layout.

### Modified Capabilities
- `data-storage-tiers`: the history stats and ESPN season snapshots for 2013–2021, the 2013–2021 rookie order and the pick value model join the committed records.

## Impact

- **Code:**
  - New `src/ffapp/pick_values.py`: rookie order, history WAR through a history store, the model, unused-pick values and the export.
  - New `src/ffapp/mizelle.py`: fetches and parses the local DLF pages.
  - `src/ffapp/cli.py`: the commands `history-fetch`, `rookie-adp-fetch` and `pick-values`.
  - `src/ffapp/export.py`.
  - New `site/pick-values.html` and `site/pick-values.js`.
  - The header link in `site/index.html`.
  - `.gitignore`: the local cache.
- **Data:**
  - New records:
    - `data/history/stats/<season>/week_NN.json`: 2013–2021, weeks 1–14, slimmed.
    - `data/history/espn/<season>/season.json`.
    - `data/pick-values/rookie-order.json`: the 2013–2021 classes, written once.
    - `data/pick-values/model.json`.
  - Derived: `site/data/pick-values.json`.
  - A one-time fetch of 126 Sleeper stat weeks, 9 ESPN season snapshots and 9 mizelle.net pages.
- **Tests:** unit tests for the rookie order, history WAR, model, groups, the never-rising rule, unused-pick values and export; layout tests for the page; contrast checks for the chart colours; copy IDs.
- **Docs:**
  - `Calculations.txt`: a new section 27.
  - `openspec/glossary.md`: Pick value, Pick group.
  - New `docs/pick-values.md` and `tools/pick_values_diagram.py`.
  - `docs/refresh-modes.md`.
- **Not in this change:**
  - The Trades tab and trade values (change `league-trades`).
  - FantasyPros data: kept for a later look at dynasty market values.
  - Running the rebuild automatically each season: a later "yearly tasks" change.
