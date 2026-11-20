"""Fixture week with one Games page card in every state (docs/games-page-states.md).

Built from a real finished week of the exported site data (so cards keep real names, lineups and
win probability added), then edited per state and served with ``page.route`` in place of the real
week. The layout tests and the gallery script (tools/games_states_gallery.py) both use it.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

from ffapp.card_states import DOC_NAMES, GAMES_OVER, STATES, impact_ranked
from ffapp.games_export import key_players

ROOT = Path(__file__).resolve().parents[2]
LEAGUE = "dynasty"
TEMPLATE_WEEK = 10          # a finished week: both views, statuses and win probability added
FIXTURE_WEEK = 11
KICKOFF = "2026-11-22T18:00:00+00:00"

# what each state must look like on the page (the CARD_LOOK table in site/games.js)
EXPECT = {
    "projected": dict(badge=False, chips=[], lineup="key", toggle=False, check=False),
    "scheduled": dict(badge=False, chips=[], lineup="key", toggle=False, check=False),
    "not_started": dict(badge=False, chips=[], lineup="key", toggle=False, check=False),
    "scoring": dict(badge=True, chips=[], lineup="full", toggle=True, check=False),
    "bench_only": dict(badge=False, chips=["Bench playing"], lineup="full", toggle=True, check=False),
    "paused": dict(badge=False, chips=[], lineup="full", toggle=True, check=False),
    "paused_no_points": dict(badge=False, chips=[], lineup="key", toggle=True, check=False),
    "starters_done": dict(badge=False, chips=["Unofficial", "Bench to play"], lineup="impact", toggle=True, check=True),
    "starters_done_bench_playing": dict(badge=False, chips=["Unofficial", "Bench playing"], lineup="impact", toggle=True, check=True),
    "all_done": dict(badge=False, chips=["Unofficial"], lineup="impact", toggle=True, check=True),
    "final": dict(badge=False, chips=[], lineup="impact", toggle=True, check=True),
}


def template() -> dict:
    return json.loads((ROOT / "site" / "data" / LEAGUE / "games" / f"week_{TEMPLATE_WEEK:02d}.json").read_text(encoding="utf-8"))


def _rows(team: dict) -> list[dict]:
    return team["lineup"] + team["key_players"]


def _upcoming(team: dict) -> None:
    for r in _rows(team):
        r.update(status=None, points=None, clock=None, wpa=None, kickoff=KICKOFF if r.get("player_id") else None)
        r.pop("benched", None)
    team.update(points_so_far=None, to_play=None, actual=None, lineup_choices=None)


def _in_play(team: dict, played: int, playing: int) -> None:
    """The first ``played`` starters final, the next ``playing`` in progress, the rest still to play."""
    for i, r in enumerate(team["lineup"]):
        if i < played:
            r.update(status="final", clock=None, kickoff=None)
        elif i < played + playing:
            r.update(status="in_progress", clock="Q2 7:41", kickoff=None, points=round(float(r.get("points") or 0) / 2, 2))
        else:
            r.update(status=None, points=None, clock=None, wpa=None, kickoff=KICKOFF if r.get("player_id") else None)
    by_slot = {(r["slot"], r.get("player_id")): r for r in team["lineup"]}
    for k in team["key_players"]:   # key rows mirror their lineup rows
        twin = next((r for (slot, pid), r in by_slot.items() if pid and pid == k.get("player_id")), None)
        if twin:
            k.update({f: twin[f] for f in ("status", "points", "clock", "kickoff", "wpa")})
    team["points_so_far"] = round(sum(float(r["points"] or 0) for r in team["lineup"] if r["status"]), 2)
    team["to_play"] = sum(1 for r in team["lineup"] if not r["status"])
    team["actual"] = None


def _over(team: dict) -> None:
    team["points_so_far"] = team.get("actual")
    team["to_play"] = 0
    team["actual"] = None


def projection_keys(lineup: list[dict]) -> list[dict]:
    """The exporter's key-player rule (QB, top RB, top WR, top RB/WR/TE by projection) on display rows."""
    raw = [[r["slot"], r.get("player_id"), r["position"], float(r.get("projected") or 0)] for r in lineup]
    picked = key_players(raw)
    return [copy.deepcopy(lineup[next(i for i, x in enumerate(raw) if x is p)]) for p in picked]


