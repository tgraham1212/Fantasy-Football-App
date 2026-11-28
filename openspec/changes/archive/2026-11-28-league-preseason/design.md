# Design

## Context

See proposal.md (Why). Current state the design builds on:

- **Season simulation (`src/ffapp/simulate.py`):** `simulate(inputs, noise, runs, seed)` scores each team-week from fixed `Starter` lists (`starter_score`: projected plus a residual from the `NoiseModel` pools). It then plays the schedule, seeds the teams and runs both brackets through `BracketRules`. Lineups are fixed per week, so there's no per-run substitution.
- **Replacement levels:** rebuilt each run into `data/replacement/<league>/<season>.json` (Calc 14), per position and week.
- **Season projections (probed 2026-11-27):**
  - **ESPN:** `seasons/<s>/players?scoringPeriodId=0&view=kona_player_info` carries `stats[]` entries with `statSourceId` 1 and `statSplitTypeId` 0. That's the preseason season line, as ESPN stat ids: 3 pass yds, 4 pass TD, 20 INT, 24 rush yds, 25 rush TD, 53 receptions, 42 rec yds, 43 rec TD, 72 fumbles lost, plus kicking and defence ids. The lines survive early injuries (McCaffrey 2024, Nabers 2025). 2023 lines are blank for many top Players.
  - **Sleeper:** its season projections are wiped for some injured Players (Rodgers and Chubb 2023, Rice 2024).
  - **Week-1 Projections:** stored in `data/projections/<s>/week_01.json` for every season.
- **ESPN to Sleeper ids:** `data/espn/crosswalk.json` matched only about a third of drafted Players in a prototype. A name, position and team match left 13 of 168 unmatched, nearly all name suffixes.
- **Bye weeks:** the NFL schedule is stored for 2026 only. Each team's played weeks can be read from the weekly stats lines, as `draft.py` already does.
- **Prototype (scratchpad, 2025 redraft):** a credible spread, from an A+ (30% title share) to four D- teams and no F, and Wins Saved of +0.02 to +0.39.

## Goals / Non-Goals

**Goals:**
- One preseason Forecast per league-season, made once, and reproducible from its stored record.
- The existing season simulation, with standings, seeding and brackets unchanged, fed by preseason values and per-run absences.
- The grade bands applied exactly as specified, and checked against every stored season with the owner before going live.

**Non-Goals:**
- No change to in-season Forecasts. In-season runs keep their fixed lineups and real out statuses.
- No roster drift and no in-season moves: the preseason Forecast judges the draft as it stood.
- No re-grading after the fact, and no ESPN data for anything else.

## Decisions

1. **Values from full-season stat lines.**
   - **Scoring:** ESPN stat ids are mapped to the league's own scoring keys and scored with `scoring.projected_points` and that league-season's scoring settings, then divided by 17.
   - **Kickers and defences:** ESPN scores them with stat ids of their own and serves `appliedTotal` = 0, so they take their week-1 Projection, scored with the league's scoring. Their values are small and they're often streamed, so one week's matchup matters little.
   - **Replacement level (preseason scale):** the mean value of the 3 best Players at each position on no roster, from the same projections. Calc 14's weekly levels come from in-season Projections and sit on a different scale: a replacement QB there was worth more than many drafted QBs' preseason values.
   - **Replacement fill-ins** carry the same residual noise as Players, so bench and replacement compare like for like.
   - **2023:** Sleeper's season projections (`pts_half_ppr` keys from the stored stat line, scored the same way), else the week-1 Projection as the per-game value.
   - **Alternative:** week-1 Projections for every season. Rejected by the owner: one week's matchup moves every value.

2. **Matching.**
   - **Players:** normalise the names (lower case, punctuation removed, suffixes Jr/Sr/II/III/IV/V removed), then match on name and position, then NFL team as a tie-break.
   - **Defences:** matched by team.
   - **Unmatched drafted Players:** listed in the record. A drafted Player with no line scores replacement level and is flagged, so the owner can see who fell through.

3. **The simulation hook.**
   - **Hook:** `simulate()` gains an optional `weekly_scores(week, rng) -> (runs, n)` hook. With the hook set, it replaces `simulated_scores`; everything after (standings, seeds, brackets) is untouched.
   - **Absences:** `src/ffapp/preseason.py` builds that hook. For each team-week it draws an absence mask over the rostered Players (runs × Players, Bernoulli at the position rate; byes count as absent).
   - **Lineups:** slots are filled in the league's lineup order. Each slot takes the highest-valued healthy, unused, eligible Player (FLEX: RB, WR or TE), vectorised over runs. Each candidate list is at most about 16 Players, and there are 9 to 10 slots.
   - **Scores:** each chosen Player scores his value plus a `NoiseModel` residual, the same score error as the Forecasts. An unfilled slot scores the position's replacement level.
   - **Settings:** runs 10,000; seed `default_seed(league, season, 0) + 1`.
   - **Alternative:** a separate simulator. That duplicates the standings and bracket rules, which must match the Forecasts.

