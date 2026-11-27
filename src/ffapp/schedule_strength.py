"""Strength of Schedule for the League sub-tab: Weekly Ranks and Schedule Swap for every stored season
of a league, exported as one file per league (``site/data/<league>/schedule.json``); the page only
renders. See Calculations.txt section 24.

Regular-season weeks only. A week is played once Sleeper has scored it; an upcoming week (including a
week in progress) takes each team's mean score and every pair's win share from the latest season
Forecast's ``upcoming`` block (the live result when there is one). A week with neither is left out.

- Weekly Ranks: each week a team's rank is 1 + the number of teams that scored more; each team is
  credited with its opponent's rank, averaged over played weeks, upcoming weeks and the season. The
  lowest season average is the hardest schedule.
- Schedule Swap: Manager A's wins with A's weekly scores against Manager B's opponent each week, A
  playing B in the weeks B's opponent is A. Played games count 1 / 0.5 / 0; upcoming games count the
  pair's win share. Schedule Difficulty Index = mean wins over all N schedules minus own wins; the
  highest is the hardest schedule.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import mean

from ffapp.managers import managers_for_league, roster_owners
from ffapp.odds import completed_weeks, regular_season_range
from ffapp.store import SeasonData, Store

log = logging.getLogger(__name__)


@dataclass
class Week:
    week: int
    upcoming: bool
    points: dict[int, float]  # roster id -> actual points, or the mean projected score
    opponent: dict[int, int]  # roster id -> opponent roster id
    win: dict[int, dict[int, float]] | None = None  # upcoming only: P(a outscores b), ties as half


def latest_forecast(store: Store, league_key: str, season: str) -> dict | None:
    """The live result when there is one, else the newest as-of result for the season."""
    live = store.read_live(league_key, season)
    if live:
        return live
    weeks = store.odds_weeks(league_key, season)
    return store.read_odds(league_key, season, max(weeks)) if weeks else None


def season_weeks(data: SeasonData, forecast: dict | None) -> list[Week]:
    """Every regular-season week with data: played from the stored matchups, upcoming from the Forecast."""
    played_through = completed_weeks(data.league)
    upcoming = (forecast or {}).get("upcoming") or {}
    out: list[Week] = []
    for week in regular_season_range(data.league):
        rows = data.matchups.get(week) or []
        pairs: dict[object, list[int]] = {}
        for r in rows:
            if r.get("matchup_id") is not None:
                pairs.setdefault(r["matchup_id"], []).append(int(r["roster_id"]))
        opponent = {a: b for p in pairs.values() if len(p) == 2 for a, b in (p, p[::-1])}
        if not opponent:
            continue
        if week <= played_through:
            points = {int(r["roster_id"]): float(r.get("points") or 0.0) for r in rows}
            out.append(Week(week, False, points, opponent))
        elif str(week) in upcoming:
            block = upcoming[str(week)]
            points = {int(k): float(v) for k, v in block["mean"].items()}
            win = {int(a): {int(b): float(p) for b, p in row.items()} for a, row in block["win"].items()}
            out.append(Week(week, True, points, opponent, win))
    return out


def weekly_ranks(weeks: list[Week]) -> dict[tuple[int, int], int]:
    """(week, roster id) -> 1 + the number of teams that scored more that week (4.10.2)."""
    return {(w.week, rid): 1 + sum(p > own for p in w.points.values()) for w in weeks for rid, own in w.points.items()}


def game_win(week: Week, a: int, b: int) -> float:
    """A's win value against B in one week: 1 / 0.5 / 0 when played, the win share when upcoming."""
    if week.upcoming:
        return week.win[a][b]
    pa, pb = week.points[a], week.points[b]
    return 1.0 if pa > pb else 0.5 if pa == pb else 0.0


