"""Slate forecasts: the league forecast as each slate of the live week went final.

A slate is the set of NFL games that kick off at the same time. The first cold run that simulates
after every game of a slate is final stores the live forecast in
``data/odds/<league>/<season>/slates_NN.json``, keyed by the slate's kickoff time; an entry is
never overwritten. A slate that kicked off more than 8 hours before the run is not stored (it went
final long ago, so today's forecast would not be its own). Runs that skip the simulation (Live
mode) store nothing, since their stored forecast is not current. See docs/refresh-modes.md and Calculations.txt, section 10.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from ffapp.odds import current_season
from ffapp.schedule import parse_iso
from ffapp.store import Store


def final_slates(nfl_week: dict | None) -> list[str]:
    """Kickoff times (ISO) of the week's slates whose games are all final."""
    slates: dict[str, list[str]] = defaultdict(list)
    for game in (nfl_week or {}).get("games") or []:
        slates[game["kickoff_utc"]].append(game.get("state") or "scheduled")
    return sorted(k for k, states in slates.items() if states and all(s == "final" for s in states))


RECENT = timedelta(hours=8)


def capture_slates(store: Store, league_key: str, now: datetime | None = None) -> list[str]:
    """Store the live forecast for every newly final slate of the live week; returns their keys."""
    now = now or datetime.now(timezone.utc)
    season = current_season(store, league_key)
    live = store.read_live(league_key, season) if season else None
    week = ((live or {}).get("live") or {}).get("week")
    if not week:
        return []
    stored = store.read_slates(league_key, season, week)
    new = [k for k in final_slates(store.read_nfl_week(season, week)) if k not in stored and now - parse_iso(k) <= RECENT]
    if not new:
        return []
    entry = {
        "generated_at": live.get("generated_at"),
        "live": live.get("live"),
        "teams": live.get("teams"),
        "games": (live.get("games") or {}).get(str(week)),
    }
    for key in new:
        stored[key] = entry
    store.write_slates(league_key, season, week, stored)
    return new
