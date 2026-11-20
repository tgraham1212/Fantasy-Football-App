# Proposal

## Why

Week 11's Thursday game was the first time the Games page ran with real live games, and it showed four problems: the game clock squeezed player names on desktop, every card showed the LIVE badge even when neither team had a starter playing, a team with no starter yet showed only its forecast while its opponent showed points so far, and long player names were cut off. The same deploy also had to fix the failed Managers tab release (92c1128), whose tiles cut text with Linux fonts.

## What Changes

- The game clock for a starter in progress moves to the right-hand column of the player row, where kickoff times already sit, in green with the live dot; the name keeps its space.
- A card shows the LIVE badge and border only when at least one real starter on either team is in a game in progress.
- Once either team in a game has a starter who has kicked off, both teams show points so far (0.0 when none), "X forecasted" beneath, and how many starters are still to play.
- Game cards stack in one column below 900 px (was 700 px), so lineups at tablet widths never overlap.
- A site-wide player name standard: show the full name; switch to first initial and last name ("A. St. Brown", a defence by its nickname) only when the full name does not fit its space; the full name stays in the tooltip. It applies on the Games page and the Managers page, and is recorded in the project standards.
- Managers page tiles scale their text with the tile's width, and the worst-case tile test also runs with a wide font that matches Linux font widths.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `games-page`: live cards only when a starter is playing, symmetric live totals, clock in the right-hand column, cards stack below 900 px, names fitted by the name standard.
- `manager-pages`: names follow the name standard (full when it fits); tile text scales with the tile and fits with wide fonts.
- `project-standards`: adds the player name standard and records it with the other standards.

## Impact

- `site/games.js`, `site/managers.js`, `site/styles.css` (clock column, live card test, name fitting, 900 px stacking, tile text scaling).
- `src/ffapp/forecast.py`: both teams carry live totals once either has started.
- Tests: `tests/test_live.py`, `tests/layout/test_managers_page.py` (wide-font pass), `tests/test_refresh.py` (accepts GitHub's annotation format for the skipped-step message, which failed CI).
- `openspec/config.yaml` and `CLAUDE.md` gain the name standard.
- Nothing stored changes; no new data or calculation (`Calculations.txt` unchanged).