def swap_wins(weeks: list[Week], a: int, b: int) -> float:
    """A's wins using A's scores against B's opponent each week, A playing B when that opponent is A."""
    total = 0.0
    for w in weeks:
        opp = w.opponent.get(b)
        if opp is None or a not in w.points:
            continue
        total += game_win(w, a, b if opp == a else opp)
    return total


def _rank(values: list[float], *, high_first: bool) -> list[int]:
    """Competition ranks (equal values share the better rank), values rounded as shown."""
    key = [round(v, 2) for v in values]
    return [1 + sum((o > v) if high_first else (o < v) for o in key) for v in key]


def season_export(data: SeasonData, owners: dict[int, str], forecast: dict | None) -> dict | None:
    weeks = season_weeks(data, forecast)
    if not weeks:
        return None
    rank = weekly_ranks(weeks)
    teams = sorted({rid for w in weeks for rid in w.opponent})
    played = [w for w in weeks if not w.upcoming]

    ranks = []
    for rid in teams:
        cells = [{"week": w.week, "opp": owners.get(w.opponent[rid]), "points": round(w.points[w.opponent[rid]], 1),
                  "opp_rank": rank[(w.week, w.opponent[rid])], "upcoming": w.upcoming} for w in weeks if rid in w.opponent]
        past = [c["opp_rank"] for c in cells if not c["upcoming"]]
        ahead = [c["opp_rank"] for c in cells if c["upcoming"]]
        wins = sum(game_win(w, rid, w.opponent[rid]) for w in played if rid in w.opponent)
        losses = sum(1 for w in played if rid in w.opponent and w.points[rid] < w.points[w.opponent[rid]])
        ties = sum(1 for w in played if rid in w.opponent and w.points[rid] == w.points[w.opponent[rid]])
        ranks.append({
            "user": owners.get(rid), "record": [int(wins - 0.5 * ties), losses, ties],
            "played": round(mean(past), 2) if past else None, "upcoming": round(mean(ahead), 2) if ahead else None,
            "season": round(mean(past + ahead), 2), "cells": cells,
        })
    for row, r in zip(ranks, _rank([x["season"] for x in ranks], high_first=False)):
        row["rank"] = r
    ranks.sort(key=lambda x: (x["rank"], x["season"]))

    table = {a: {b: swap_wins(weeks, a, b) for b in teams} for a in teams}
    rows = []
    for a in teams:
        own = table[a][a]
        avg = mean(table[a].values())
        rows.append({"rid": a, "user": owners.get(a), "own": round(own, 2), "avg": round(avg, 2), "index": round(avg - own, 2),
                     "lo": round(min(table[a].values()), 2), "hi": round(max(table[a].values()), 2)})
    for row, r in zip(rows, _rank([x["index"] for x in rows], high_first=True)):
        row["rank"] = r
    rows.sort(key=lambda x: (x["rank"], -x["index"]))
    order = [x["rid"] for x in rows]
    for row in rows:
        row["wins"] = [round(table[row["rid"]][b], 2) for b in order]
        del row["rid"]

    return {
        "weeks": [w.week for w in weeks],
        "played_through": max((w.week for w in played), default=None),
        "ranks": ranks,
        "swap": {"order": [owners.get(r) for r in order], "rows": rows},
    }


def schedule_export(store: Store, config, league_key: str) -> dict:
    """The strength of schedule file for one league: every stored season with any weeks (4.10)."""
    seasons = {}
    for season in store.seasons(league_key):
        data = store.read_season(league_key, season)
        entry = season_export(data, roster_owners(store, league_key, season), latest_forecast(store, league_key, season))
        if entry:
            seasons[season] = entry
    managers = managers_for_league(store, league_key)
    return {
        "league_key": league_key,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "current_season": max(seasons) if seasons else None,
        "managers": {u: {"name": m.name, "team_name": m.team_names.get(m.last), "logo": m.logo, "avatar": m.avatar, "current": m.current}
                     for u, m in managers.items()},
        "seasons": seasons,
    }
