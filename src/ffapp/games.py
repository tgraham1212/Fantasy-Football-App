"""Game logs and predictions of record, one file per league, season and week.

Every run, each game of the current and later weeks gets a log entry: the run time, both
teams' model lineups and win probability from the latest simulation, and every rostered
player's projection with whether his NFL game has kicked off. An entry is added only when
something other than the time changed. A player who has kicked off keeps his last
projection from before kickoff in every later entry.

Once a week is final, each game's prediction of record is simulated from the lineup the
manager actually started, each player at his last logged projection before kickoff (else
his stored projection), with the same noise model and one week of roster drift. A week
played before the log existed falls back to the forecast made as of the week before it.

Storage: ``data/games/<league>/<season>/week_NN.json`` with ``log`` ({game key: [entries]}),
``forecast`` (the latest simulation's games for the week) and ``record``.
"""

from __future__ import annotations

import copy
import logging
import math
import zlib
from datetime import datetime, timedelta, timezone

import numpy as np

from ffapp.bracket import BracketRules
from ffapp.config import Config
from ffapp.drift import estimate_for_league
from ffapp.forecast import histogram, win_probability
from ffapp.league import resolve_settings, starter_slots
from ffapp.noise import NoiseModel, build_pools
from ffapp.odds import completed_weeks, current_season, regular_season_range
from ffapp.schedule import Schedule
from ffapp.scoring import record_points
from ffapp.standings import pairings
from ffapp.store import SeasonData, Store

log = logging.getLogger(__name__)

RECORD_RUNS = 10_000
EASTERN = timezone(timedelta(hours=-5))  # fallback lock time when no schedule is stored: midnight Eastern on game day


def season_weeks(league: dict) -> list[int]:
    rules = BracketRules.from_league(league)
    return list(regular_season_range(league)) + [rules.week_for_round(r) for r in range(1, rules.rounds + 1)]


def game_key(rid_a: int, rid_b: int) -> str:
    return "-".join(str(r) for r in sorted((int(rid_a), int(rid_b))))


# -- locks ------------------------------------------------------------------------------------


def player_team(pid: str, projection: dict | None, crosswalk: dict[str, dict]) -> str | None:
    if projection and projection.get("team"):
        return str(projection["team"])
    cw = crosswalk.get(pid) or {}
    if cw.get("team"):
        return str(cw["team"])
    return pid if pid.isalpha() and pid.isupper() else None  # defenses are keyed by team


def is_locked(schedule: Schedule, week: int, nfl_team: str | None, projection: dict | None, now: datetime) -> bool:
    if schedule.has_week(week):
        return schedule.kicked_off(week, nfl_team, now)
    date = (projection or {}).get("date")
    if not date:
        return False
    game_day = datetime.fromisoformat(str(date)).replace(tzinfo=EASTERN)
    return now >= game_day


# -- the log -------------------------------------------------------------------------------------


def last_unlocked(entries: list[dict], rid: int, pid: str) -> float | None | bool:
    """The player's projection in the latest entry where he was not locked; False when never seen unlocked."""
    for entry in reversed(entries):
        value = (entry.get("players") or {}).get(str(rid), {}).get(pid)
        if value is not None and not value[1]:
            return value[0]
    return False


def build_entry(
    game: dict,
    previous: list[dict],
    rosters: dict[int, list[str]],
    projections: dict[str, dict],
    scoring: dict[str, float],
    schedule: Schedule,
    week: int,
    crosswalk: dict[str, dict],
    now: datetime,
) -> dict:
    teams = [t["roster_id"] for t in game["teams"]]
    players: dict[str, dict[str, list]] = {}
    for rid in teams:
        rows = {}
        for pid in rosters.get(rid, []):
            record = projections.get(pid)
            locked = is_locked(schedule, week, player_team(pid, record, crosswalk), record, now)
            projected = None if record is None else round(record_points(record, scoring), 2)
            if locked:
                earlier = last_unlocked(previous, rid, pid)
                if earlier is not False:
                    projected = earlier
            rows[pid] = [projected, locked]
        players[str(rid)] = dict(sorted(rows.items()))
    return {
        "time": now.isoformat(timespec="seconds"),
        "teams": teams,
        "win_prob": [t["win_prob"] for t in game["teams"]],
        "lineups": [t["lineup"] for t in game["teams"]],
        "players": players,
    }


