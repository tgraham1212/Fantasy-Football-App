"""Model and actual lineup views of finished and live games, and lineup choices.

Model view: each team's best legal lineup from its roster that week, every player at his last
projection before kickoff (the log's frozen value, else his stored projection), with the
week's projected replacement-level floor. Actual view: the starters the manager used at the
same projections. Both are simulated with the record's model and no results; during the live
week the actual view is the live forecast instead.

Lineup choices: the actual starters' points minus the model lineup's points, a replacement
fill counting the week's realised replacement level (projected level when none is stored).
During the live week only players whose games have kicked off count, fills once final.
"""

from __future__ import annotations

import copy
import zlib
from datetime import datetime

from ffapp.config import Config
from ffapp.forecast import histogram, win_probability
from ffapp.games import last_unlocked, record_lineup, record_wpa, simulate_fixed, week_games, game_key, player_team
from ffapp.league import resolve_settings, starter_slots
from ffapp.lineup import Candidate, best_lineup
from ffapp.noise import NoiseModel
from ffapp.odds import apply_floor
from ffapp.replacement import read_replacement, weekly_level
from ffapp.schedule import Schedule
from ffapp.scoring import record_points
from ffapp.store import SeasonData, Store


def entries_by_team(log_by_key: dict) -> dict[int, list[dict]]:
    out: dict[int, list[dict]] = {}
    for entries in (log_by_key or {}).values():
        for entry in entries:
            for rid in entry["teams"]:
                out.setdefault(int(rid), []).append(entry)
    for entries in out.values():
        entries.sort(key=lambda e: e["time"])
    return out


def frozen_projection(entries: list[dict], rid: int, pid: str, record: dict | None, scoring: dict[str, float]) -> float | None:
    """Last logged projection before kickoff, else the stored projection; None when neither exists."""
    logged = last_unlocked(entries, rid, pid)
    if logged is not False and logged is not None:
        return float(logged)
    return record_points(record, scoring) if record else None


def model_lineup(
    row: dict,
    slots: list[str],
    entries: list[dict],
    projections: dict[str, dict],
    scoring: dict[str, float],
    floor: dict[str, float] | None,
    crosswalk: dict[str, dict],
) -> list[list]:
    """``[slot, player_id, position, projected]`` rows of the best lineup at frozen projections (None id = fill)."""
    rid = int(row["roster_id"])
    candidates = []
    for pid in (str(p) for p in row.get("players") or []):
        record = projections.get(pid)
        value = frozen_projection(entries, rid, pid, record, scoring)
        position = (record or {}).get("position") or (crosswalk.get(pid) or {}).get("position")
        if value is None or not position:
            continue
        positions = tuple((record or {}).get("fantasy_positions") or [position])
        candidates.append(Candidate(pid, position, positions, value))
    lineup = best_lineup(slots, candidates)
    if floor is not None:
        lineup = apply_floor(lineup, slots, floor)
    by_slot: dict[str, list] = {}
    for s in lineup:
        by_slot.setdefault(s.slot, []).append(s)
    rows = []
    for slot in slots:  # slot order, like the actual lineup
        s = by_slot.get(slot, []).pop(0) if by_slot.get(slot) else None
        if s is None:
            continue
        rows.append([slot, None if s.player_id.startswith("FA:") else s.player_id, s.position, round(float(s.projected), 1)])
    return rows


def week_floor(store: Store, config: Config, data: SeasonData, week: int, projections: dict[str, dict], scoring: dict[str, float]) -> dict[str, float]:
    rostered = {str(p) for r in data.matchups.get(week, []) for p in (r.get("players") or [])}
    levels = weekly_level(projections, scoring, rostered, None, config.simulation.replacement_top_n)
    return {pos: level["projected"] for pos, level in levels.items()}


def simulate_view(lineups: dict[int, list[list]], games: list[tuple[dict, dict, str]], noise: NoiseModel, drift, seed: int, source: str) -> dict[str, dict]:
    totals = simulate_fixed(lineups, noise, drift, seed)
    out = {}
    for a, b, bracket in games:
        ra, rb = int(a["roster_id"]), int(b["roster_id"])
        sa, sb = totals[ra], totals[rb]
        pa = win_probability(sa, sb)
        out[game_key(ra, rb)] = {
            "source": source,
            "bracket": bracket,
            "teams": [
                {"roster_id": ra, "mean": round(float(sa.mean()), 2), "win_prob": round(pa, 4), "lineup": lineups[ra]},
                {"roster_id": rb, "mean": round(float(sb.mean()), 2), "win_prob": round(1.0 - pa, 4), "lineup": lineups[rb]},
            ],
            "hist": histogram(sa, sb),
            "margin_mean": round(float((sa - sb).mean()), 3),
            "margin_sd": round(float((sa - sb).std()), 3),
        }
    return out


