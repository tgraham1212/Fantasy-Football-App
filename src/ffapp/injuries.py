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
# Sleeper status -> the reason shown on a card (statuses not listed here do not keep a player out)
NOT_PLAYING = {"Out": "Out", "Doubtful": "Doubtful", "IR": "IR", "PUP": "Out", "Sus": "Out"}


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
            reason = NOT_PLAYING.get(saved.get(pid, ""))
            if reason:
                out.append({"player_id": pid, "reason": reason})
            continue
        projected = projected_value(record, scoring)
        if not defense and bye is False and (projected is None or projected <= 0):  # a defense always plays
            out.append({"player_id": pid, "reason": "Inferred out"})
    return out
