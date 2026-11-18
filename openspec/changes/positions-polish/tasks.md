# Tasks

## 1. Vacant roster fallback

- [x] 1.1 In `src/ffapp/store.py`, make `read_rosters()` and `read_users()` fill a vacant roster's owner:
  - the most recent earlier season's owner of that roster id, else the earliest later one
  - the roster is marked `owner_inherited`, and the inherited user's record is appended to the users from the season it came from
  - the ownership map is cached per Store and cleared by `write_season()`
  - raw files are untouched

  Verify: tests for the four spec scenarios (quit before the year ended, vacant in the first stored season, never owned, stored files untouched) pass.
- [x] 1.2 Check the consumers on the real store:
  - `league.owners()` names roster 11 in dynasty 2023 as DeekBurg with his 2022 team name
  - `ratings` credits his 2023 weeks with no vacant entry
  - WAR holders for roster 11's 2023 players are DeekBurg
  - a never-owned roster in a synthetic store still rates as vacant

  Verify: the ratings tests pass, including a new inherited-owner test, and a printed check on the real store.

## 2. Shared out statuses

- [x] 2.1 Add `OUT_STATUSES` (status to label: Out, Doubtful, IR, PUP, Suspended, Not active, Did not report) to `src/ffapp/injuries.py`. Use it in `not_playing()` in place of `NOT_PLAYING`, in `war.UNAVAILABLE_STATUSES` (adding Doubtful; update its comment), and in `positions` (flag plus a `status` label in each player entry). Verify: injury tests for NA, Sus and PUP labels; a WAR test where a Doubtful player never seen active uses ownership; positions tests for Doubtful flagged and Questionable not.
- [x] 2.2 Update the README:
  - the WAR "Current-season start percentages" subsection names the shared list
  - the Games not-playing description lists the statuses
  - the Positions section describes the popup lines

  Verify: the text matches the code.

## 3. Positions page polish

- [x] 3.1 Two-line row labels (manager display name, team name in small muted text, no swatch, ellipsis with the full text in `title`) and a 38 px minimum row height. Verify: a browser check at 1280 and 375 px.
- [x] 3.2 Equal row heights per desktop grid row: compute each chart's geometry first, pair the charts in order when the grid has two columns, use the larger row height, and leave a lone last chart alone. Verify: a layout test that the charts in each row have equal row heights and equal card heights at 1280 px.
- [x] 3.3 Centre the top player's name on his dot. Drop `overflow: hidden` on the plot, measure the name, and shift it only as far as needed to stay inside the card. Verify: the existing name-inside-card test passes at 375 px, and a desktop check shows Smith-Njigba or Gibbs centred over the dot.
- [x] 3.4 Popup status and taxi lines: add a `--gold` token in all theme blocks, checked to reach at least 4.5:1 against `--surface` in light and dark, plus `data-status` and `data-taxi` on the dots and the status (red) and "Taxi" (gold) lines, status first. Verify: a contrast check printed for both themes, and a layout test focusing an injured and a taxi dot that asserts the lines.

## 4. Regenerate, test and document

- [x] 4.1 Regenerate `ratings`, `war`, `simulate`, `games` and `export` on the real store. Report DeekBurg's dynasty rating before and after, and confirm roster 11's 2023 WAR owners and Positions row. Verify: the printed check, and that only expected files changed.
- [x] 4.2 Update `tests/layout/controls.py` and the layout tests for the new popup states and equal heights, and run `pytest`, `node --test relay/worker.test.mjs` and `LAYOUT_REQUIRED=1 pytest tests/layout`. Verify: all pass.
- [x] 4.3 Screenshots of the Positions page at 1280 and 375 px, light and dark, plus a popup on an injured and on a taxi player, for the user. Run `openspec validate positions-polish --strict`. Verify: validation passes and the screenshots are listed.

## Workflow follow-up

- Commit, push and archive with spec sync when the user asks.
