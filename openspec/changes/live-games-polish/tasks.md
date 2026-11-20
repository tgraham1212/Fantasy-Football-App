## 1. Live Games Page

- [x] 1.1 `forecast.game()`: both teams carry `points_so_far` and `to_play` once either has a starter who has kicked off; `tests/test_live.py` checks it
- [x] 1.2 `games.js`: `cardIsLive` drives the LIVE badge and border (live week, a real starter in progress)
- [x] 1.3 `games.js` and `styles.css`: the game clock shows in the right-hand `kick` column in green with the dot; status tags no longer show the clock
- [x] 1.4 `styles.css`: game cards stack below 900 px; check that nothing overlaps at 768 px

## 2. Player Name Standard

- [x] 2.1 `games.js`: lineup names carry the full and short forms and are fitted after rendering, on view toggle, on list open and on resize; a replacement fill drops its "(replacement level)" bracket when it does not fit
- [x] 2.2 `managers.js` and `styles.css`: `shortName` returns a fitted `.fitname` span; names are fitted on render, card and history tabs, moves, resize and page show
- [x] 2.3 Add the player name standard to the `openspec/config.yaml` context and to `CLAUDE.md`

## 3. Managers Tiles and CI

- [x] 3.1 `styles.css`: tile text scales with `cqi` clamps; label icons hide in tiles narrower than 185 px
- [x] 3.2 `tests/layout/test_managers_page.py`: the worst-case tile test also runs with a wide font
- [x] 3.3 `tests/test_refresh.py`: the trending test accepts both forms of the skipped-step message

## 4. Verify

- [x] 4.1 Run `python -m ffapp site-copy` and confirm no new copy entries are needed or pending
- [x] 4.2 Run the Python test suite, the Games and Managers layout tests, and the accessibility and touch checks in light and dark mode
- [x] 4.3 Check the Games page against the current live-week data at 360, 768 and 1280 px: badge only on cards with a starter playing, symmetric totals, clock column and fitted names
