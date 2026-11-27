# Glossary

The project's terms, its nomenclature rules and the terms requirements may not use. Specs use these words with the meanings below. The requirements standard is in `openspec/config.yaml` and the `project-standards` spec; the requirements check (`tests/test_requirements.py`) reads the Terms and Banned Terms lists from this file.

A term goes here when specs use it with a meaning a new reader could not guess. A term no spec uses any more is removed (the check names it).

## Nomenclature

In everything people read (site text, docs, specs; not code or data identifiers such as `owner_id`):
- **Managers** for league members, never "owners".
- **Team Names** for the names Managers give their teams each season.
- **Players** for NFL players.
- **Forecasts** for anything the simulation produces, never "odds", "chances" or "predictions".
- **Projections** only for Sleeper's Player projections, which are inputs.

Style is APA, with title case for titles and headings.

## Terms

- **Manager:** a member of a league, who sets a team's lineup and makes its moves.
- **Team Name:** the name a Manager gives their team for one season.
- **Player:** an NFL player, or a team defence, on a fantasy roster or available as a free agent.
- **Forecast:** a probability or expected value produced by the simulation, such as a team's probability of making the playoffs or of winning a game.
- **Forecast of record:** the game Forecast frozen at kickoff, which the finished game is judged against.
- **Slate Forecast:** the season Forecast saved when a slate of games ends, so each slate's effect can be shown.
- **Projection:** Sleeper's expected stat line for a Player in a week (Rotowire, via Sleeper); an input, never an output.
- **As-of week:** the week after which a season Forecast was made; the as-of-week-11 Forecast uses results through week 11.
- **Slate:** a group of NFL games with the same kickoff time, such as Sunday 1 pm, the two late-afternoon groups, and each night game.
- **FLEX:** a lineup slot that takes a running back, wide receiver or tight end.
- **Replacement level:** the points per week a Player freely available on waivers would score at a position (`Calculations.txt`, section 14).
- **WAR:** wins above replacement, how many wins a Player added over a replacement-level Player.
- **Win probability added (WPA):** how far a Player's scoring moved their team's win probability in a game.
- **Default lineup:** the best legal lineup of a team's rostered Players at their pre-kickoff Sleeper Projections; lineup choices are measured against it (`Calculations.txt`, section 11).
- **Residual:** a Player's actual points minus their projected points in one week.
- **Error pool:** the residuals of Players at the same position and projection level, from which the simulation draws each simulated miss; `Calculations.txt`, section 4, calls it a noise pool.
- **Roster drift:** the shrinking of a team's projected edge, and the added spread, the further ahead a week is, modelled as a random walk (`Calculations.txt`, section 6).
- **Calibration:** the comparison of Forecast probabilities with what happened, across every completed season.
- **Record:** data committed to git under `data/`, kept for good; the durable copy of league history and Player data.
- **Derived data:** files rebuilt from records by `python -m ffapp build` and not kept in git.
- **Tally:** a count captured from Sleeper or ESPN that changes through the day, such as trending adds and start percentages, committed once a day.
- **League record:** a best or worst figure in a league's history, such as the highest team score or the longest losing streak, shown on the League sub-tab's Records page; not a stored **Record**.
- **Meaningful Games:** the games most Managers care about, which league records count: regular-season games, winners-bracket games on the path to the championship, the championship, the 3rd place game (often still played for money) and, in a toilet-bowl league, the toilet bowl games on the path to its final and that final. Every other placement game (5th place and so on) and every consolation game is ignored; in a league without a toilet bowl, the teams outside the playoffs finish in standings order.
- **Strength of Schedule:** how hard a Manager's regular-season schedule is, shown two ways on the League sub-tab: Weekly Ranks and Schedule Swap.
- **Weekly rank:** a team's place among all teams by points scored in one week, 1 for the most; equal scores share the better rank.
- **Weekly Ranks:** the Strength of Schedule view that averages the weekly ranks of each Manager's opponents; the lowest average is the hardest schedule.
- **Schedule Swap:** the Strength of Schedule view giving each Manager's wins had they played every other Manager's schedule with their own weekly scores.
- **Schedule Difficulty Index:** a Manager's average wins across every Manager's schedule, their own included, minus their wins on their own schedule; the highest is the hardest schedule.
- **Card state:** which of eleven states a Games page card is in (F1, F2, C, P2, L1, L2, P1, O1, O2, O3, PW), set by whose games have started or finished; defined in the `game-card-states` spec and `docs/games-page-states.md`.
- **Refresh mode:** how often data is refreshed: offseason, quiet (in season, no games in progress) or live (games in progress).
- **Hot run:** the quick refresh of the current week (`hot.yml`), which writes the live bundle.
- **Cold run:** the full refresh (`refresh.yml`), which commits changed records and deploys the site when it changes.
- **Live bundle:** the current week's Forecasts and game cards, written by a hot run to Cloudflare Workers KV and read by the site.
- **Relay:** the Cloudflare Worker that starts refreshes, sets the refresh mode and serves the live bundle to the site.
- **Supported browsers:** Chrome, Safari, Edge and Firefox on desktop; Chrome and Safari on phones.
- **Phone widths:** the widths the layout check tests: 360, 390, 414 and 440 px, plus 768, 1000 and 1280 px.
- **Maintainer:** the person who runs the project and approves its changes; not a league member (those are Managers).
- **Need:** a top-level requirement (level 0) in the `needs` spec, stating what the app is for.
- **Primary parent:** the first parent in a requirement's Traces to line, which its ID is numbered under.
- **TBR:** To Be Resolved; a value or behavior not yet settled, with its rationale, what closes it and a target date.
- **Verification gap:** a requirement with no test or other evidence yet, written `Gap:` on its Verified by line.
- **Standard review:** the dated inspection of a spec's tolerances, rationale and glossary terms, recorded in `openspec/inspection-checklist.md`.

## Banned Terms

Requirement statements may not use these. They are unverifiable or ambiguous (NASA Systems Engineering Handbook, Appendix C) or retired by the nomenclature rules. Text in backticks (code, file and data names) is not checked.

- adequate
- appropriate
- as appropriate
- as needed
- as required
- adaptable
- and/or
- approximately
- but not limited to
- easy
- etc.
- fast
- fault tolerant
- flexible
- high fidelity
- if possible
- maximize
- minimize
- normally
- optimize
- quickly
- rapid
- robust
- roughly
- sufficient
- support
- TBD
- typically
- user friendly
- when necessary
- owner
- owners
- odds
- chance
- chances
- prediction
- predictions
- predicted
