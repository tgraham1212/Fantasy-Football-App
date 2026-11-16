# Proposal

## Why

Between a season's last week and the next season's first, the table and chart show each manager's pre-reversion rating, so the preseason pull toward 1000 only becomes visible after week 1. The user wants the reverted rating shown as soon as the new season's draft has happened.

## What Changes

- The ratings file gains a week-0 "preseason" entry per member for every stored season whose draft is done (Sleeper status `in_season` or `complete`): the rating entering the season (reverted for returning managers, 1000 for newcomers), with carried career z and no weekly z. Seasons still in `pre_draft` or `drafting` get no entry.
- The export shows the preseason rating in the ELO column with an empty change cell until week 1 is scored; from week 1 the change is measured from the preseason entry.
- The rating chart plots the preseason point ("Pre") at each season start, so the reversion step is visible.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `manager-ratings`: preseason entries in the rating history.
- `league-odds-site`: ELO column and rating chart behaviour after the draft and before week 1.

## Impact

- `src/ffapp/ratings.py` (season iteration, week-0 entries, week list), `src/ffapp/export.py` (change rule), `site/app.js` (labels), tests, README data-file description.
- Rating files and site data grow by one entry per member per season.
