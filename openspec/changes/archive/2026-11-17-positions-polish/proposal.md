# Proposal

## Why

The first live version of the Positions page works, but four things read badly:

- A chart beside a taller neighbour leaves its card half empty.
- Rows show only a team name, while the Predictions and Games tabs show the manager with the team name beneath.
- The top player's name slides away from its dot near the chart edge.
- The popup doesn't say why a dot has a red cross or a dotted outline.

Two data issues surfaced while looking at those. First, the site has three different lists of "statuses that keep a player out", so it can disagree with itself:
- the Games cards' not-playing list: Out, Doubtful, IR, PUP, Sus
- the WAR ownership fallback: IR, Out, PUP, Sus, NA, DNR
- the Positions page: IR and Out only

Second, the one vacant roster in the stored data (dynasty 2023, roster 11, previously DeekBurg's) shows as "Unknown owner 11", and its season is rated under an anonymous vacant entry. The owner most likely quit before the league year officially ended, after playing the season.

## What Changes

- **Charts fill their cards.** On desktop, the two charts in one grid row use the same row height, so neither card is left half empty.
- **Manager and team labels.** Each chart row shows the manager's display name, with the team name in small muted text beneath, as on the Predictions and Games tabs. There is no colour swatch.
- **Top name centred.** The top player's last name stays centred over his dot even when it overhangs the plot. It shifts only as far as needed to stay inside the card.
- **Popup reasons.**
  - A player with an out status shows it in red, as a readable label: Out, Doubtful, IR, PUP, Suspended, Not active, or Did not report.
  - A taxi player shows "Taxi" in a new gold colour: dark gold in light mode, bright yellow in dark mode, readable on the popup in both.
- **One shared out-status list:** Out, Doubtful, IR, PUP, Sus, NA, DNR, each with one display label. It drives:
  - the red cross and popup on Positions; the positions data carries the status itself, not only a flag
  - the Games cards' "not playing" list, which gains NA and DNR and uses the shared labels (PUP and Sus were shown as "Out"); the simulation itself is unchanged and still reads projections
  - the WAR ownership fallback, which gains Doubtful
- **Vacant rosters inherit their last owner.** A roster with no owner in a season takes the most recent owner of that roster slot in an earlier season, with that owner's last-known name and team name. If no earlier owner exists, it takes the first later one.
  - Every reader of stored rosters and users sees the inherited owner: Positions, Player WAR owners, odds and calibration labels, and manager ratings.
  - DeekBurg's rating history gains dynasty 2023, and other managers' ratings shift slightly as a result.
  - A roster with no owner in any stored season stays vacant, as today.
  - The raw stored files are not changed.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `sleeper-league-sync`: "Owner identity" adds the vacant-roster fallback to the last earlier owner, or else the first later one.
- `manager-ratings`: "Ratings follow the manager". A vacant roster is rated under its inherited owner, and only a roster with no owner in any stored season is a vacant entry.
- `league-odds-site`: "Manager colours on the rating chart". The hidden vacant line applies only to a roster with no owner in any stored season.
- `injury-history`: "Not-playing status for a week" uses the shared out-status list and labels.
- `games-page`: "Not playing" lists the shared statuses with their labels.
- `player-war`: "Yearly and weekly cut". The ownership fallback uses the shared out-status list, which adds Doubtful.
- `positional-rankings`: "Injury flag" uses the shared list and records the status. "Positional rankings file contents" carries the status.
- `positional-rankings-page`:
  - "Position charts" gets manager and team labels and equal row heights per grid row.
  - "Top player label" centres the name over the dot.
  - "Dot hover" adds the status and taxi lines.

## Impact

- **Code:**
  - `src/ffapp/injuries.py`: the shared out-status list and labels.
  - `src/ffapp/store.py`: rosters and users read with the vacant fallback.
  - `src/ffapp/war.py`, `src/ffapp/positions.py`: use the shared list. The export carries the status.
  - `site/positions.js`, `site/styles.css`: labels, equal heights, centred name, popup lines, gold token.
  - `site/games.js`: the not-playing labels, if rendered client-side.
- **Data regenerated:** ratings, WAR, games, odds labels and the site export. Dynasty ratings change for 2023 onward. Past seasons' WAR owners for roster 11 become DeekBurg.
- **Tests:**
  - store fallback (earlier owner, later owner, never owned)
  - shared statuses in injuries, WAR and positions
  - ratings crediting the inherited owner
  - layout check: equal heights, the top name inside the card, the popup lines
- No new dependencies.
