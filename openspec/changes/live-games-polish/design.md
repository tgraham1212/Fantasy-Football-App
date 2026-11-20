# Design

## Context

See proposal.md (Why). The fixes were built and checked against live week-11 data during Thursday's game. They touch the forecast output (`src/ffapp/forecast.py`), two page scripts and the shared stylesheet. Before this change, `game()` gave live totals only to a team with a locked starter. `cardHtml` marked every card live during a live week. The Managers page always used "A. St. Brown" names.

## Goals / Non-Goals

**Goals:**
- A live card means a starter is playing right now.
- Both teams in a started game read the same way.
- One name rule for every page that lists players.
- Managers tiles that fit with Linux fonts, so the deploy that failed passes CI.

**Non-Goals:**
- In-game projection updates. The week-11 probe showed Sleeper's projections stay frozen during a game; that stays on the backlog.
- Changing how live points or forecasts are calculated.

## Decisions

1. **Live totals for both teams in `forecast.game()`.** When any lineup row in the game has a status, both teams get `points_so_far` and `to_play`. A team with nothing played gets 0.0. Doing this in the data keeps the page script simple. It also means the card and any later view show the same thing. The alternative, filling in 0.0 in `games.js`, would have split the rule across two places.
2. **`cardIsLive(g)` checks the actual view's lineups for an `in_progress` row.** This applies only on the live week. Replacement fills never have a status, so they never count. The rule uses the actual view whatever view toggle the visitor has chosen, so the badge does not change when they switch views.
3. **The clock moves into the right-hand `kick` column.** That column already exists for kickoff times and takes no width when empty. It is styled `st-live`, in green with the dot. The name column no longer shares its line with a status tag, so long names keep their space.
4. **Cards stack below 900 px (was 700).** At 768 px two cards side by side left too little room for points, win probability added and the clock. 900 px is the narrowest width tested where two lineups fit.
5. **Names are fitted after rendering.** Each name carries `data-full`, `data-short` and a `title` holding the full name. `fitNames(root)` first sets the full name, then swaps to the short one when `scrollWidth > clientWidth`. It runs after rendering, on resize (debounced) and when a hidden list or card is shown. Hidden elements measure 0 wide and are skipped until they are shown. The Managers name span is `display:block` so it has a width to measure. The alternative, CSS-only ellipsis, cuts names off, which the standard forbids. Picking names by character count does not match real font widths.
6. **Tile text scales with container units.** Each tile's text sizes use `clamp(min, cqi, max)`. Label icons hide in tiles narrower than 185 px. The worst-case tile test runs a second time with a wide font (Verdana or DejaVu Sans), so local Windows runs catch what the Linux CI fonts would cut.
7. **The standard is recorded in three places:** the `project-standards` spec, the `openspec/config.yaml` context and `CLAUDE.md`, as the colour standard is.

## Risks / Trade-offs

- [Names are measured in the browser] → names can flash the full form before fitting on a slow device. They are fitted in the same frame as the render, so this is rarely visible.
- [The shared helpers are copied in two scripts] → `shortPlayerName`, `nameAttrs` and `fitNames` sit in both `games.js` and `managers.js`. They are small; moving them to a shared module can come with the next change that touches both scripts.
- [The trending refresh test accepts two message formats] → it only checks the message text, so a different GitHub annotation format would need another update.
