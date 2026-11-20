# Design

## Context

The site is static. Python builds JSON in `site/data/` at each refresh, and the browser renders it. The Positions page set the pattern this change follows: one export per league, built from stored data, rendered by its own module.

The stored data already covers almost everything the page needs:

| Need | Stored source |
|---|---|
| Results, scores, weekly rosters | `matchups/week_NN.json` (`players`, `starters`, `points`, `players_points`) |
| Final places | `brackets.json` (winners and losers, with placement games `p`) |
| Records, streaks, potential points, FAAB used | `rosters.json` (`settings.ppts`, `waiver_budget_used`, `metadata.record`) |
| Names, avatars, team logos | `users.json` |
| Ratings, forecast history, WAR, replacement levels | existing stores |
| Injury statuses | `data/injuries/<season>/week_NN.json` |

Two things are missing. Body part, practice participation and depth chart are in the Sleeper player list the refresh already downloads, but they are not saved. Trending adds need one new request.

Constraints: the project standards (browsers and widths, WCAG 2.2 AA, 48 px touch targets, nomenclature, APA, colours in OKLCH by lightness only, calculations documented). Every new control goes in the layout registry, and every new text gets a copy ID.

The mockups are the visual reference:
- **Whole tab:** https://claude.ai/artifact/Mf2BJpgp1jpQMc3vkrcZ9H
- **Team info bar:** https://claude.ai/artifact/UvTbUrgnNXkpyxyMRwgZMp
- **Season info bar:** https://claude.ai/artifact/B2tPNvCWVTFbkKH3oiFbnD
- **Roster card:** https://claude.ai/artifact/5ESJUMohCQSEfbhznntwbe
- **Team History card:** https://claude.ai/artifact/TPFyqFx1uCxzGE2BrnBu1u
- **Moves card:** https://claude.ai/artifact/JPLB4L2pp4hd22Apm3yqnh
- **Team News card:** https://claude.ai/artifact/Y55cBuZtpMqQ1gRV9VkzWw

## Goals / Non-Goals

**Goals:**
- The Managers page as mocked, on desktop and phones, for current and retired managers in both leagues.
- Every figure computed once in Python and exported, so the page only renders.
- Story text editable through `site-copy.txt`.
- WAR wording corrected, with values proven unchanged.

**Non-Goals:**
- The transactions and drafts sync, the Moves lists, Moves stories, ESPN headlines and keepers. These belong to the second change.
- nflverse stories and AI-written recaps, which are on the backlog.
- Any change to forecasts, ratings or WAR values.

## Decisions

1. **One export per league, computed in Python.** A new `src/ffapp/managers.py` builds `site/data/<league>/managers.json` at export time. It holds every current and retired manager, each with every block the page shows. The browser does no statistics.
   - **Why:** consistent with Positions and Games, testable in Python, and the page loads one file.
   - **Size:** estimated under 400 KB per league, compressed by Pages.
   - *Alternative:* computing in JavaScript from raw matchups. Rejected: it would duplicate the bracket and identity logic, and is untestable in pytest.

