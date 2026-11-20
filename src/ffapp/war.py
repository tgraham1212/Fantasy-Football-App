"""Wins Above Replacement per player and league-season.

Each regular-season week a consensus lineup is drawn from the ESPN start-percentage
snapshot: the most-started players with a game that week fill each position's slots,
then the most-started remaining RB/WR/TE fill the flex. The three most-started
players past each position's cut are the week's replacement players. Over the season
those lineups give a slot mean and variance per position; the opponent is a normal
distribution with the summed means and variances. A player's week is their actual
points in a lineup whose other slots sit at the slot means, so their win probability
is Phi((score - slot mean) / spread). WAR accumulates only over the weeks a player was
active: expected wins is the sum of his weekly win probabilities over those weeks, and WAR
subtracts what a player scoring the replacement level would earn in the same weeks, so a bye or
a week he was ruled out adds nothing. (This equals the earlier definition, which scored missed
weeks at the replacement level and so gave each of them exactly zero.)

A season uses the weekly cut when every scored week has a weekly snapshot, the yearly cut
(every week from the season snapshot) when none has, and the merged cut when some have: those
weeks use their own snapshot and the rest rank by a merged start percentage (see
``merged_start_percentages`` and the README's "Current-season start percentages").
Output: ``data/war/<league>/<season>.json``.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from ffapp.config import Config
from ffapp.espn import FANTASY_POSITIONS, match, teams_from_stats
from ffapp.injuries import OUT_STATUSES, statuses_for_week
from ffapp.league import FLEX_ELIGIBLE, resolve_settings, starter_slots
from ffapp.odds import regular_season_range
from ffapp.stats import actual_points, played
from ffapp.store import SeasonData, Store, read_json, write_json

log = logging.getLogger(__name__)

REPLACEMENT_COUNT = 3
STAT_KEYS = {
    "QB": ("pass_yd", "pass_td", "pass_int", "rush_yd", "rush_td"),
    "RB": ("rush_yd", "rush_td", "rec", "rec_yd", "rec_td"),
    "WR": ("rec", "rec_yd", "rec_td", "rush_yd"),
    "TE": ("rec", "rec_yd", "rec_td", "rush_yd"),
    "K": ("fgm", "fga", "xpm"),
    "DEF": ("sack", "int", "fum_rec", "def_td", "pts_allow"),
}
PER_GAME_KEYS = {"pts_allow"}


def normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


# -- lineup and cut -------------------------------------------------------------------------


@dataclass
class Lineup:
    starters: dict[str, list[str]]  # position -> Sleeper ids in the position's slots
    flex: list[str]
    replacement: dict[str, list[str]]  # position -> replacement player ids


def team_count(league: dict) -> int:
    return int(league.get("settings", {}).get("num_teams") or 12)


def slot_counts(league: dict) -> tuple[dict[str, int], dict[str, int]]:
    """League-wide slot counts (per-team slots times teams) for the lineup positions and for each flex kind."""
    teams = team_count(league)
    positions: dict[str, int] = {}
    flex: dict[str, int] = {}
    for slot in starter_slots(league):
        if slot in FANTASY_POSITIONS:
            positions[slot] = positions.get(slot, 0) + teams
        elif slot in FLEX_ELIGIBLE:
            flex[slot] = flex.get(slot, 0) + teams
    return positions, flex


def consensus_lineup(ranked: dict[str, list[str]], positions: dict[str, int], flex: dict[str, int], available, started: dict[str, float]) -> Lineup:
    """``ranked``: position -> Sleeper ids, most-started first; ``started``: id -> percent started.
    Only ids passing ``available`` are placed. Flex takes the most-started leftovers across its positions."""
    starters: dict[str, list[str]] = {}
    remaining: dict[str, list[str]] = {}
    for pos, count in positions.items():
        pool = [pid for pid in ranked.get(pos, []) if available(pid)]
        starters[pos] = pool[:count]
        remaining[pos] = pool[count:]
    flex_ids: list[str] = []
    taken: set[str] = set()
    for slot, count in flex.items():
        # a flex-eligible position with no slots of its own feeds the flex with its whole available pool
        for pos in FLEX_ELIGIBLE[slot]:
            if pos not in remaining:
                remaining[pos] = [pid for pid in ranked.get(pos, []) if available(pid)]
        candidates = [pid for pos in FLEX_ELIGIBLE[slot] for pid in remaining.get(pos, []) if pid not in taken]
        candidates.sort(key=lambda pid: (-started.get(pid, 0.0), pid))
        chosen = candidates[:count]
        flex_ids.extend(chosen)
        taken.update(chosen)
    replacement = {pos: [pid for pid in remaining[pos] if pid not in taken][:REPLACEMENT_COUNT] for pos in positions}
    return Lineup(starters=starters, flex=flex_ids, replacement=replacement)


def ranked_by_started(snapshot: dict, mapping: dict[str, str]) -> tuple[dict[str, list[str]], dict[str, float]]:
    """Position -> mapped Sleeper ids, most-started first (ties by ESPN id for determinism), plus id -> percent started."""
    rows = sorted(
        ((rec["started"], espn_id, rec["position"]) for espn_id, rec in (snapshot.get("players") or {}).items() if espn_id in mapping),
        key=lambda r: (-r[0], r[1]),
    )
    ranked: dict[str, list[str]] = {}
    started: dict[str, float] = {}
    for pct, espn_id, pos in rows:
        sid = mapping[espn_id]
        if sid in started:
            continue
        started[sid] = float(pct)
        ranked.setdefault(pos, []).append(sid)
    return ranked, started


# -- season constants ---------------------------------------------------------------------------


@dataclass
class WeekRecord:
    week: int
    slot_scores: dict[str, list[float]]  # position (or flex slot name) -> every starter's score
    replacement_scores: dict[str, float]  # position -> mean of the replacement players' scores


@dataclass
class Constants:
    slot_mean: dict[str, float]
    slot_var: dict[str, float]
    opponent_mean: float
    opponent_sd: float
    replacement: dict[str, float]


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _variance(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = _mean(values)
    return sum((v - m) ** 2 for v in values) / (len(values) - 1)


def season_constants(records: list[WeekRecord], positions: dict[str, int], flex: dict[str, int], teams: int) -> Constants:
    """Pooled slot means and variances over the season; opponent mean and spread weighted by slots per team."""
    pooled: dict[str, list[float]] = {}
    for rec in records:
        for slot, scores in rec.slot_scores.items():
            pooled.setdefault(slot, []).extend(scores)
    teams_per_slot = {**positions, **flex}
    slot_mean = {slot: _mean(pooled.get(slot, [])) for slot in teams_per_slot}
    slot_var = {slot: _variance(pooled.get(slot, [])) for slot in teams_per_slot}
    weights = {slot: count / teams for slot, count in teams_per_slot.items()}
    opponent_mean = sum(slot_mean[s] * weights[s] for s in teams_per_slot)
    opponent_sd = math.sqrt(sum(slot_var[s] * weights[s] for s in teams_per_slot))
    replacement = {pos: _mean([rec.replacement_scores[pos] for rec in records if pos in rec.replacement_scores]) for pos in positions}
    return Constants(slot_mean=slot_mean, slot_var=slot_var, opponent_mean=opponent_mean, opponent_sd=opponent_sd, replacement=replacement)


# -- players --------------------------------------------------------------------------------


def win_probability(score: float, slot_mean: float, spread: float) -> float:
    if spread <= 0:
        return 1.0 if score > slot_mean else 0.5 if score == slot_mean else 0.0
    return normal_cdf((score - slot_mean) / spread)


def player_weeks(scores: dict[int, float | None], weeks: list[int], position: str, constants: Constants) -> tuple[list[dict], float, int]:
    """Per week: the actual score and its win probability for weeks played; weeks not played are kept
    (``played`` False, no score or probability) for the walkthrough but add nothing. Returns the rows,
    the expected wins over active weeks and the number of active weeks."""
    rows = []
    total = 0.0
    active = 0
    for week in weeks:
        actual = scores.get(week)
        if actual is None:
            rows.append({"week": week, "score": None, "played": False, "p": None})
            continue
        p = win_probability(actual, constants.slot_mean[position], constants.opponent_sd)
        total += p
        active += 1
        rows.append({"week": week, "score": round(actual, 2), "played": True, "p": round(p, 4)})
    return rows, total, active


def baseline_wins(position: str, weeks: int, constants: Constants) -> float:
    return weeks * win_probability(constants.replacement[position], constants.slot_mean[position], constants.opponent_sd)


def stat_totals(position: str, lines: list[dict], games: int) -> dict[str, float]:
    totals: dict[str, float] = {}
    for key in STAT_KEYS.get(position, ()):
        value = sum(float((line.get("stats") or {}).get(key) or 0.0) for line in lines)
        if key in PER_GAME_KEYS:
            value = value / games if games else 0.0
        totals[key] = round(value, 1)
    return totals


def holders_by_week(data: SeasonData, weeks: list[int]) -> dict[str, list[tuple[int, str]]]:
    """player id -> [(week, owner user id)] for every scored week a roster held them."""
    owner = {int(r["roster_id"]): str(r.get("owner_id") or "") for r in data.rosters}
    held: dict[str, list[tuple[int, str]]] = {}
    for week in weeks:
        for team in data.matchups.get(week, []):
            uid = owner.get(int(team["roster_id"]), "")
            for pid in team.get("players") or []:
                held.setdefault(str(pid), []).append((week, uid))
    return held


def owner_attribution(pid: str, held: dict[str, list[tuple[int, str]]], current: dict[str, str] | None) -> tuple[str | None, list[str]]:
    """(owner, holders): the end-of-season or current holder, and every distinct manager who held the player."""
    history = held.get(pid, [])
    holders: list[str] = []
    for _, uid in history:
        if uid and uid not in holders:
            holders.append(uid)
    if current is not None:
        owner = current.get(pid)
        if owner and owner not in holders:
            holders.append(owner)
    else:
        owner = history[-1][1] if history else None
    return (owner or None), holders


# -- the run -----------------------------------------------------------------------------------


def cut_mode(store: Store, season: str, weeks: list[int]) -> str:
    """weekly: every scored week has its own snapshot; yearly: none has; merged: some have."""
    stored = set(store.espn_weeks(season))
    captured = [w for w in weeks if w in stored]
    if weeks and len(captured) == len(weeks):
        return "weekly"
    return "merged" if captured else "yearly"


# Statuses that keep a player out (the shared list in injuries.py); only such players may fall
# back to ownership (see below).
UNAVAILABLE_STATUSES = frozenset(OUT_STATUSES)


# Why a merged start percentage (README, Player WAR -> "Current-season start percentages"):
#
# While a season is in progress, ESPN's public feed reports its season-level start percentage
# as the CURRENT WEEK's figure, so data/espn/<season>/season.json is one week's view, rewritten
# by every in-season run (in 2026 it matched week_11.json for every player). Ranking every
# week by that view treats anyone on a bye or hurt in the snapshot week as a bench player for
# the whole season (Josh Jacobs in week 11: owned 91.5%, started 8.6%); the consensus starter
# cut slides deeper and the replacement players become real backups (2026 RB replacement level
# 5.0 against 8-11 in every completed season).
#
# So for weeks without their own snapshot, a player's figure is the HIGHEST percent started
# across his trusted weekly snapshots. Byes and injuries only ever LOWER a start percentage:
# - a snapshot of a scored week is trusted only if he played that week;
# - a snapshot of a week not yet scored (the current week) is always trusted: a low figure there
#   cannot win the maximum, and a player whose team had a bye in the only scored captured week
#   gets his real figure from it.
# A player never seen active in a scored captured week AND carrying an out status (the shared list:
# Out, Doubtful, IR, PUP, Sus, NA, DNR) takes the higher of that figure and his percent OWNED: ownership barely moves
# through an IR stint, so it stands in for how often he was started while healthy. Healthy
# players never use it: a backup's ownership far exceeds his start rate (owned 50%, started 15%),
# and giving it to everyone not seen active lifted week-10-bye backups into the replacement zone
# (2026 WR 6.5, RB 6.4 under that earlier rule; 15.6 QB / 9.6 RB / 8.8 WR with this one).
# Past seasons were captured after they ended (their season snapshot is the real season-long
# figure) and keep the yearly cut; fully captured seasons (2027 on) use the weekly cut.
def merged_start_percentages(
    store: Store,
    season: str,
    weeks: list[int],
    stats: dict[int, dict],
    season_snapshot: dict,
    crosswalk: dict,
    teams: dict,
) -> tuple[dict, dict[str, str]]:
    """A synthetic snapshot (ESPN id -> started, position) and its mapping, for ranked_by_started."""
    snapshot_weeks = sorted(store.espn_weeks(season))
    weekly: dict[int, tuple[dict, dict[str, str]]] = {}
    for w in snapshot_weeks:
        snap = store.read_espn_week(season, w) or {}
        mapping, _ = match(snap.get("players") or {}, crosswalk, teams)
        weekly[w] = (snap.get("players") or {}, mapping)
    season_players = season_snapshot.get("players") or {}
    season_mapping, _ = match(season_players, crosswalk, teams)
    statuses = statuses_for_week(store, season, 99) or {}  # the latest saved statuses of the season

    best: dict[str, float] = {}  # Sleeper id -> highest percent started in a trusted snapshot
    active: set[str] = set()  # played in a scored week that has a snapshot
    for w in snapshot_weeks:
        players, mapping = weekly[w]
        rows = stats.get(w) or {}
        for espn_id, rec in players.items():
            sid = mapping.get(espn_id)
            if not sid:
                continue
            if w in weeks:  # a scored week: trusted only if he played
                if not played(rows.get(sid) or {}):
                    continue
                active.add(sid)
            best[sid] = max(best.get(sid, float("-inf")), float(rec.get("started") or 0.0))

    owned: dict[str, float] = {}  # latest weekly snapshot holding the player, else the season snapshot
    sources = [weekly[w] for w in reversed(snapshot_weeks)] + [(season_players, season_mapping)]
    for players, mapping in sources:
        for espn_id, rec in players.items():
            sid = mapping.get(espn_id)
            if sid and sid not in owned:
                owned[sid] = float(rec.get("owned") or 0.0)

    merged: dict[str, dict] = {}
    merged_mapping: dict[str, str] = {}
    for players, mapping in sources:
        for espn_id, rec in players.items():
            sid = mapping.get(espn_id)
            if not sid or espn_id in merged:
                continue
            pct = best.get(sid, 0.0)
            if sid not in active and statuses.get(sid) in UNAVAILABLE_STATUSES:
                pct = max(pct, owned.get(sid, 0.0))
            merged[espn_id] = {"started": pct, "position": rec["position"]}
            merged_mapping[espn_id] = sid
    return {"players": merged}, merged_mapping


def scored_weeks(store: Store, data: SeasonData) -> list[int]:
    """Regular-season weeks up to the last scored leg that have stat lines stored."""
    completed = int(data.league.get("settings", {}).get("last_scored_leg") or 0)
    stats_weeks = set(store.stats_weeks(data.season))
    return [w for w in regular_season_range(data.league) if w <= completed and w in stats_weeks]


def build_war(store: Store, config: Config, league_key: str, season: str) -> dict:
    data = store.read_season(league_key, season)
    weeks = scored_weeks(store, data)
    positions, flex = slot_counts(data.league)
    crosswalk = store.read_crosswalk() or {}
    season_snapshot = store.read_espn_season(season)
    if season_snapshot is None:
        raise FileNotFoundError(f"{league_key} {season}: no ESPN season snapshot, run `ffapp snapshot` first")
    mode = cut_mode(store, season, weeks)
    teams = teams_from_stats(store, season)
    season_mapping, _ = match(season_snapshot.get("players") or {}, crosswalk, teams)
    season_ranked, season_started = ranked_by_started(season_snapshot, season_mapping)

    stats = {w: store.read_stats(season, w) for w in weeks}
    if mode == "merged":
        merged, merged_mapping = merged_start_percentages(store, season, weeks, stats, season_snapshot, crosswalk, teams)
        season_ranked, season_started = ranked_by_started(merged, merged_mapping)
    own_weeks = set(store.espn_weeks(season)) if mode != "yearly" else set()
    records: list[WeekRecord] = []
    for week in weeks:
        if week in own_weeks:
            snapshot = store.read_espn_week(season, week) or season_snapshot
            mapping, _ = match(snapshot.get("players") or {}, crosswalk, teams)
            ranked, started = ranked_by_started(snapshot, mapping)
        else:
            ranked, started = season_ranked, season_started
        scoring = resolve_settings(config, league_key, data.league, week)
        rows = stats[week]
        lineup = consensus_lineup(ranked, positions, flex, lambda pid, rows=rows: played(rows.get(pid) or {}), started)
        points = {pid: actual_points(rows.get(pid), scoring) for pos in positions for pid in lineup.starters[pos]}
        points.update({pid: actual_points(rows.get(pid), scoring) for pid in lineup.flex})
        slot_scores = {pos: [points[pid] for pid in lineup.starters[pos]] for pos in positions}
        for slot in flex:
            slot_scores[slot] = [points[pid] for pid in lineup.flex]
        replacement_scores = {}
        for pos in positions:
            ids = lineup.replacement[pos]
            if ids:
                replacement_scores[pos] = _mean([actual_points(rows.get(pid), scoring) for pid in ids])
        records.append(WeekRecord(week=week, slot_scores=slot_scores, replacement_scores=replacement_scores))
    constants = season_constants(records, positions, flex, team_count(data.league))

    held = holders_by_week(data, weeks)
    in_progress = data.status != "complete"
    current = None
    if in_progress:
        current = {}
        for roster in data.rosters:
            uid = str(roster.get("owner_id") or "")
            for key in ("players", "reserve", "taxi"):
                for pid in roster.get(key) or []:
                    current[str(pid)] = uid
    players: dict[str, dict] = {}
    seen: dict[str, dict[int, dict]] = {}
    for week in weeks:
        for pid, rec in stats[week].items():
            if played(rec):
                seen.setdefault(str(pid), {})[week] = rec
    for pid, lines in seen.items():
        last = lines[max(lines)]
        position = war_position(last)
        if position not in positions:
            continue
        scores = {w: actual_points(lines[w], resolve_settings(config, league_key, data.league, w)) for w in lines}
        weekly, exp_wins, active = player_weeks(scores, weeks, position, constants)
        baseline = baseline_wins(position, active, constants)
        owner, holders = owner_attribution(pid, held, current)
        name = f"{last.get('first_name') or ''} {last.get('last_name') or ''}".strip() or pid
        players[pid] = {
            "name": name,
            "position": position,
            "team": last.get("team"),
            "games": len(lines),
            "points": round(sum(scores.values()), 2),
            "stats": stat_totals(position, list(lines.values()), len(lines)),
            "weekly": weekly,
            "exp_wins": round(exp_wins, 4),
            "war": round(exp_wins - baseline, 4),
            "owner": owner,
            "holders": holders,
        }
    _, unmatched = match(season_snapshot.get("players") or {}, crosswalk, teams)
    return {
        "league_key": league_key,
        "season": season,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "cut": mode,
        "through_week": weeks[-1] if weeks else 0,
        "weeks": weeks,
        "constants": {
            "slot_mean": {k: round(v, 4) for k, v in constants.slot_mean.items()},
            "slot_var": {k: round(v, 4) for k, v in constants.slot_var.items()},
            "opponent_mean": round(constants.opponent_mean, 4),
            "opponent_sd": round(constants.opponent_sd, 4),
        },
        "replacement": {
            pos: {"level": round(constants.replacement[pos], 4), "baseline_wins": round(baseline_wins(pos, len(weeks), constants), 4)}
            for pos in positions
        },
        "players": dict(sorted(players.items(), key=lambda kv: (-kv[1]["war"], kv[0]))),
        "unmatched": [{"name": u.name, "position": u.position, "started": u.started} for u in unmatched],
    }


def war_position(line: dict) -> str | None:
    """The lineup position a stat line plays at: its position, else its first lineup-eligible fantasy position."""
    pos = line.get("position")
    if pos in FANTASY_POSITIONS:
        return pos
    for alt in line.get("fantasy_positions") or []:
        if alt in FANTASY_POSITIONS:
            return alt
    return None


# -- files -------------------------------------------------------------------------------------


def war_path(store: Store, league_key: str, season: str) -> Path:
    return store.root / "war" / league_key / f"{season}.json"


@dataclass
class WarReport:
    written: list[Path] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def write_war(store: Store, config: Config, league_key: str) -> WarReport:
    report = WarReport()
    for season in store.seasons(league_key):
        try:
            payload = build_war(store, config, league_key, season)
        except FileNotFoundError as exc:
            report.skipped.append(str(exc))
            log.warning("%s", exc)
            continue
        path = war_path(store, league_key, season)
        write_json(path, payload)
        report.written.append(path)
        log.info("war %s %s: %s cut through week %s, %d players", league_key, season, payload["cut"], payload["through_week"], len(payload["players"]))
    return report


def read_war(store: Store, league_key: str, season: str) -> dict | None:
    path = war_path(store, league_key, season)
    return read_json(path) if path.exists() else None


def war_seasons(store: Store, league_key: str) -> list[str]:
    base = store.root / "war" / league_key
    if not base.exists():
        return []
    return sorted(p.stem for p in base.iterdir() if p.suffix == ".json")