def _card(base: dict, state: str) -> dict:
    g = copy.deepcopy(base)
    g["state"] = state
    g["winner"] = g["winner"] if state == "final" else None
    g["leader"] = None
    views = g["views"]
    for name, v in views.items():
        for t in v["teams"]:
            if state in ("projected", "scheduled", "not_started", "paused_no_points"):
                _upcoming(t)
            elif state == "scoring":
                _in_play(t, played=2, playing=1)
            elif state in ("bench_only", "paused"):
                _in_play(t, played=3, playing=0)
            elif state in GAMES_OVER:
                _over(t)
            if state in (*GAMES_OVER, "final"):
                t["key_players"] = impact_ranked([r for r in t["lineup"] if r.get("player_id")]) if name == "actual" else []
            elif EXPECT[state]["lineup"] == "key":
                t["key_players"] = projection_keys(t["lineup"])
    if state != "final":   # only past weeks before the projection log have a rebuilt Actual view
        for name, v in views.items():
            v["source"] = "log" if name == "actual" else "forecast"
    if state in ("projected", "scheduled", "not_started"):
        g["views"] = {"model": views["model"]}
        g["default_view"] = "model"
    if state == "projected":
        g.update(projected=True, frequency=0.42, bracket="winners", round=1, seeds=[1, 4])
    if state in GAMES_OVER:
        a, b = g["views"]["actual"]["teams"]
        if (a["points_so_far"] or 0) != (b["points_so_far"] or 0):
            g["leader"] = a["roster_id"] if (a["points_so_far"] or 0) > (b["points_so_far"] or 0) else b["roster_id"]
    g["teams"] = g["views"][g["default_view"]]["teams"]
    g["hist"] = g["views"][g["default_view"]]["hist"]
    g["key"] = f"{g['key']}-{state}"
    return g


def fixture_week() -> dict:
    """A current, live week whose cards are one per state, in ``STATES`` order."""
    W = template()
    games = W["games"]
    out = copy.deepcopy(W)
    out.update(week=FIXTURE_WEEK, label=f"Week {FIXTURE_WEEK}", kind="current", live=True, playoffs=False, byes=[], source="forecast",
               games=[_card(games[i % len(games)], s) for i, s in enumerate(STATES)])
    return out


def fixture_index(season: str) -> dict:
    return {"season": season, "current": FIXTURE_WEEK, "weeks": [{"week": FIXTURE_WEEK, "label": f"Week {FIXTURE_WEEK}", "kind": "current", "file": f"week_{FIXTURE_WEEK:02d}.json"}]}


def install(page) -> dict:
    """Serve the fixture week in place of the league's games data; returns the fixture."""
    week = fixture_week()
    index = fixture_index(week["season"])
    page.route(f"**/data/{LEAGUE}/games/index.json", lambda route: route.fulfill(status=200, json=index))
    page.route(f"**/data/{LEAGUE}/games/week_{FIXTURE_WEEK:02d}.json", lambda route: route.fulfill(status=200, json=week))
    return week


def open_states(page) -> dict:
    """Install the fixture on an open page and reload so the Games page shows it."""
    week = install(page)
    page.reload()
    page.wait_for_load_state("networkidle")
    page.wait_for_selector(f".game-card[data-state='{STATES[-1]}']", timeout=15000)
    page.wait_for_timeout(300)
    return week


__all__ = ["DOC_NAMES", "EXPECT", "LEAGUE", "STATES", "fixture_week", "install", "open_states"]