2. **Identity reuses the existing helper.** Managers are keyed by Sleeper user id, with the vacant-roster fallback already used by Positions and ratings. Team names come per season from `users.json` metadata. The crest source is the team logo URL, else the avatar id, else none (the page then draws initials in the manager's chart colour). Retired managers have no chart colour, so their initials use the neutral former-member grey.

3. **Final places from the brackets.** Winners-bracket placement games give places: `p` 1 gives 1st and 2nd, `p` 3 gives 3rd and 4th, `p` 5 gives 5th and 6th.
   - **Losers bracket:** when it is a toilet bowl (`playoff_type` 0, as `BracketRules` already detects), its placement games read in reverse. The `p` 1 "winner" is last place (the toilet bowl champion), the loser is 11th, and so on.
   - **Consolation bracket** (dynasty): `p` 1 gives 7th and 8th.
   - **Missing data:** a season without stored brackets falls back to regular-season standings, and the History tab notes it.
   - **Check:** a test compares the computed champions and toilet bowl teams for 2021–2025 with what the league knows.

4. **Records ranked across everyone.** Each record is computed for every manager and season, then ranked: highest first for bests, lowest first for "lowest score" and for the losing streak, and closest loss by the smallest margin. Ties share a rank. Ranks 1 to 3 are exported for the gold, silver and bronze tags. The League History records cover regular season and playoffs; the all-play and luck figures use regular season only.

5. **Rivals in the league config.** `config/leagues.yaml` gains a per-league `rivals` block: `pairs` as roster ids (rivalries follow the team), plus `rivalry_week` per season (a week number, or null). It is seeded from the data found during exploration: week 7 for 2021–2025, null for 2026, and these six pairs:

   | Rival pairs |
   |---|
   | tg1212 – kjern17 |
   | djernberg – jrizzo15 |
   | NickLove17 – shanhynes |
   | corygraham12 – micaelaconnors |
   | TateFM – DeekBurg |
   | khar432 – Jdeguire (shown as SpookyCast in 2021) |

   Leagues without the block use the nemesis rule. Config validation rejects unknown roster ids.

6. **Move windows from weekly rosters.** `players` in each week's matchup gives every roster's players that week. A player's run of consecutive weeks on a team is an added window; the run of weeks away until he returns (or the latest week) is a departed window.
   - **WAR per week:** taken from the stored WAR weekly rows as `p_week − p(R_pos)` for active weeks. That is the same quantity the active-weeks WAR sums, so window WAR adds up exactly.
   - **Seasons:** redraft windows stop at the season's end. Dynasty windows continue across season files.
   - **Uses:** Best Player All-Time sums a player's added windows. The one that got away is the largest single departed window. Change 2 reuses the same windows for transactions.

7. **News as data, text in the site.** `src/ffapp/news.py` exports stories as data: a type, the week, a time, a link target, and named fields such as player, score and change. `site/managers.js` renders each type from a template string with a `/*copy:NEWS-…*/` ID, so the existing site-copy workflow covers every headline.
   - **Ranking:** a fixed order (record, forecast move of 20 or more, result, then the rest) picks the feature story. Within a week, stories are newest first.
   - **Limits:** at most three player stories per week per team, so injuries cannot flood the feed.
   - **Team of the Week:** the best legal lineup across all teams' starters and bench from that week's `players_points`.

8. **Player details and trending as new saves.**
   - **Details:** `injuries.py` writes `data/players/<season>/week_NN.json` (body part, practice participation, depth-chart order) from the player list it already downloads, with the same "last save of the week wins" rule.
   - **Trending:** `sleeper.py` gains `trending_adds()` for `/players/nfl/trending/add?lookback_hours=24&limit=25`, saved to `data/trending/<season>/<date>.json` by a new optional refresh step. Its failure warns and never stops the refresh, like the ESPN snapshot.
   - **Depth-chart and practice stories** compare a week's save with the previous week's.

9. **Page module and layout.**
   - **Code:** a new `site/managers.js`, loaded like the other page modules with `?v=__BUILD__`.
   - **Layout:** desktop is a grid with the four cards at `1.2fr 1fr 1fr 1fr`, falling to 2 × 2 under 1100 px. The site's existing 600 px breakpoint switches to the phone layout: the card tab row, no inner scroll, and a `min-height` shared by every card.
   - **Container queries:** used inside tiles and the feature picture, where the size depends on the tile rather than the window. They are supported in all target browsers.
   - **WebKit fix:** the page's grid children get `min-width: 0`, the fix found in the mockup for the scrolling sub-tab strip.
   - **Site width (decided during apply):** the site's content column widens from 1,088 px to 1,280 px (body `max-width` 1,312 px), so the seven tiles and the roster card fit the worst-case names as in the mockups. Every page uses the extra room on large screens. Defences in the roster show their nickname ("Chiefs").

10. **Images from Sleeper's CDN with fallbacks.** Team logos (users' `metadata.avatar`), avatars (`sleepercdn.com/avatars/thumbs/<id>`) and player headshots (`sleepercdn.com/content/nfl/players/thumb/<id>.jpg`). Every image has fixed dimensions, empty alt text where decorative, and an `onerror` fallback (initials for crests, a neutral silhouette for players), so a missing image never shifts the layout.

11. **New colour tokens.** Every new colour is added in OKLCH with lightness-only variants, in all three token blocks, and classified in `tests/test_colour_contrast.py`:
    - position pills;
    - IR and taxi pills;
    - PPG tiers r1–r5;
    - banner gold and brown;
    - form bars;
    - all-time rank tags;
    - news thumbnails;
    - rival badge.

    Text pairs are checked at 4.5:1. Decorative fills (the FLEX thirds, banner shapes, chart zone) are exempt, each with a reason.

12. **WAR active-weeks refactor (folded in).** `player_weeks` keeps only active weeks, and `baseline_wins` takes the count of active weeks. Missed weeks are still exported for the walkthrough, with `played: false` and no score or p. A test rebuilds WAR for every stored season before and after and asserts equality to four decimal places. The walkthrough cell reads "Bye" when the NFL schedule shows no game for his team that week, else "Out". `Calculations.txt` section 16 is reworded.

13. **Calculations documented.** New `Calculations.txt` sections:
    - **19 MANAGER HISTORY:** finishes, honours, head to head, records and ranks, luck, nemesis, move windows, best players.
    - **20 TEAM NEWS:** story triggers, thresholds and ranking.

    `managers.py` and `news.py` are added to `tests/test_calculations_doc.py`.

## Risks / Trade-offs

- **Bracket placement reading** is the riskiest assumption. Mitigation: the champion and toilet bowl test in decision 3, checked against known seasons, before anything renders.
- **A big page and a lot of new copy.** Mitigation: the tasks build the page in the order of the mockups, each section with its own tests and screenshots, and site-copy pending edits are reviewed with the owner.
- **Linux fonts on CI are wider.** The touch probe's wide-font pass and the layout check's wide-font test cover it, and the mockups were measured at worst-case values (double-digit WAR, 188.6 scores, the longest names).
- **Sleeper CDN images may be missing or slow.** The fallbacks render the same footprint.
- **Generated stories can repeat or read awkwardly.** The thresholds and the per-week cap limit volume, and templates are editable through site-copy.
- **Retired managers' data is partial** (no current roster, chart colour or forecast). Every block has an explicit retired state, shown in the mockups.