def same_entry(a: dict, b: dict) -> bool:
    return {k: v for k, v in a.items() if k != "time"} == {k: v for k, v in b.items() if k != "time"}


# -- prediction of record ---------------------------------------------------------------------------


def record_lineup(
    row: dict,
    slots: list[str],
    log_entries: list[dict],
    projections: dict[str, dict],
    scoring: dict[str, float],
    crosswalk: dict[str, dict],
) -> list[list]:
    """``[slot, player_id, position, projected]`` for the starters the manager actually used."""
    rid = int(row["roster_id"])
    starters = [str(p) for p in (row.get("starters") or [])]
    out = []
    for i, slot in enumerate(slots):
        pid = starters[i] if i < len(starters) else "0"
        if pid in ("0", "", "None"):
            out.append([slot, None, slot, 0.0])
            continue
        logged = last_unlocked(log_entries, rid, pid)
        record = projections.get(pid)
        if logged is not False and logged is not None:
            projected = float(logged)
        elif record is not None:
            projected = record_points(record, scoring)
        else:
            projected = 0.0
        position = (record or {}).get("position") or (crosswalk.get(pid) or {}).get("position") or slot
        out.append([slot, pid, position, round(projected, 1)])
    return out


def simulate_fixed(lineups: dict[int, list[list]], noise: NoiseModel, drift, seed: int, runs: int = RECORD_RUNS) -> dict[int, np.ndarray]:
    """Simulate one week of fixed lineups with the model's noise and one week of roster drift."""
    rng = np.random.default_rng(seed)
    totals = {}
    strength = {rid: sum(row[3] for row in rows) for rid, rows in lineups.items()}
    mean = float(np.mean(list(strength.values()))) if strength else 0.0
    for rid in sorted(lineups):
        total = np.zeros(runs)
        for slot, pid, position, projected in lineups[rid]:
            if pid is None and projected == 0.0:
                continue  # an empty starting slot scores nothing
            total += projected + noise.sample(position, projected, rng, runs)
        if drift is not None and not drift.identity:
            total += (drift.slope(1) - 1.0) * (strength[rid] - mean)
            sd = drift.step_sd(1)
            if sd > 0:
                total += rng.normal(0.0, sd, size=runs)
        totals[rid] = total
    return totals


def week_games(data: SeasonData, week: int) -> list[tuple[dict, dict, str]]:
    """The week's real games as (row, row, bracket); playoff weeks keep winners and toilet bowl games only."""
    rules = BracketRules.from_league(data.league)
    rows = data.matchups.get(week, [])
    if week < rules.playoff_week_start:
        return [(a, b, "regular") for a, b in pairings(rows)]
    round_no = week - rules.playoff_week_start + 1
    brackets = [("winners", data.winners_bracket)] + ([("losers", data.losers_bracket)] if rules.toilet_bowl else [])
    out = []
    for a, b in pairings(rows):
        pair = {int(a["roster_id"]), int(b["roster_id"])}
        for name, entries in brackets:
            if any(int(e.get("r", 0)) == round_no and {e.get("t1"), e.get("t2")} == pair for e in entries or []):
                out.append((a, b, name))
                break
    return out


def actuals(a: dict, b: dict) -> tuple[list[float], int | None]:
    pa, pb = float(a.get("points") or 0.0), float(b.get("points") or 0.0)
    winner = int(a["roster_id"]) if pa > pb else int(b["roster_id"]) if pb > pa else None
    return [round(pa, 2), round(pb, 2)], winner


