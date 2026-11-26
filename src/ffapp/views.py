"""Model and actual lineup views of finished and live games, and lineup choices.

Model view: each team's best legal lineup from its roster that week, every player at his last
projection before kickoff (the log's frozen value, else his stored projection), with the
week's projected replacement-level floor. Actual view: the starters the manager used at the
same projections. Both are simulated with the record's model and no results; during the live
week the actual view is the live forecast instead.

Lineup choices: the actual starters' points minus the default lineup's points. The default lineup
is the best legal lineup from the week's rostered players at the same frozen projections, with no
free-agent fills, so following the projections scores 0. An empty slot counts 0 on either side.
During the live week only players whose games have kicked off count.
"""

from __future__ import annotations

import copy
import zlib
from datetime import datetime

from ffapp.config import Config
from ffapp.forecast import histogram, win_probability
from ffapp.games import LINEUP_BASIS, last_unlocked, record_lineup, record_wpa, simulate_fixed, week_games, game_key, player_team
from ffapp.league import resolve_settings, starter_slots
from ffapp.lineup import Candidate, best_lineup
from ffapp.noise import NoiseModel
from ffapp.odds import apply_floor
from ffapp.replacement import weekly_level
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
    first: list[Candidate] | None = None,
) -> list[list]:
    """``[slot, player_id, position, projected]`` rows of the best lineup at frozen projections (None id = fill).
    ``first`` are players placed before any projected one (projected ``inf``, listed as 0.0)."""
    rid = int(row["roster_id"])
    candidates = list(first or [])
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
        projected = 0.0 if s.projected == float("inf") else round(float(s.projected), 1)
        rows.append([slot, None if s.player_id.startswith("FA:") else s.player_id, s.position, projected])
    return rows


def default_lineup(
    row: dict,
    slots: list[str],
    entries: list[dict],
    projections: dict[str, dict],
    scoring: dict[str, float],
    crosswalk: dict[str, dict],
) -> list[list]:
    """What lineup choices are measured against: the best legal lineup from the week's rostered players
    at frozen projections, with no replacement floor (a slot nobody can fill is left out). A starter with
    no projection at all has no default to judge him by, so he is placed in the default lineup first and
    counts the same on both sides."""
    rid = int(row["roster_id"])
    unprojected = []
    for pid in (str(p) for p in row.get("starters") or []):
        if pid in ("0", "", "None") or frozen_projection(entries, rid, pid, projections.get(pid), scoring) is not None:
            continue
        position = (crosswalk.get(pid) or {}).get("position")
        if position:
            unprojected.append(Candidate(pid, position, (position,), float("inf")))
    return model_lineup(row, slots, entries, projections, scoring, None, crosswalk, first=unprojected)


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


def lineup_choices(actual_rows: list[list], default_rows: list[list], points: dict[str, float], counted) -> float:
    """Actual starters' points minus the default lineup's points; an empty slot counts 0 on either side and
    ``counted(pid)`` limits players (the live week: only games that have kicked off)."""

    def total(rows: list[list]) -> float:
        return sum(float(points.get(row[1], 0.0)) for row in rows if row[1] is not None and counted(row[1]))

    return round(total(actual_rows) - total(default_rows), 1)


def stored_lineup_choices(derived: dict | None) -> dict[int, float]:
    """roster_id -> lineup choices from a stored week of game views; {} when none are stored or they
    follow an earlier rule (no current ``lineup_basis``)."""
    if (derived or {}).get("lineup_basis") != LINEUP_BASIS:
        return {}
    out: dict[int, float] = {}
    for views in (derived.get("views") or {}).values():
        for team in (views.get("actual") or {}).get("teams") or []:
            if team.get("lineup_choices") is not None:
                out[int(team["roster_id"])] = float(team["lineup_choices"])
    return out


def season_lineup_choices(store: Store, config: Config, league_key: str, data: SeasonData) -> dict[tuple[int, int], float]:
    """(week, roster_id) -> lineup choices for every finished regular-season week of a season.

    Weeks whose stored game views follow the current rule keep their values. Other weeks are computed
    the same way: the starters from the matchup against the default lineup, at the game log's frozen
    projections where the week has a log (from 2026), else that week's stored projections, which are
    the last stored each week and not always the exact pre-kickoff figures."""
    from ffapp.odds import completed_weeks, regular_season_range
    from ffapp.store import read_json

    season = data.season
    done = completed_weeks(data.league)
    slots = starter_slots(data.league)
    crosswalk = store.read_crosswalk() or {}
    out: dict[tuple[int, int], float] = {}
    for week in regular_season_range(data.league):
        if week > done:
            break
        rows = {int(r["roster_id"]): r for r in data.matchups.get(week, []) if r.get("matchup_id") is not None}
        if not rows:
            continue
        path = store.games_derived_path(league_key, season, week)
        stored = stored_lineup_choices(read_json(path) if path.exists() else None)
        if stored:
            out.update({(week, rid): value for rid, value in stored.items() if rid in rows})
            continue
        projections = store.read_projections(season, week)
        if not projections:
            continue
        scoring = resolve_settings(config, league_key, data.league, week)
        entries = entries_by_team((store.read_games(league_key, season, week) or {}).get("log") or {})
        for rid, row in rows.items():
            default = default_lineup(row, slots, entries.get(rid, []), projections, scoring, crosswalk)
            actual = record_lineup(row, slots, entries.get(rid, []), projections, scoring, crosswalk)
            points = {str(k): float(v or 0.0) for k, v in (row.get("players_points") or {}).items()}
            out[(week, rid)] = lineup_choices(actual, default, points, lambda pid: True)
    return out


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

    views = {key: {"model": model[key], "actual": actual[key]} for key in actual if key in model}
    set_lineup_choices(store, config, league_key, data, week, stored, views, live=live, now=now)
    return views


def set_lineup_choices(
    store: Store,
    config: Config,
    league_key: str,
    data: SeasonData,
    week: int,
    stored: dict,
    views: dict[str, dict],
    *,
    live: bool = False,
    now: datetime | None = None,
) -> None:
    """Write each team's lineup choices onto both of its views: the actual view's starters against the
    default lineup (rostered players at frozen projections, no free-agent fills)."""
    season = data.season
    slots = starter_slots(data.league)
    scoring = resolve_settings(config, league_key, data.league, week)
    projections = store.read_projections(season, week)
    crosswalk = store.read_crosswalk() or {}
    rows = {int(r["roster_id"]): r for r in data.matchups.get(week, [])}
    entries = entries_by_team(stored.get("log") or {})
    schedule = Schedule(store, season)

    def counted_for(pid: str) -> bool:
        if not live:
            return True
        team = player_team(pid, projections.get(pid), crosswalk)
        return bool(team) and schedule.kicked_off(week, team, now)

    for view in views.values():
        for team in view["actual"]["teams"]:
            rid = int(team["roster_id"])
            row = rows.get(rid) or {}
            points = {str(k): float(v or 0.0) for k, v in (row.get("players_points") or {}).items()}
            default = default_lineup(row, slots, entries.get(rid, []), projections, scoring, crosswalk) if row else []
            choice = lineup_choices(team["lineup"], default, points, counted_for)
            team["lineup_choices"] = choice
            for other in view["model"]["teams"]:
                if int(other["roster_id"]) == rid:
                    other["lineup_choices"] = choice
