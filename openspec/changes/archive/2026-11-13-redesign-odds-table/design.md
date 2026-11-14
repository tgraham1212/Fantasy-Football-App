# Design

## Context

See proposal.md for motivation. Relevant current state:

- `src/ffapp/export.py` writes `site/data/<league>.json`: per-team rates (`RATE_KEYS`), each with `change` since the previous as-of week, plus `history.teams[rid][metric]` series (`HISTORY_KEYS`). Teams are emitted sorted by playoff chance. Every stored odds file already carries `seed_distribution` (12 entries, one per regular-season finishing place) and `last`, for every as-of week since preseason.
- The league object stored per season has `settings.type` (0 redraft, 1 keeper, 2 dynasty) and `settings.playoff_type` (0 toilet bowl, 1 consolation). `BracketRules.from_league` already reads `playoff_type`. Today: dynasty is type 2 / consolation, redraft is type 0 / toilet bowl.
- `site/app.js` is one plain module: it renders the table from a fixed template string, has a static `METRICS` list for the chart, and re-renders the chart on theme change but not the table. `site/styles.css` defines light/dark tokens on `:root` and keeps the first column sticky inside a horizontally scrolling wrapper. There is no JS test runner; the site has been verified with headless Chrome screenshots at desktop width and a 375px iframe harness.
- The `league-odds-site` spec exists only as a delta inside the unarchived `monte-carlo-playoff-odds` change.

## Goals / Non-Goals

**Goals:**

- Export every number the new table needs so the site stays a pure renderer with no league-specific logic.
- Keep the odds history intact: the new bottom column must have a full history line from preseason onward without re-running any simulation.
- Make the ELO columns a data-only follow-up: markup, styles and a rendering rule exist now; the ELO change only fills `elo` and `elo_change` and flips a sortable flag.

**Non-Goals:**

- No change to the simulation, the stored `data/odds/` files, the sync or the scheduled job.
- No JS build step or test runner. Table logic stays in plain modules, kept to small pure functions so a runner could be added later.
- No custom tooltip component for table cells; the native `title` tooltip is enough for a one-line delta. The chart keeps its existing hover layer.

## Decisions

### 1. Compute the bottom-column rate in the export, from `seed_distribution`

`avoid_losers_bye = 1 - seed_distribution[-1] - seed_distribution[-2]` (the last two finishing places, so it follows the league size). It is computed for every stored as-of week while building the history series, so the chart line exists back to preseason the moment the site deploys.

*Alternative*: add it to `simulate.summarize` and re-backfill. Rejected: it rewrites every odds file for a number that is a pure function of what is already stored, and future seasons would still need the export to handle older files.

### 2. The export picks the column; the site renders a descriptor

`league_export` adds a league-level `bottom_column` object: `{"key": "avoid_losers_bye" | "last", "label": "Avoid Loser's Bye" | "#1 Pick", "description": "<one sentence for the header tooltip>"}`. Selection rule, in order:

1. `playoff_type == 0` (toilet bowl) → `avoid_losers_bye`
2. `settings.type == 2` (dynasty) with a consolation bracket → `last`, labelled "#1 Pick"
3. otherwise → `avoid_losers_bye`

The site reads `league.bottom_column.key` to pick the team field for the table cell, the chart metric and the `?metric=` URL value, and uses the label verbatim. `BracketRules` gains nothing; the rule lives in `export.py` next to the other league-derived fields, with `settings.type` read directly.

*Alternative*: hardcode by league key in `app.js`. Rejected: the point of the rule is that a new league, or a settings change, needs no site edit.

### 3. Export payload additions, nothing removed

- Per team: `avoid_losers_bye` (rate), `elo: null`, `elo_change: null`. `RATE_KEYS` and `HISTORY_KEYS` both gain `avoid_losers_bye`, so `change` and `history` cover it like the other rates.
- League level: `bottom_column` as above.
- `points_for`, `semifinal`, `final`, `losers_bracket`, `last` and their changes stay in the file. Removing them saves nothing worth a schema break, and the chart and future stats pages can still use them.

Team order in the file stays sorted by playoff chance; the site sorts for display (decision 5), because display order is the site's concern and the file is also consumed by the history series.

### 4. Table rendering from a column definition list