def record_from_log(
    store: Store, config: Config, league_key: str, data: SeasonData, week: int, log_by_key: dict[str, list[dict]],
    noise: NoiseModel, drift,
) -> dict:
    slots = starter_slots(data.league)
    scoring = resolve_settings(config, league_key, data.league, week)
    projections = store.read_projections(data.season, week)
    crosswalk = store.read_crosswalk() or {}
    games = week_games(data, week)
    entries_for: dict[int, list[dict]] = {}
    for entries in log_by_key.values():
        for entry in entries:
            for rid in entry["teams"]:
                entries_for.setdefault(int(rid), []).append(entry)
    for entries in entries_for.values():
        entries.sort(key=lambda e: e["time"])
    lineups = {}
    for a, b, _ in games:
        for row in (a, b):
            rid = int(row["roster_id"])
            lineups[rid] = record_lineup(row, slots, entries_for.get(rid, []), projections, scoring, crosswalk)
    seed = zlib.crc32(f"record:{league_key}:{data.season}:{week}".encode())
    totals = simulate_fixed(lineups, noise, drift, seed)
    out = []
    for a, b, bracket in games:
        ra, rb = int(a["roster_id"]), int(b["roster_id"])
        sa, sb = totals[ra], totals[rb]
        pa = win_probability(sa, sb)
        scores, winner = actuals(a, b)
        out.append(
            {
                "key": game_key(ra, rb),
                "bracket": bracket,
                "teams": [
                    {"roster_id": ra, "mean": round(float(sa.mean()), 2), "win_prob": round(pa, 4), "lineup": lineups[ra]},
                    {"roster_id": rb, "mean": round(float(sb.mean()), 2), "win_prob": round(1.0 - pa, 4), "lineup": lineups[rb]},
                ],
                "hist": histogram(sa, sb),
                "margin_mean": round(float((sa - sb).mean()), 3),
                "margin_sd": round(float((sa - sb).std()), 3),
                "actual": scores,
                "winner": winner,
            }
        )
    return {"source": "log", "runs": RECORD_RUNS, "games": out}


# -- win probability added ------------------------------------------------------------------------


def normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def margin_stats(game: dict) -> tuple[float, float]:
    """(mean, sd) of team A's margin: stored by newer runs, else from the two histograms as independent teams."""
    if game.get("margin_mean") is not None and game.get("margin_sd"):
        return float(game["margin_mean"]), float(game["margin_sd"])
    hist = game["hist"]
    stats = []
    for shares in hist["shares"]:
        total = float(sum(shares)) or 1.0
        mids = [hist["start"] + hist["width"] * (i + 0.5) for i in range(len(shares))]
        mean = sum(m * s for m, s in zip(mids, shares)) / total
        var = sum((m - mean) ** 2 * s for m, s in zip(mids, shares)) / total
        stats.append((mean, var))
    mean_a = float(game["teams"][0].get("mean", stats[0][0]))
    mean_b = float(game["teams"][1].get("mean", stats[1][0]))
    return mean_a - mean_b, math.sqrt(stats[0][1] + stats[1][1])


def win_probability_added(margin: float, spread: float, projected: float, score: float, player_sd: float, share: float = 0.0) -> float:
    """Change in the team's win chance from one player's score against his projection, all else as projected.

    ``margin`` and ``spread`` are the team's pre-kickoff margin over the opponent; a finished player
    (``share`` 0) removes his whole variance, a player in progress keeps ``share`` of it.
    """
    spread = max(spread, 1e-9)
    before = normal_cdf(margin / spread)
    after_spread = math.sqrt(max(spread ** 2 - player_sd ** 2 * (1.0 - share), 1e-9))
    after = normal_cdf((margin + score - projected) / after_spread)
    return round(after - before, 3)


