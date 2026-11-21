"""Weekly injury statuses and who is expected not to play.

Each snapshot run saves, for Sleeper's current NFL week, every fantasy-position player
with an injury status set (``data/injuries/<season>/week_NN.json``, ``{player_id:
status}``), overwriting that week until it rolls over. For a week without a saved file,
a rostered player is inferred out when he had no projection or a projection of 0 while
his NFL team played.
"""

from __future__ import annotations

import logging

from ffapp.espn import FANTASY_POSITIONS
from ffapp.schedule import Schedule
from ffapp.store import Store

log = logging.getLogger(__name__)

SAVE_SEASON_TYPES = ("regular", "post")
# The one list of Sleeper statuses that keep a player out, with the label shown for each. Used by
# the Games cards' not-playing list, the WAR ownership fallback and the Positions page. Doubtful
# counts as out: such players almost never play. Statuses not listed (Questionable) do not.
OUT_STATUSES = {
    "Out": "Out",
    "Doubtful": "Doubtful",
    "IR": "IR",
    "PUP": "PUP",
    "Sus": "Suspended",
    "NA": "Not active",
    "DNR": "Did not report",
}


def statuses_from_players(payload: dict) -> dict[str, str]:
    """``{player_id: injury_status}`` for fantasy-position players whose status is set."""
    out = {}
    for pid, rec in (payload or {}).items():
        if isinstance(rec, dict) and rec.get("position") in FANTASY_POSITIONS and rec.get("injury_status"):
            out[str(pid)] = str(rec["injury_status"])
    return dict(sorted(out.items()))


def save_injuries(store: Store, state: dict, players_payload: dict) -> tuple[str, int] | None:
    """Save the current week's statuses; returns (season, week) written, or None outside the season."""
    if state.get("season_type") not in SAVE_SEASON_TYPES or not state.get("week"):
        return None
    season, week = str(state.get("season")), int(state["week"])
    store.write_injuries(season, week, statuses_from_players(players_payload))
    log.info("injuries %s week %d saved", season, week)
    return season, week


DETAIL_FIELDS = {  # Sleeper player-list field -> saved name
    "injury_body_part": "body_part",
    "practice_participation": "practice",
    "depth_chart_order": "depth",
    "depth_chart_position": "depth_pos",
}


def details_from_players(payload: dict, rostered: set[str]) -> dict[str, dict]:
    """``{player_id: {body_part, practice, depth, depth_pos}}`` for rostered fantasy-position players,
    keeping only the fields that are set; players with none set are left out."""
    out: dict[str, dict] = {}
    for pid, rec in (payload or {}).items():
        if str(pid) not in rostered or not isinstance(rec, dict) or rec.get("position") not in FANTASY_POSITIONS:
            continue
        fields = {name: rec[key] for key, name in DETAIL_FIELDS.items() if rec.get(key) not in (None, "")}
        if fields:
            out[str(pid)] = fields
    return dict(sorted(out.items()))


def rostered_players(store: Store, leagues) -> set[str]:
    """Every player on a current-season roster (starters, bench, IR, taxi) in the configured leagues."""
    out: set[str] = set()
    for key in leagues:
        seasons = store.seasons(key)
        if not seasons:
            continue
        for roster in store.read_rosters(key, seasons[-1]):
            for field_name in ("players", "reserve", "taxi"):
                out.update(str(p) for p in roster.get(field_name) or [])
    return out


def save_player_details(store: Store, state: dict, players_payload: dict, rostered: set[str]) -> tuple[str, int] | None:
    """Save the current week's body part, practice participation and depth chart for rostered players
    (the last save of the week wins); returns (season, week) written, or None outside the season."""
    if state.get("season_type") not in SAVE_SEASON_TYPES or not state.get("week"):
        return None
    season, week = str(state.get("season")), int(state["week"])
    store.write_player_details(season, week, details_from_players(players_payload, rostered))
    log.info("player details %s week %d saved", season, week)
    return season, week


def save_trending(store: Store, client, state: dict, now) -> Path:
    """Save Sleeper's trending adds with the time saved (one file per day; a later refresh that day
    replaces it); returns the path written."""
    from ffapp.store import write_if_changed

    adds = client.trending_adds()
    season = str(state.get("season") or now.year)
    path = store.trending_path(season, now.strftime("%Y-%m-%d"))
    write_if_changed(path, {"saved_at": now.isoformat(timespec="seconds"), "adds": adds}, ("saved_at",))  # unchanged adds: no new record
    return path


def statuses_for_week(store: Store, season: str, week: int) -> dict[str, str] | None:
    """The week's saved statuses; for a week after the latest save, the latest save (today's news is
    the best guess for upcoming weeks); None for weeks before saving began."""
    saved = store.read_injuries(season, week)
    if saved is not None:
        return saved
    base = store.root / "injuries" / str(season)
    weeks = sorted(int(p.stem.split("_")[1]) for p in base.glob("week_*.json")) if base.exists() else []
    earlier = [w for w in weeks if w < week]
    return store.read_injuries(season, earlier[-1]) if earlier else None


def projected_value(record: dict | None, scoring: dict[str, float]) -> float | None:
    from ffapp.scoring import record_points

    return None if record is None else record_points(record, scoring)


def not_playing(
    store: Store,
    season: str,
    week: int,
    roster: list[str],
    projections: dict[str, dict],
    scoring: dict[str, float],
    teams: dict[str, str],
) -> list[dict]:
    """Rostered players expected not to play in ``week``: ``[{player_id, reason}]``.

    ``teams`` maps player id to NFL team for players without a projection that week.
    Order of precedence: bye, then the saved status, then (weeks without a saved file) inferred out.
    """
    schedule = Schedule(store, season)
    saved = statuses_for_week(store, season, week)
    out = []
    for pid in roster:
        record = projections.get(pid)
        nfl_team = (record or {}).get("team") or teams.get(pid)
        defense = (record or {}).get("position") == "DEF" or schedule.is_team(week, pid)
        if defense:
            nfl_team = nfl_team or pid  # defenses are keyed by team
        bye = schedule.on_bye(week, nfl_team)
        if bye:
            out.append({"player_id": pid, "reason": "Bye"})
            continue
        if saved is not None:
            reason = OUT_STATUSES.get(saved.get(pid, ""))
            if reason:
                out.append({"player_id": pid, "reason": reason})
            continue
        projected = projected_value(record, scoring)
        if not defense and bye is False and (projected is None or projected <= 0):  # a defense always plays
            out.append({"player_id": pid, "reason": "Inferred out"})
    return out
