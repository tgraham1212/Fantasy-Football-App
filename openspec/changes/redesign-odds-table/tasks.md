# Tasks

## 1. Export: bottom column, placeholders, history

- [ ] 1.1 Add `avoid_losers_bye` to the export: computed per team for every stored as-of week as `1 - seed_distribution[-1] - seed_distribution[-2]` (`None` when the distribution is missing), included in `RATE_KEYS` and `HISTORY_KEYS` so `change` and `history` cover it. Verify with a unit test using a team whose distribution puts 3% in 11th and 1% in 12th → 0.96, and that the history series for it has one entry per stored week.
- [ ] 1.2 Add the league-level `bottom_column` descriptor (`key`, `label`, `description`) chosen from `settings.playoff_type` and `settings.type`: toilet bowl → `avoid_losers_bye` / "Avoid Loser's Bye"; dynasty with consolation → `last` / "#1 Pick"; anything else → `avoid_losers_bye`. Verify with unit tests for all three cases plus a league object with no `type` field.
- [ ] 1.3 Add `elo: null` and `elo_change: null` to every exported team. Verify the schema test in `tests/test_export.py` asserts both keys exist and are `None`, and that `pytest` passes in full.
- [ ] 1.4 Run `python -m ffapp export` against the stored data and verify `site/data/dynasty.json` has `bottom_column.key == "last"` with label "#1 Pick", `site/data/redraft.json` has `avoid_losers_bye` with label "Avoid Loser's Bye", and both files' histories contain `avoid_losers_bye` for weeks 0 through the current as-of week.

## 2. Table markup and styling

- [ ] 2.1 Rewrite the table `<thead>` in `site/index.html` as two rows: a group row with a "Playoff chances" cell spanning the four chance columns, and a header row for ELO, 1-wk change, Owner, Proj. record, bottom column, Make playoffs, Bye, Win championship, with sortable headers as `<button>`s. Verify the page renders with the eight headers and the group label spanning exactly the four chance columns.
- [ ] 2.2 Style headers in the 538 format in `site/styles.css`: small uppercase labels wrapping to two lines, a rule under the group label, right-aligned numeric headers, and the `aria-sort` states (dark fill plus ▾ / ▴ via `::after`), with no fill or arrow when `aria-sort` is absent. Verify by toggling `aria-sort` on a header in devtools and screenshotting the three states.
- [ ] 2.3 Add the fill tokens (`--fill-lo`, `--fill-hi` for light and dark) and the `color-mix()` rule driven by `--p`, plus the `fill-dark` light-text rule, and the ELO change pill tokens and styles (black text on light green / light red). Verify contrast with the dataviz validator: `--fill-hi` against each theme's surface, and the ink colour against the fill at the `fill-dark` threshold and at 100%, all ≥ 4.5:1; adjust the threshold until it passes.
- [ ] 2.4 Implement sticky positioning for the ELO, change and owner columns with fixed widths on screens ≥ 600px and no sticky columns below that. Verify screenshots at 1100px (three columns pinned while the chance columns scroll) and in the 375px iframe harness (whole table scrolls, no page-level horizontal scroll).

## 3. Table rendering and sorting

- [ ] 3.1 Replace the fixed row template in `site/app.js` with a per-league `COLUMNS` definition (key, header, align, render, sortValue, sortable) and render the owner cell (owner name with record beside it, team name beneath), projected record as `10.6 - 3.4`, chance cells with `--p` and `fill-dark`, and empty ELO cells. Verify in the browser that all 12 teams render for both leagues, the dynasty bottom column reads "#1 Pick", the redraft one "Avoid Loser's Bye", and ELO cells are empty.
- [ ] 3.2 Implement sorting: `state.sort` null by default (standings order: wins + ½ ties, then points scored), first click descending (owner A→Z), second click toggling, ties falling back to standings order, ELO columns ignored, sort reset on league switch. Verify in the browser: untouched table matches Sleeper's standings order for both leagues; clicking "Win championship" orders highest first with a dark header and ▾; clicking again orders lowest first with ▴; clicking ELO changes nothing.
- [ ] 3.3 Add the chance-cell `title` tooltip ("Up 2.6 points since week 8" / "Down …" / "No change since week 8"), omitted when there is no previous as-of week, and remove the old Δ column and `delta()` helper. Verify the tooltip text on a hovered cell in the browser and that a single-week export (test fixture or temporarily trimmed history) shows no tooltip.
- [ ] 3.4 Make the chart metric list a function of the league payload, in the table's column order (`bottom_column`, playoffs, bye, title), keep the buttons right-aligned in the chart card head, accept the bottom column's key in `?metric=`, and fall back to playoffs for unknown values. Verify in the browser that the switcher shows four buttons at the top right labelled and ordered to match the table's chance columns, the bottom-column chart plots values from preseason to the current week, and `?metric=last#dynasty` opens the "#1 Pick" chart.
- [ ] 3.5 Update the "Current odds" card hint text and the README's website section for the new columns, sorting and the re-export note after `git pull`. Verify the README commands still run as written.

## 4. Chart colors and axis

- [ ] 4.1 Write `tools/team_palette.py` (dependency-free OKLCH→sRGB) that walks the hue wheel from the brand blue with per-step lightness and chroma tuning and prints a 12-color light set and a 12-color dark set. Verify by running the dataviz skill's `validate_palette.js` on each set (`--mode light` against the light surface, `--mode dark` against the dark surface) and adjusting the parameters until neither run reports a FAIL; keep the validator output in the task notes.
- [ ] 4.2 Commit the passing colors as `--team-1` … `--team-12` tokens under each theme in `site/styles.css`; in `site/app.js` assign them by ascending `roster_id`, color each line with its team token, dim unselected lines to 25% alpha when a team is selected, draw a colored dot before each end label, and replace the table's selection dot with the team swatch beside the owner name. Verify screenshots in both themes show 12 distinct lines whose colors match the row swatches, that sorting the table does not change any team's color, and that selecting a team keeps its color and dims the rest.
- [ ] 4.3 Make the y-axis max `min(100, ceil((max + 5) / 10) * 10)` over the plotted points, recomputed on metric switch and league load, with the floor at 0 and the tick step chosen from the range. Verify in the browser that the title metric's axis top is the next multiple of 10 above its highest value, the playoff metric shows 0-100, and switching metrics rescales immediately.

## 5. Integration check

- [ ] 5.1 Take headless Chrome screenshots of both leagues in light and dark themes at desktop width and in the 375px iframe harness, in the default state, sorted by a chance column, and on the title metric, and verify: fills run from no fill at <1% to dark blue at >99% with readable text throughout, headers match the 538 format, no page-level horizontal scroll at 375px, the chart and table agree on the four metrics and their order, every team's line color matches its table swatch, and the title chart's axis fits its data.

## Workflow follow-up

- Archive `monte-carlo-playoff-odds` before applying this change, so the `league-odds-site` main spec exists for the MODIFIED requirements.
- When the ELO feature is built: populate `elo` and `elo_change` in the export, set `sortable: true` on the two ELO columns, and verify the change pill renders green/red with black text.
- Commit and push to `main`, then run the "Refresh odds" workflow (or wait for the daily run) and confirm the published site shows the new table.