def team_wpa(
    side: int,
    margin: float,
    spread: float,
    starters: list[tuple[str, str, float, float, float]],
    noise: NoiseModel,
) -> dict[str, float]:
    """``{player_id: wpa}`` for ``(player_id, position, projected, score, share)`` starters, from one team's side."""
    out = {}
    for pid, position, projected, score, share in starters:
        sd = noise.spread(position, projected) if projected > 0 else noise.spread(position, 0.0)
        out[pid] = win_probability_added(side * margin, spread, projected, score, sd, share)
    return out


def record_wpa(record: dict, data: SeasonData, week: int, projections: dict[str, dict], scoring: dict[str, float],
               crosswalk: dict[str, dict], noise: NoiseModel) -> None:
    """Add ``wpa`` per team to every game of a final week's record: each real starter's score against his
    projection in the record (log records: the record lineup; pre-week records: his stored projection)."""
    rows = {int(r["roster_id"]): r for r in data.matchups.get(week, [])}
    for game in record.get("games", []):
        margin, spread = margin_stats(game)
        for side, team in zip((1, -1), game["teams"]):
            row = rows.get(int(team["roster_id"]))
            if row is None:
                continue
            in_lineup = {r[1]: r for r in team.get("lineup", []) if r[1]}
            points = {str(k): float(v or 0.0) for k, v in (row.get("players_points") or {}).items()}
            starters = []
            for pid in (str(p) for p in row.get("starters") or []):
                if pid in ("0", "", "None"):
                    continue
                record_row = projections.get(pid)
                if record.get("source") == "log" and pid in in_lineup:
                    projected, position = float(in_lineup[pid][3]), in_lineup[pid][2]
                else:
                    projected = record_points(record_row, scoring) if record_row else 0.0
                    position = (record_row or {}).get("position") or (crosswalk.get(pid) or {}).get("position") or "WR"
                starters.append((pid, position, projected, points.get(pid, 0.0), 0.0))
            team["wpa"] = team_wpa(side, margin, spread, starters, noise)


def live_baseline(store: Store, config: Config, league_key: str, data: SeasonData, week: int, log_by_key: dict, noise: NoiseModel, drift) -> dict:
    """Pre-kickoff margins for the live week's real games: the managers' current starters, each at his last
    logged projection before kickoff (players not yet locked: their latest projection)."""
    provisional = record_from_log(store, config, league_key, data, week, log_by_key, noise, drift)
    return {g["key"]: {"margin_mean": g["margin_mean"], "margin_sd": g["margin_sd"],
                       "lineups": {str(t["roster_id"]): t["lineup"] for t in g["teams"]}} for g in provisional["games"]}


def live_wpa(forecast: dict, baseline: dict, noise: NoiseModel) -> None:
    """Add ``wpa`` to each team of the live forecast for its locked starters (final or in progress)."""
    for game in forecast.get("games", []):
        base = baseline.get(game["key"])
        if base is None:
            continue
        for side, team in zip((1, -1), game["teams"]):
            base_rows = {r[1]: r for r in base["lineups"].get(str(team["roster_id"]), []) if r[1]}
            starters = []
            for row in team.get("lineup", []):
                if len(row) < 8 or row[1] is None:
                    continue
                pid, position, current_proj, status, points, _clock, share = row[1], row[2], row[3], row[4], row[5], row[6], row[7]
                projected = float(base_rows[pid][3]) if pid in base_rows else float(current_proj)
                score = float(points) + float(share) * projected  # in progress: projected final
                starters.append((pid, position, projected, score, float(share)))
            team["wpa"] = team_wpa(side, base["margin_mean"], base["margin_sd"], starters, noise)


