"""The state of one Games page card (docs/games-page-states.md; Calculations.txt section 22).

A state describes both fantasy teams together, from the managers' real starters and bench (never the
Model lineup), using each player's NFL game state as the site saw it at the last refresh:

- ``none``: no game this week (bye) or an empty starter slot: finished from the start;
- ``scheduled``: his game has not kicked off (a ruled-out player too, until his game ends);
- ``in_progress``: his game is being played;
- ``final``: his game is over (ESPN reports a cancelled game as over: finished with 0).

The 11 states, with their names in the documentation:

    projected (F1)  scheduled (F2)  not_started (C)
    scoring (L1)    bench_only (L2)
    paused (P1)     paused_no_points (P2)
    starters_done (O1)  starters_done_bench_playing (O2)  all_done (O3)
    final (PW)
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

STATES = ("projected", "scheduled", "not_started", "scoring", "bench_only", "paused", "paused_no_points",
          "starters_done", "starters_done_bench_playing", "all_done", "final")
DOC_NAMES = {"projected": "F1", "scheduled": "F2", "not_started": "C", "scoring": "L1", "bench_only": "L2", "paused": "P1",
             "paused_no_points": "P2", "starters_done": "O1", "starters_done_bench_playing": "O2", "all_done": "O3", "final": "PW"}
GAMES_OVER = ("starters_done", "starters_done_bench_playing", "all_done")
FINISHED = ("none", "final")


def card_state(week_kind: str, projected: bool, teams: Sequence[dict]) -> str:
    """One of ``STATES``. ``week_kind`` is the exporter's ``final`` / ``current`` / ``upcoming``;
    ``teams`` holds each team's ``starters`` and ``bench`` as player game states."""
    if week_kind == "final":
        return "final"          # Sleeper has scored the week
    if week_kind != "current":
        return "projected" if projected else "scheduled"
    starters = [s for t in teams for s in t.get("starters", ())]
    bench = [s for t in teams for s in t.get("bench", ())]
    if not _any(starters + bench, ("in_progress", "final")):
        return "not_started"
    if _any(starters, ("in_progress",)):
        return "scoring"
    if all(s in FINISHED for s in starters):
        if _any(bench, ("in_progress",)):
            return "starters_done_bench_playing"
        if _any(bench, ("scheduled",)):
            return "starters_done"
        return "all_done"
    # starters still to play, none playing now
    if _any(bench, ("in_progress",)):
        return "bench_only"
    return "paused" if _any(starters, ("final",)) else "paused_no_points"


def _any(states: Iterable[str], wanted: tuple[str, ...]) -> bool:
    return any(s in wanted for s in states)


POSITION_ORDER = {"QB": 0, "RB": 1, "WR": 2, "TE": 3, "DEF": 4, "K": 5}


def impact_ranked(rows: list[dict], n: int = 4) -> list[dict]:
    """The ``n`` starters with the largest win probability added either way, largest first; ties on the
    whole percentage shown are broken by position (QB, RB, WR, TE, DEF, K)."""
    def key(r: dict) -> tuple:
        return (-abs(round((r.get("wpa") or 0.0) * 100)), POSITION_ORDER.get(r.get("position") or "", 9))
    return sorted(rows, key=key)[:n]
