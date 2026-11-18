"""Positional rankings: every manager's rostered players by position, rated by regular-season
points per game, for the site's Positions page.

Points per game blends what a player has scored with what he is projected to score:
actual points in the final regular-season weeks he played, plus his projected points for
the regular-season weeks not yet final (a projection above zero counts as a game), over
the number of those weeks. A week in progress is not final, so it counts as projected.
Completed seasons use each team's final roster; the season in progress uses the current
one. The dotted line on each chart is the position's WAR replacement level.

Built at export time from stored files (rosters, users, stats, projections, injury
statuses, WAR); nothing is written under ``data/``.
"""

from __future__ import annotations

import math

from ffapp.config import Config
from ffapp.espn import FANTASY_POSITIONS
from ffapp.injuries import OUT_STATUSES, statuses_for_week
from ffapp.league import owners, resolve_settings, starter_slots
from ffapp.odds import regular_season_range
from ffapp.scoring import record_points
from ffapp.stats import actual_points, played
from ffapp.store import Store
from ffapp.war import read_war, scored_weeks

POSITION_ORDER = ("QB", "RB", "WR", "TE", "K", "DEF")
AXIS_STEP = 5.0
AXIS_QUANTILE = 0.99


def lineup_positions(league: dict) -> list[str]:
    """The positions the league starts, in chart order (FLEX is not a position of its own)."""
    slots = set(starter_slots(league))
    return [pos for pos in POSITION_ORDER if pos in slots and pos in FANTASY_POSITIONS]


def _player_info(pid: str, records: list[dict | None]) -> tuple[str, str | None, str | None]:
    """Name, position and NFL team from the most recent record that has them."""
    name, position, team = None, None, None
    for rec in records:
        if not rec:
            continue
        if name is None:
            full = f"{rec.get('first_name') or ''} {rec.get('last_name') or ''}".strip()
            name = full or None
        position = position or rec.get("position")
        team = team or rec.get("team")
        if name and position and team:
            break
    return name or pid, position, team


def build_positions(store: Store, config: Config, league_key: str, season: str) -> dict:
    """One league-season's rankings (without axis ranges, which span all seasons)."""
    data = store.read_season(league_key, season)
    regular = list(regular_season_range(data.league))
    final = scored_weeks(store, data)
    remaining = [w for w in regular if w not in final]
    positions = lineup_positions(data.league)
    in_progress = data.status != "complete"

    stats = {w: store.read_stats(season, w) for w in final}
    projections = {w: store.read_projections(season, w) for w in remaining}
    scoring = {w: resolve_settings(config, league_key, data.league, w) for w in regular}
    statuses = (statuses_for_week(store, season, 99) or {}) if in_progress else {}

    war = read_war(store, league_key, season) or {}
    replacement = {pos: (war.get("replacement") or {}).get(pos, {}).get("level") for pos in positions}

    by_roster = owners(data.users, data.rosters)
    teams = []
    for roster in sorted(data.rosters, key=lambda r: int(r["roster_id"])):
        taxi = {str(p) for p in roster.get("taxi") or []}
        reserve = {str(p) for p in roster.get("reserve") or []}
        ids = list(dict.fromkeys(str(p) for p in [*(roster.get("players") or []), *taxi, *reserve]))
        players = []
        for pid in ids:
            # newest first, so name and team reflect the player's latest record
            recent = [stats[w].get(pid) for w in reversed(final)] + [projections[w].get(pid) for w in remaining]
            name, position, team = _player_info(pid, recent)
            if position not in positions:
                continue
            points, games, projected = 0.0, 0, 0
            for w in final:
                row = stats[w].get(pid)
                if row and played(row):
                    points += actual_points(row, scoring[w])
                    games += 1
            for w in remaining:
                value = record_points(projections[w].get(pid), scoring[w])
                if value > 0:
                    points += value
                    projected += 1
            if games + projected == 0 or points == 0:
                continue
            players.append({
                "id": pid,
                "name": name,
                "position": position,
                "team": team,
                "ppg": round(points / (games + projected), 2),
                "games": games,
                "projected": projected,
                "taxi": pid in taxi,
                "reserve": pid in reserve,
                "injured": statuses.get(pid) in OUT_STATUSES,
                "status": OUT_STATUSES.get(statuses.get(pid, "")),
            })
        players.sort(key=lambda p: (POSITION_ORDER.index(p["position"]), -p["ppg"], p["id"]))
        owner = by_roster.get(int(roster["roster_id"]))
        teams.append({
            "roster_id": int(roster["roster_id"]),
            "owner_id": owner.user_id if owner else None,
            "display_name": owner.display_name if owner else None,
            "team_name": owner.team_name if owner else None,
            "players": players,
        })
    return {
        "league_key": league_key,
        "season": season,
        "status": "in_progress" if in_progress else "complete",
        "weeks": regular,
        "final_through": final[-1] if final else 0,
        "positions": {pos: {"replacement": None if replacement[pos] is None else round(replacement[pos], 2)} for pos in positions},
        "teams": teams,
    }


def _quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    k = (len(ordered) - 1) * q
    lo, hi = math.floor(k), math.ceil(k)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (k - lo)


def axis_ranges(seasons: list[dict]) -> dict[str, list[float]]:
    """Per position, one range for every season: about 99% of points-per-game values inside,
    rounded outward to multiples of 5, always including zero and the highest replacement level."""
    values: dict[str, list[float]] = {}
    replacement: dict[str, float] = {}
    for payload in seasons:
        for pos, info in payload["positions"].items():
            values.setdefault(pos, [])
            if info.get("replacement") is not None:
                replacement[pos] = max(replacement.get(pos, 0.0), info["replacement"])
        for team in payload["teams"]:
            for player in team["players"]:
                values.setdefault(player["position"], []).append(player["ppg"])
    ranges = {}
    for pos, vals in values.items():
        low = min(0.0, math.floor(_quantile(vals, 1 - AXIS_QUANTILE) / AXIS_STEP) * AXIS_STEP)
        top = max(_quantile(vals, AXIS_QUANTILE), replacement.get(pos, 0.0), AXIS_STEP)
        high = math.ceil(top / AXIS_STEP) * AXIS_STEP
        if high == top:  # a value exactly on the edge still gets room for its dot
            high += AXIS_STEP
        ranges[pos] = [low, high]
    return ranges


def positions_export(store: Store, config: Config, league_key: str) -> dict | None:
    """Per stored season: the rankings with the league's shared axis ranges, plus an index."""
    seasons = store.seasons(league_key)
    if not seasons:
        return None
    payloads = {season: build_positions(store, config, league_key, season) for season in seasons}
    ranges = axis_ranges(list(payloads.values()))
    for payload in payloads.values():
        for pos, info in payload["positions"].items():
            info["axis"] = ranges.get(pos, [0.0, AXIS_STEP])
    index = {
        "seasons": [{"season": s, "status": p["status"], "final_through": p["final_through"], "file": f"{s}.json"} for s, p in payloads.items()],
        "current": seasons[-1],
    }
    return {"index": index, "files": payloads}