def record_from_pre_week(store: Store, league_key: str, data: SeasonData, week: int) -> dict | None:
    payload = store.read_odds(league_key, data.season, week - 1)
    forecast = ((payload or {}).get("games") or {}).get(str(week))
    if not forecast:
        return None
    by_pair = {frozenset(t["roster_id"] for t in g["teams"]): g for g in forecast["games"]}
    out = []
    for a, b, bracket in week_games(data, week):
        ra, rb = int(a["roster_id"]), int(b["roster_id"])
        found = by_pair.get(frozenset((ra, rb)))
        if found is None:
            continue
        teams = sorted(found["teams"], key=lambda t: 0 if t["roster_id"] == ra else 1)
        hist = found["hist"]
        if teams[0]["roster_id"] != found["teams"][0]["roster_id"]:
            hist = {**hist, "shares": list(reversed(hist["shares"]))}
        scores, winner = actuals(a, b)
        out.append({"key": game_key(ra, rb), "bracket": bracket, "teams": teams, "hist": hist, "actual": scores, "winner": winner})
    return {"source": "pre-week", "as_of_week": week - 1, "games": out}


# -- the run ---------------------------------------------------------------------------------------


def update_games(store: Store, config: Config, league_key: str, *, now: datetime | None = None, force_records: bool = False) -> list[int]:
    """Append log entries for the current and later weeks and write records for final weeks; returns weeks written."""
    now = now or datetime.now(timezone.utc)
    season = current_season(store, league_key)
    if season is None:
        return []
    data = store.read_season(league_key, season)
    as_of = completed_weeks(data.league)
    live = store.read_live(league_key, season)
    payload = live if live and live.get("as_of_week") == as_of else store.read_odds(league_key, season, as_of)
    forecasts = (payload or {}).get("games") or {}
    schedule = Schedule(store, season)
    crosswalk = store.read_crosswalk() or {}
    rosters = {int(r["roster_id"]): [str(p) for p in (r.get("players") or [])] for r in data.rosters}
    written = []
    noise = drift = None

    def models():
        nonlocal noise, drift
        if noise is None:
            noise = build_pools(store, config)
            drift = estimate_for_league(store, config, league_key)
        return noise, drift

    live_week_no = ((payload or {}).get("live") or {}).get("week")
    for week in season_weeks(data.league):
        stored = store.read_games(league_key, season, week) or {"league_key": league_key, "season": season, "week": week, "log": {}, "forecast": None, "record": None}
        before = copy.deepcopy(stored)
        if week > as_of and str(week) in forecasts:
            forecast = forecasts[str(week)]
            stored["forecast"] = {"as_of_week": as_of, "generated_at": payload.get("generated_at"), "live": (payload.get("live") or {}).get("week") == week, **forecast}
            projections = store.read_projections(season, week)
            scoring = resolve_settings(config, league_key, data.league, week)
            for game in forecast["games"]:
                entries = stored["log"].setdefault(game["key"], [])
                entry = build_entry(game, entries, rosters, projections, scoring, schedule, week, crosswalk, now)
                if not entries or not same_entry(entries[-1], entry):
                    entries.append(entry)
            if week == live_week_no and data.matchups.get(week):
                nz, dr = models()
                stored["baseline"] = live_baseline(store, config, league_key, data, week, stored["log"], nz, dr)
                live_wpa(stored["forecast"], stored["baseline"], nz)
        elif week <= as_of and (stored.get("record") is None or force_records) and data.matchups.get(week):
            if any(stored["log"].values()):
                nz, dr = models()
                stored["record"] = record_from_log(store, config, league_key, data, week, stored["log"], nz, dr)
            else:
                stored["record"] = record_from_pre_week(store, league_key, data, week)
        if week <= as_of and stored.get("record") and any("wpa" not in t for g in stored["record"]["games"] for t in g["teams"]):
            nz, _ = models()
            scoring = resolve_settings(config, league_key, data.league, week)
            record_wpa(stored["record"], data, week, store.read_projections(season, week), scoring, crosswalk, nz)
        if stored != before:
            store.write_games(league_key, season, week, stored)
            written.append(week)
    return written