def realised_levels(store: Store, league_key: str, season: str, week: int) -> dict[str, float]:
    levels = ((read_replacement(store, league_key, season) or {}).get("weeks") or {}).get(str(week)) or {}
    return {pos: float(v["realised"] if v.get("realised") is not None else v.get("projected") or 0.0) for pos, v in levels.items()}


def lineup_choices(actual_rows: list[list], model_rows: list[list], points: dict[str, float], fills: dict[str, float], counted) -> float:
    """Actual starters' points minus the model lineup's points; ``counted(pid)`` limits players (live week),
    ``fills`` is {position: level} for replacement fills, empty to leave fills out."""

    def total(rows: list[list]) -> float:
        out = 0.0
        for row in rows:
            pid, position = row[1], row[2]
            if pid is None:
                out += fills.get(position, 0.0) if fills else 0.0
            elif counted(pid):
                out += float(points.get(pid, 0.0))
        return out

    return round(total(actual_rows) - total(model_rows), 1)


def build_views(
    store: Store,
    config: Config,
    league_key: str,
    data: SeasonData,
    week: int,
    stored: dict,
    noise: NoiseModel,
    drift,
    *,
    live: bool = False,
    now: datetime | None = None,
) -> dict[str, dict]:
    """``{game key: {"model": view, "actual": view}}`` for a finished or live week."""
    season = data.season
    slots = starter_slots(data.league)
    scoring = resolve_settings(config, league_key, data.league, week)
    projections = store.read_projections(season, week)
    crosswalk = store.read_crosswalk() or {}
    games = week_games(data, week)
    rows = {int(r["roster_id"]): r for r in data.matchups.get(week, [])}
    entries = entries_by_team(stored.get("log") or {})
    floor = week_floor(store, config, data, week, projections, scoring)
    has_log = any(stored.get("log", {}).values())
    record = stored.get("record") or {}

    # model view: always simulated from frozen projections, except pre-log weeks keep the pre-week forecast
    if has_log or live:
        model_lineups = {rid: model_lineup(rows[rid], slots, entries.get(rid, []), projections, scoring, floor, crosswalk) for a, b, _ in games for rid in (int(a["roster_id"]), int(b["roster_id"]))}
        model = simulate_view(model_lineups, games, noise, drift, zlib.crc32(f"model:{league_key}:{season}:{week}".encode()), "model")
    else:
        model = {g["key"]: {**copy.deepcopy(g), "source": "pre-week"} for g in record.get("games", [])}

    # actual view
    if live:
        forecast = stored.get("forecast") or {}
        actual = {game_key(*(t["roster_id"] for t in g["teams"])): {**copy.deepcopy(g), "source": "live"} for g in forecast.get("games", [])}
    elif has_log:
        actual = {g["key"]: {**copy.deepcopy(g), "source": "log"} for g in record.get("games", [])}
    else:
        actual_lineups = {rid: record_lineup(rows[rid], slots, [], projections, scoring, crosswalk) for a, b, _ in games for rid in (int(a["roster_id"]), int(b["roster_id"]))}
        actual = simulate_view(actual_lineups, games, noise, drift, zlib.crc32(f"actual:{league_key}:{season}:{week}".encode()), "rebuilt")
        record_wpa({"source": "log", "games": [{"key": k, **v} for k, v in actual.items()]}, data, week, projections, scoring, crosswalk, noise)

    # lineup choices on both views
    fills = {} if live else realised_levels(store, league_key, season, week)
    schedule = Schedule(store, season)

    def counted_for(pid: str) -> bool:
        if not live:
            return True
        team = player_team(pid, projections.get(pid), crosswalk)
        return bool(team) and schedule.kicked_off(week, team, now)

    views = {}
    for key in actual:
        if key not in model:
            continue
        for side in (0, 1):
            rid = actual[key]["teams"][side]["roster_id"]
            row = rows.get(int(rid)) or {}
            points = {str(k): float(v or 0.0) for k, v in (row.get("players_points") or {}).items()}
            model_team = next(t for t in model[key]["teams"] if t["roster_id"] == rid)
            choice = lineup_choices(actual[key]["teams"][side]["lineup"], model_team["lineup"], points, fills, counted_for)
            actual[key]["teams"][side]["lineup_choices"] = choice
            model_team["lineup_choices"] = choice
        views[key] = {"model": model[key], "actual": actual[key]}
    return views
