"""The week in progress: who holds each lineup slot once games start, and how they score.

The live week is the first week after the as-of point once any of its NFL games has kicked
off. In it, a starting slot whose player has kicked off holds the player the manager started
there (Sleeper's lineup for the week), scoring his points so far plus his projection times the
share of his game left; a final game leaves no share. The other slots are filled with the
model's best lineup from rostered players who have not kicked off, with the replacement floor.
A player who kicked off on the bench is not used. The game card's Actual view instead keeps the
manager's own starters in the open slots (``set_starters_lineup``): no model picks, no free agents.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ffapp.lineup import Starter
from ffapp.schedule import Schedule, share_left
from ffapp.scoring import record_points
from ffapp.store import SeasonData, Store

EMPTY = ("0", "", "None")


@dataclass(frozen=True)
class LiveContext:
    week: int
    at: datetime


def live_week(store: Store, data: SeasonData, as_of: int, now: datetime) -> int | None:
    """``as_of + 1`` when one of its NFL games has kicked off by ``now``, else None."""
    week = as_of + 1
    schedule = Schedule(store, data.season)
    games = (schedule.week(week) or {}).get("games") or []
    return week if any(schedule.kicked_off(week, g["home"], now) for g in games) else None


def games_progress(store: Store, season: str, week: int) -> tuple[int, int]:
    games = (Schedule(store, season).week(week) or {}).get("games") or []
    return sum(1 for g in games if g["state"] == "final"), len(games)


def player_team(pid: str, record: dict | None, crosswalk: dict[str, dict]) -> str | None:
    if record and record.get("team"):
        return str(record["team"])
    team = (crosswalk.get(pid) or {}).get("team")
    if team:
        return str(team)
    return pid if pid.isalpha() and pid.isupper() else None  # defenses are keyed by team


def clock_label(game: dict | None) -> str | None:
    if not game or game.get("state") != "in_progress":
        return None
    quarter, clock = game.get("quarter"), game.get("clock")
    if quarter is None or clock is None:
        return "In progress"
    label = f"Q{quarter}" if quarter <= 4 else "OT"
    minutes, seconds = divmod(int(round(float(clock))), 60)
    return f"{label} {minutes}:{seconds:02d}"


def live_lineup(
    row: dict,
    slots: list[str],
    roster: list[str],
    projections: dict[str, dict],
    scoring: dict[str, float],
    schedule: Schedule,
    week: int,
    now: datetime,
    crosswalk: dict[str, dict],
    open_lineup,
) -> list[Starter]:
    """The team's live-week lineup in slot order.

    ``open_lineup(open_slots, players)`` returns the model's lineup for the slots still open,
    in ``open_slots`` order (the caller passes the projection-and-floor lineup builder). With
    ``open_lineup=None`` the open slots keep the manager's own starters (see ``set_starters_lineup``).
    """
    starters = [str(p) for p in (row.get("starters") or [])]
    points = {str(k): float(v or 0.0) for k, v in (row.get("players_points") or {}).items()}
    kicked = {}
    for pid in set(roster) | set(starters):
        if pid in EMPTY:
            continue
        team = player_team(pid, projections.get(pid), crosswalk)
        if team and schedule.kicked_off(week, team, now):
            kicked[pid] = schedule.game_for(week, team)
    locked: dict[int, Starter] = {}
    for i, slot in enumerate(slots):
        pid = starters[i] if i < len(starters) else "0"
        if pid in EMPTY or pid not in kicked:
            continue
        game = kicked[pid]
        record = projections.get(pid)
        position = (record or {}).get("position") or (crosswalk.get(pid) or {}).get("position") or slot
        share = share_left(game)
        status = "final" if share == 0.0 and (game or {}).get("state") != "in_progress" else "in_progress"
        projected = record_points(record, scoring) if record else 0.0
        locked[i] = Starter(slot, pid, position, projected, fixed=points.get(pid, 0.0), share=share, status=status, clock=clock_label(game))
    if open_lineup is None:
        return [locked[i] if i in locked else _set_starter(slot, starters[i] if i < len(starters) else "0", projections, scoring, crosswalk)
                for i, slot in enumerate(slots)]
    taken = {s.player_id for s in locked.values()}
    available = [pid for pid in roster if pid not in kicked and pid not in taken]
    open_slots = [slot for i, slot in enumerate(slots) if i not in locked]
    picked = list(open_lineup(open_slots, available)) if open_slots else []
    lineup = []
    for i, slot in enumerate(slots):
        if i in locked:
            lineup.append(locked[i])
        else:
            j = next((k for k, s in enumerate(picked) if s.slot == slot), None)
            if j is not None:
                lineup.append(picked.pop(j))
    return lineup


def _set_starter(slot: str, pid: str, projections: dict[str, dict], scoring: dict[str, float], crosswalk: dict[str, dict]) -> Starter:
    """A starter the manager set who has not kicked off, at his latest projection; an empty slot is
    ``FA:`` with 0.0 (it scores nothing, and is shown as empty, not as a free agent)."""
    if pid in EMPTY:
        return Starter(slot, "FA:", slot, 0.0)
    record = projections.get(pid)
    position = (record or {}).get("position") or (crosswalk.get(pid) or {}).get("position") or slot
    return Starter(slot, pid, position, record_points(record, scoring) if record else 0.0)


def set_starters_lineup(
    row: dict,
    slots: list[str],
    projections: dict[str, dict],
    scoring: dict[str, float],
    schedule: Schedule,
    week: int,
    now: datetime,
    crosswalk: dict[str, dict],
) -> list[Starter]:
    """The live-week lineup the manager set: locked starters at their results, the others at their latest
    projections, an empty slot scoring 0 (game-predictions 2.7.3)."""
    roster = [str(p) for p in (row.get("players") or [])]
    return live_lineup(row, slots, roster, projections, scoring, schedule, week, now, crosswalk, None)
