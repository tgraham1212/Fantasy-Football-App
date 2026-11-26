# Proposal

## Why

In the dynasty league the losers bracket is a consolation bracket: the higher scorer moves on, and its
games decide places 7 to 12. Managers pay little attention to those games and often do not set lineups,
so the places they give are noise. In 2023 DeekBurg went 2-12, the worst record in the league, won two
consolation games and finished 9th, so the League tab's Worst Record shows "Missed Playoffs". Meanwhile
zagaplooza (6-8) lost theirs and is listed as that season's Last Place. Last place should be last in the
standings.

The rule for which games count already exists as "games that matter". Naming it **Meaningful Games**
makes the idea clearer and lets the place rule refer to it.

The live week's game cards have a related bug. The Actual view is meant to show each Manager's own lineup
(2.7.2), but during the live week it shows the live Forecast's lineup. In that lineup every slot not yet
locked is the model's pick, with free-agent fills. In week 12, tg1212 started Cam Ward, Josh Downs,
Chig Okonkwo and Derrick Henry, but the Actual view showed a free-agent quarterback, Mike Evans,
T.J. Hockenson and Jonathan Taylor. So the Model view's correct "benched" marks on Evans, Hockenson
and Taylor looked wrong.

## What Changes

- In a league without a toilet bowl, the consolation bracket is ignored. The teams outside the playoffs
  finish 7th to 12th in regular-season standings order (wins, then points for), so last place is last in
  the standings.
- This flows through every place shown: the League tab's Champions Last Place column, the season result
  chip ("Last"), the All-Time Standings last-place count, the Managers tab's season finishes, and Team
  News.
- Places 1 to 6, and every place in a toilet-bowl league, still come from the brackets.
- The simulation still plays the consolation bracket internally. The Forecasts "#1 Pick" column already
  measures last in the standings, so no Forecast changes.
- "Games that matter" is renamed **Meaningful Games**: regular-season games, winners-bracket games on
  the path to the championship, the championship, the 3rd place game, and in a toilet-bowl league the
  toilet bowl games on the path to its final and that final. Every other placement game is ignored. The
  definition is unchanged.
- During the live week, the game card's Actual view is simulated from the starters each Manager set.
  Locked starters count at their results and the others at their latest Projections, with no free-agent
  fills (an empty slot scores 0). The card's headline win probability, which is the Actual view's,
  follows. The Model view, its "benched" marks and the season Forecasts are unchanged.
- The "This season" chip on Player games (Best Games, Best Bench Games) becomes a requirement, and the
  Top 25 pop-up now shows it on phones too (it was missing there).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `manager-history`: 4.5.2 Final places takes the places of teams outside the playoffs from the toilet
  bowl or the standings; 4.5.2.1 drops "a consolation league's consolation winner 7th"; adds 4.5.2.2
  Consolation games ignored.
- `league-records`: 4.8.1 renamed Meaningful Games; 4.8.3 says last place is last in the standings in a
  league without a toilet bowl, and it and 4.8.6.5 gain a consolation scenario; 4.8.4.1 and 4.8.6.2 use
  the new term. 4.8.4's last-place count follows 4.5.2 with no wording change.
- `game-predictions`: 2.7.3 Live week views: the live Actual view uses the Managers' set starters, not
  the model's picks for open slots.
- `league-records-page`: adds 4.9.2.2.2, the "This season" chip on Player games, on the cards and in
  their pop-ups.

## Impact

- `src/ffapp/managers.py`: `bracket_places` ignores a consolation bracket and orders the teams outside
  the playoffs by the standings; `season_complete` follows (a season is complete once its winners
  bracket is placed).
- `src/ffapp/league_records.py`: comments and test names for Meaningful Games; no logic change beyond
  the places it reads.
- `src/ffapp/views.py` (`build_views`, live branch) and `src/ffapp/live.py`: build the live Actual
  lineups from the set starters and simulate them; WPA and points so far carry over from the live
  Forecast.
- `Calculations.txt` section on game views; `docs/simulation.md` mention of the live Actual view.
- `site/league.js`: the phone pop-up chip (already made in the working tree).
- `Calculations.txt` sections 19 and 23; `openspec/glossary.md`; `docs/league-records.md` and
  `tools/league_records_diagram.py`.
- Tests: `tests/test_managers.py` (consolation case), `tests/test_league_records.py` (rename, last place),
  `tests/layout/test_league_records_page.py` (`test_player_games_this_season`, already written).
- Data: derived files only (`managers.json`, `records.json`, news); no committed records change.
