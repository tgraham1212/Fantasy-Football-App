# Proposal

## Why

The site stores every result and transaction but no drafts. So it can't answer the questions Managers argue about most after a season: who drafted well, who reached, which picks paid off, and where the best players went. The League sub-tab planned a History tab for this. It becomes **Draft**, and it brings draft picks into the data that the later Trades tab needs for trade trees.

## What Changes

- **Sync drafts:** for each league-season, store the draft that Sleeper names in that season's league settings, with every pick and every traded pick. A finished draft is fetched once. The current season's draft is fetched until it is complete.
  - In the dynasty league, the league's own draft is the rookie draft. Its first Sleeper season (2022) also has a 19-round "startup" draft, which only moved the rosters over from Yahoo. It is never stored.
  - Dynasty rookie drafts may include free agents, not only rookies.
- **Sync ADP:** for each season, store Sleeper's preseason ADP once that season's drafts are complete: half-PPR ADP for redraft, dynasty half-PPR ADP for dynasty.
- **Draft-day grade, Steal/Reach (in picks):**
  - **Redraft:** pick number minus ADP. A steal is a full round (12 picks) or more later than ADP; a reach is a full round or more earlier.
  - **Rookie drafts:** pick number minus the player's ADP rank among that draft's players, with half a round (6 picks) as the threshold.
  - **Exceptions:** an RB or WR who was the best or second-best ADP still available at his position is never a reach. Keepers and players without an ADP get no grade.
- **Retrospective grade, Hit/Bust (in WAR):** a pick's WAR minus the WAR that draft slot usually produces in this league, which is its slot WAR.
  - **Slot WAR:** the average for picks within 6 slots (redraft) or 3 slots (rookie drafts), across the league's drafts.
  - **Redraft:** the draft season's WAR, with ±0.75 WAR as the threshold.
  - **Rookie drafts:** WAR on every roster over the draft season and the next, with ±1.0 WAR as the threshold.
  - **Current season:** the slot WAR is scaled to the share of the window played so far, so grades move as the season goes.
- **Unlucky:** a pick who missed more than half of his NFL team's games over the grading window while listed Out, on injured reserve (IR) or on PUP. Shown in place of a bust, never in place of a hit.
- **Injury history from nflverse:** nflverse's weekly roster statuses (with each Player's Sleeper id) and weekly injury reports give, for every season from 2021, each fantasy Player's IR, PUP or Out weeks, stored as a small committed record. Completed seasons are fetched once; the current season on every cold run. The existing saved Sleeper statuses, which Player WAR reads, are left as they are.
- **Keepers (redraft):** the league's own keeper rules, tracked outside Sleeper:
  - **Recorded keepers:** from 2025 on, each season's keepers are listed in the league configuration (2026: Rashee Rice, Javonte Williams, Jaxon Smith-Njigba, Emeka Egbuka, Cam Skattebo). They are marked Keeper on the board and table and get no Steal/Reach or Hit/Bust grade, like the keepers Sleeper flagged in 2022 to 2024 under the earlier rules.
  - **Keeper eligible:** a Player is eligible to be kept the next season when the Manager drafted him (traded picks included) and he stayed on that roster through the championship week.
  - **Price:** one round higher than he was drafted (a first-round pick can't be kept); a Player kept this season costs a 1st to keep again, and a Player kept two seasons running can't be kept.
  - **Where it shows:** a Keeper Eligible matrix at the bottom of the latest redraft draft (Managers by price round, "eligible so far" while the season is in progress), and a small gold "KE" badge next to the Player's name on the Managers tab Roster card.
- **Managers summary:** per Manager, for one draft or all of a league's drafts: picks, average Steal/Reach, average Hit/Bust, total WAR, best pick and unlucky picks.
- **Export:** one draft file per league, holding every stored draft with its graded picks and both summaries.
- **Page:** a third League tab, "Draft", laid out as in the canvas mockups.
  - **Controls:** a Board | Table switch, a Season picker, and a Draft Day | Results switch on the board.
  - **Board:** rounds against draft slots. Cells are tinted by position. Traded picks name the Manager who made them, keepers are marked, and each cell carries one grade badge.
  - **Table:** sortable, with these columns: Pick ("2.01 (13)"), Manager ("via" the original Manager), Player (Steal/Reach pill at the end), ADP, ADP Rank with position rank, WAR, WAR Rank with position rank, Slot WAR, Hit/Bust, and Games Played.
  - **Colours:** Hit badges dark blue with light text, Bust badges dark red with light text, and WAR numbers blue when positive, red when negative.
  - **Phones:** the board scrolls sideways with the round column pinned, and the table becomes a list.
- **Docs:** a new Calculations section, glossary terms, a feature doc with its diagram, and redrawn requirement diagrams.

The Preseason tab (post-draft preseason Forecast and draft grades A to F) is a separate later change.

## Capabilities

### New Capabilities
- `league-draft`: the draft figures for every stored draft, and the redraft league's keepers and keeper eligibility: which draft counts, Steal/Reach against ADP (thresholds and the RB/WR exception), Hit/Bust against slot WAR (windows, neighbourhoods, scaling, thresholds), Unlucky, the Managers summaries and the export file.
- `league-draft-page`: the League sub-tab's Draft tab: the switches and Season picker, the board and table, badges and colours, sorting, phone layouts and the URL.

### Modified Capabilities
- `sleeper-league-sync`: the sync also stores each league-season's draft (picks and traded picks), fetched once when complete, and Sleeper's preseason ADP for each season; failures keep the stored files.
- `data-storage-tiers`: drafts, ADP snapshots and nflverse injury reports join the records committed to git.
- `injury-history`: past seasons' injury reports (IR, PUP and Out weeks) from nflverse are stored once per completed season and on every cold run for the current one.
- `manager-pages`: the redraft Roster card marks keeper-eligible Players with a gold "KE" badge.

## Impact

- **Code:**
  - `src/ffapp/sleeper.py`: draft, picks, traded picks and season ADP calls.
  - `src/ffapp/sync.py`: draft and ADP sync.
  - `src/ffapp/store.py`: draft and ADP files.
  - New `src/ffapp/draft.py`: the grades and summaries.
  - `src/ffapp/export.py`: the new file per league.
  - `site/index.html`, `site/league.js`, new `site/draft.js`, `site/styles.css`.
- **Data:** new committed records `data/leagues/<league>/<season>/draft.json` and `data/adp/<season>.json`, about 1,300 picks across both leagues plus one ADP file per season. A new derived file, `site/data/<league>/draft.json`, is built by `python -m ffapp build`. The cold refresh stops fetching a draft once it is complete.
- **Tests:** unit tests for the sync, grades and export; layout tests for the tab; entries in `tests/layout/controls.py`; contrast checks for the new colour tokens; copy IDs in `site-copy.txt`.
- **Docs:**
  - `Calculations.txt`: a new section 25.
  - `openspec/glossary.md`: ADP, Steal/Reach, Slot WAR, Hit/Bust, Unlucky pick and Rookie draft.
  - New `docs/draft.md` and `tools/draft_diagram.py`.
  - `docs/requirements.md` diagrams.