4. **Wins Saved:** for each team, another run with the same seed and draws in which only that team's injured starters give way to replacement level, while every other team keeps its bench. Taking every bench away at once was tried and rejected: a team's relative wins then fall when its rivals' benches are deeper. Wins Saved = mean wins (bench) − mean wins (that team without its bench). The draws are common, so the difference isn't swamped by noise. That's 13 runs per league-season.

5. **Grades:** computed in Python from the shares by the bands in `preseason-forecast` 1.5.5 and 1.5.5.1. They're stored in the record and the page only shows them.

6. **The record:** `data/preseason/<league>/<season>.json` holds:
   - `made_at`;
   - `sources` (which projection source each Player used);
   - `values {pid: per_game}`;
   - `rosters {roster_id: [pid]}`;
   - `unmatched`;
   - the replacement levels used;
   - `teams [{roster_id, title, playoffs, last, wins, losses, ppg, wins_saved, grade}]`;
   - `runs` and `seed`.

   It's written once and never rewritten (1.5), and the actual finish is joined at export from the stored brackets. Keeping the values in the record makes the Forecast reproducible even if ESPN later changes its data.

7. **When it runs:** a `preseason` CLI command and an optional cold-run step after `replacement`, which needs the season's replacement levels.
   - **What it does:** it makes a Forecast for each league-season with a complete draft (`data/leagues/.../draft.json`), preseason values available, and no stored record.
   - **The first run** backfills redraft 2021 to 2026 and dynasty 2022 to 2026.
   - **A failure** warns and leaves no record, so the next run tries again.

8. **The export:** `site/data/<league>/preseason.json` = `{managers, latest, seasons {s: {made_at, final, teams [... + user, finish]}}}`.

9. **The page:** a new `site/preseason.js` following `site/draft.js`.
   - **Tab and route:** a fourth `#lg-tabs` button, with the route `#<league>/league/preseason/<season>`.
   - **Table:** sortable; each share bar is a fixed-width track with a fill whose width is the share.
   - **Phones:** list rows, as in the mockup.
   - **Grade colours:** 13 `--grade-*-f/i` token pairs, as hex with OKLCH notes. Light values are from the PreseasonGrades artboard. Dark values are derived by changing lightness only, and every pair is added to `tests/test_colour_contrast.py`.

10. **Redraft grades and the backtest (owner's decision, 2026-11-27).**
    - **Finding:** replayed over every season, preseason strength predicts dynasty results well. Points per week correlate 0.55 with actual, a slope of 1.02. It doesn't predict redraft: correlation −0.13 and a slope of −0.72. Redraft rosters come out of the draft within about 2 points a week of each other (sd 2.1), and in-season injuries, moves and luck spread them by 8.8.
    - **What was tried:** the leagues' roster drift barely moved the grades. A per-league calibration (shrinking each edge by the measured slope, plus a season-long team spread) turned redraft into nearly all C's.
    - **Decision:** keep the model unchanged, and add a Draft Strength rank (preseason points per week) to the redraft table.
    - **Backlog:** a redraft revision built around positional and starter/bench draft rankings.
    - **Drift on the hook path:** the `simulate` hook still applies roster drift when inputs carry a drift model, so both paths behave the same. The preseason Forecast passes none.

## Risks / Trade-offs

- **[ESPN changes or removes past season projections]** → The record stores each Player's value, so a made Forecast never depends on ESPN again. Only an unmade season would need another source.
- **[Name matching misses Players]** → Unmatched drafted Players are listed in the record and the docs. The backfill task reports the count per season, and the owner reviews it with the grade counts.
- **[Pooled injury rates are rough]** → They're constants in Calc 26 with their source and date, and can be re-measured each year.
- **[A preseason grade is often wrong (the 2025 A+ finished last)]** → That's expected, and the Finished column shows it. The note says what the grade is: the drafted roster's outlook before any moves.
- **[Simulation time]** → Two runs of 10,000 per league-season, about a minute each. The backfill happens once, and a new season adds two runs at most.

## Migration Plan

- **First deploy:** the first cold run after deploy backfills the 11 league-season records, which are committed like other records.
- **Rollback:** remove the tab, the export and the step. The records are harmless.
