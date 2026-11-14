# Proposal

## Why

The current odds table is a plain grid of eleven numbers per team: it shows everything the simulation produces, nothing stands out, and it has no room for the ELO rating that is next on the roadmap. League members should be able to glance at it and see who is safe, who is in trouble, and who is sliding toward the loser's bye or the 1.01 pick, in the familiar FiveThirtyEight layout. Reworking the table now, with ELO columns in place but empty, means the ELO change later only has to fill in data.

## What Changes

- Replace the odds table's columns with, in order: ELO, 1-week ELO change, owner (team name underneath, current record beside the owner name), projected record, and four playoff-chance columns: a league-dependent "bottom" column, Make Playoffs, Bye, Win Championship.
- The ELO and 1-week change columns render empty and are not sortable until the ELO feature exists; the exported data carries `null` placeholders for them.
- The bottom column depends on the league's settings: a toilet-bowl league shows **Avoid Loser's Bye** (chance of finishing outside the bottom two of the regular-season standings); a dynasty league with a consolation bracket shows **#1 Pick** (chance of finishing last in the regular season). The export decides; the site renders the label it is given.
- Chance cells get a sequential blue fill: white at <1%, dark blue at >99%, with text switching to white on dark fills. Light and dark themes each get their own ramp.
- Headers follow the 538 format: small uppercase two-line labels and a "Playoff chances" group header spanning the four chance columns.
- Default row order is the league standings (wins, then points scored). Clicking a sortable header sorts descending; clicking it again sorts ascending. The active sort header gets a dark fill and a small arrow; an untouched table shows neither.
- The weekly change column is removed. Each chance cell gets a hover tooltip with its change since the previous as-of week; the chart remains the place to read trends.
- Projected record renders to one decimal with spaces around the dash (`10.6 - 3.4`).
- The chart's metric buttons, at the top right of the chart card, match the four table chance columns in the same order (bottom column, make playoffs, bye, win championship).
- Every team gets its own fixed color on the chart, from a 12-color categorical palette anchored on the brand blue, built in OKLCH and validated for separation and AA contrast in both themes. Selecting a team dims the others instead of recoloring. A small swatch of the same color sits beside the owner name in the table, so the table doubles as the chart legend.
- The chart's vertical axis scales to the plotted data with some headroom instead of a fixed 0-100, so low-probability metrics such as the title are readable.
- Points scored, semifinal, final, losers-bracket and last-place columns leave the table. The data stays in the exported files.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `league-odds-site`: the "Current odds table" requirement changes (columns, default order, sorting, chance fills, tooltips, placeholder ELO columns, league-dependent bottom column) and the "Odds-over-time chart" requirement's selectable metrics change to match the table.

The `league-odds-site` capability currently exists only as a delta in the unarchived `monte-carlo-playoff-odds` change. Archive that change first so this delta applies on top of the main spec.

## Impact

- `site/index.html`, `site/app.js`, `site/styles.css`: table markup, sorting, cell fills, header styling, chart metrics, per-team line colors and axis scaling. `site/styles.css` gains 12 team-color tokens per theme; a small generator script under `tools/` records how they were derived.
- `src/ffapp/export.py` and `tests/test_export.py`: per-team `avoid_losers_bye` rate (derived from the stored seed distribution, so history is available for every stored as-of week), `elo`/`elo_change` placeholders, the league-level bottom-column descriptor, and the matching change and history series.
- No change to the simulation, stored odds files, the scheduled job or the Sleeper sync. The exported `site/data/*.json` files gain fields; nothing is removed, so the old site would still load them.
- Follow-up for the ELO change: populate `elo` and `elo_change` in the export and enable sorting on those two columns.