`app.js` replaces the fixed row template with a `COLUMNS` array built per league: `{ key, header (two lines), group?, align, render(team), sortValue(team), sortable }`. ELO and ELO change entries have `sortable: false` for now. The thead is two rows: a group row with an empty cell spanning the four leading columns and a "Playoff chances" cell spanning the four chance columns, then the per-column header row. Sortable headers are `<button>`s inside `<th>`, with `aria-sort` set on the active `<th>` so the fill and arrow are pure CSS (`th[aria-sort="descending"] button::after` etc.) and assistive tech gets the state for free.

The owner cell is: `<span class="owner-name"><span class="swatch" style="--team: var(--team-3)"></span>tg1212 <span class="record">7-2</span></span><span class="team">Diaper Dandies</span>`, that is the existing two-line cell with the lines swapped, the record moved up, and the selection dot replaced by the team's color swatch (decision 10). The record is `7-2-1` only when ties exist. Projected record is `${w.toFixed(1)} - ${l.toFixed(1)}`.

### 5. Sorting: standings order by default, per-column comparators

`state.sort = null | { key, dir: "desc" | "asc" }`. Rendering sorts a copy of `league.teams`:

- `null` → standings: `wins + 0.5 * ties` desc, then `points_for` desc (the same rule as `standings.seed_order`, so the table matches Sleeper's standings page).
- `record` key → same comparator; `proj` → `proj_wins`; chance columns → their rate; `owner` → `display_name` case-insensitive, where "desc" means A to Z (the first click gives the natural reading order for every column).
- Ties within a sort fall back to standings order so the result is stable and predictable.

Clicking the active header toggles `dir`; clicking a different header sets `{ key, dir: "desc" }`. The sort is view state only: it is not written to the URL and resets on league switch.

### 6. Chance fill via `color-mix` and theme tokens

Each chance cell gets `style="--p: 63"` (percentage, clamped: `< 1` → 0, `> 99` → 100) and CSS does `background: color-mix(in oklab, var(--fill-lo) calc(100% - var(--p) * 1%), var(--fill-hi))`. The tokens are defined per theme: light `--fill-lo` = the surface colour, `--fill-hi` a 538-like dark blue (around `#1f5fa6`); dark `--fill-lo` = the dark surface, `--fill-hi` a mid blue that still reads as "high" on a near-black page (around `#2d6fc4`). Cells at or above 55% get class `fill-dark` which switches the text to the light ink token; the exact threshold is tuned in implementation so both the 55% light-theme cell and the 100% dark-theme cell meet 4.5:1. OKLab mixing keeps the mid steps from looking washed out the way sRGB mixing does.

Because the mix uses CSS variables, toggling the theme restyles the cells without re-rendering the table.

*Alternative*: compute RGB in JS. Rejected: it needs a re-render on every theme change and duplicates colour knowledge outside the stylesheet. `color-mix()` has shipped in every evergreen browser since 2023.

Per the dataviz rule that text wears text tokens, the value text uses the ink tokens, not the blue; only the fill carries magnitude.

### 7. ELO change pill

`elo_change` renders as `<span class="elo-delta up|down">+20</span>` with black text on `--pill-good` (light green) or `--pill-bad` (light red) tokens in both themes, empty when `null` or `0`. ELO renders as the plain integer or empty. Both columns get fixed narrow widths so the layout does not jump when data appears.

### 8. Sticky columns

On screens 600px and wider, the first three columns (ELO, change, owner) are sticky as a group: ELO at `left: 0`, change at `left: <elo width>`, owner at `left: <elo + change widths>`, which is why decision 7 fixes their widths. Below 600px nothing is sticky; three sticky columns would leave under 130px of scrolling room on a 375px phone, so the whole table scrolls instead, as the existing spec allows.

### 9. Chart metrics follow the table

`METRICS` becomes a function of the league payload: `[bottom_column, playoffs, bye, title]`, in the table's column order and using the bottom column's label and key. The buttons stay in the chart card's head, right-aligned, where the switcher already lives. `?metric=` accepts any of those keys; an unknown value falls back to playoffs. The `history` series for `final` keeps being exported but is no longer offered in the switcher.

### 10. One fixed color per team

Twelve categorical colors, one per roster. They are built by walking the OKLCH hue wheel starting from the brand blue (`--accent`), with lightness and chroma tuned per step so neighbours stay apart for colour-vision-deficient readers and every colour reads against its surface. Light and dark themes get separate sets (the dark set is lighter and slightly less saturated; it is not the light set flipped). Both sets are produced by `tools/team_palette.py`, a dependency-free script with its own OKLCH→sRGB conversion, and committed to `site/styles.css` as `--team-1` … `--team-12` under each theme. The script's output is checked with the dataviz skill's `validate_palette.js` in `--mode light` and `--mode dark`: adjacent-pair CVD separation, the normal-vision floor, and contrast against the surface must pass; the script's parameters are adjusted until they do, and the passing hexes are what get committed.

Assignment: teams sorted by ascending `roster_id` take `--team-1` … `--team-12`. Roster ids are stable for a season, so a team's colour never changes with sorting, metric, week or theme toggle, and it is the same on both the line and the table swatch. The swatch (an 8px dot before the owner name) replaces today's selection dot and makes the table the chart's legend, so identity is never carried by colour alone: the end label and the row name are always there too.

Highlighting: with no selection every line draws at full colour, 2px. Selecting a team keeps its line at full colour and 3px and drops the others to 25% alpha; the end labels stay in the ink text tokens (dimmed with the lines) with a small dot of the line colour in front of each, per the dataviz rule that text wears text tokens.

*Alternative*: 12 tints and shades of the brand blue. Rejected: adjacent steps of a one-hue 12-step ramp fail the categorical separation check and the light end cannot reach AA, so neighbouring teams would be indistinguishable.

*Alternative*: keep today's neutral lines with a single accent highlight. Rejected by the request: readers want to find their team without clicking.

### 11. The y-axis fits the data

For the current metric, the axis maximum is `min(100, ceil((maxValue + 5) / 10) * 10)` over every plotted point, recomputed on each metric switch and league load; the minimum stays 0. Title chances topping out at 34% therefore get a 0–40 axis instead of 0–100, while playoff chances still show 0–100. The floor stays at 0 because these are probabilities: a non-zero floor would exaggerate small moves and hide how far a team really is from certainty. The tick step follows the range (5 for a top of 40 or less, otherwise 10 or 25) so the grid stays recessive.

### 12. Verification approach

- Python: unit tests in `tests/test_export.py` for the bottom-column rule (toilet bowl, dynasty consolation, non-dynasty consolation), the `avoid_losers_bye` arithmetic against a known `seed_distribution`, the `elo` placeholders and the extended `change`/`history` key sets. The existing fixtures cover dynasty; the redraft case uses a league object with `playoff_type` and `type` overridden in the test.
- Site: headless Chrome screenshots of both leagues at desktop width and in the 375px iframe harness, light and dark, in the default state, after sorting, and on the title metric (axis scaled). A contrast check on the fill endpoints and the text-switch threshold using the dataviz skill's validator for the two `--fill-hi` colours against each surface.
- Palette: `node <dataviz skill>/scripts/validate_palette.js "<12 hexes>" --mode light` and `--mode dark` on the committed team colours; both runs must report no FAIL. The validator's report is kept in the task output.

## Risks / Trade-offs

- [`seed_distribution` missing from an old odds file] → The export treats a missing distribution as `avoid_losers_bye = None`, and the site renders "–" with no fill. All current files have it, so this is a guard, not an expected path.
- [`settings.type` absent or unexpected in a Sleeper league object] → Rule 3's default applies ("Avoid Loser's Bye"), which is correct for both current leagues even if the field vanished.
- [The site is deployed with data exported by old code] → Cannot happen through the workflow (export runs before deploy), but a local checkout after `git pull` will show a half-rendered table until `python -m ffapp export` is run. The site shows "–" for missing fields rather than throwing, and the README notes the re-export.
- [`color-mix()` unsupported in an old browser] → Cells show no fill but the percentages remain readable; the table degrades to the current look.
- [Three sticky columns on mid-width screens (600-760px)] → Still leaves 300px+ of scroll room; verified in the screenshot pass. Breakpoint can move up if it feels cramped.
- [Native `title` tooltips do not appear on touch devices] → Acceptable: the chart carries the trend story, and the tooltip is a convenience, not the only place the change is readable.

## Migration Plan

1. Archive `monte-carlo-playoff-odds` so `openspec/specs/league-odds-site/spec.md` exists for this delta to modify.
2. Implement export changes with tests, then the site changes; run `python -m ffapp export` locally and verify the site from `site/`.
3. Commit and push to `main`; the next scheduled run (or a manual `workflow_dispatch`) re-exports and deploys. No data migration: stored odds files are untouched.
4. Rollback: revert the commit. Old `app.js` ignores the extra fields, so the data files need no rollback.
