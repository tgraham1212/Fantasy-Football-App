"""Positional rankings: rosters, points per game, flags, replacement levels and the shared axis."""

from __future__ import annotations

import pytest

from ffapp.positions import axis_ranges, build_positions, positions_export
from ffapp.store import SeasonData, write_json
from tests.test_war import synthetic_store, tiny_config


def in_progress_store(tmp_path):
    """The WAR test league, reshaped: regular season weeks 1-4, weeks 1-2 final, weeks 3-4 projected."""
    store = synthetic_store(tmp_path, status="in_season")
    data = store.read_season("tiny", "2025")
    league = {**data.league, "roster_positions": ["QB", "RB", "WR", "FLEX", "BN", "BN"],
              "settings": {**data.league["settings"], "playoff_week_start": 5, "last_scored_leg": 2}}
    rosters = [
        {"roster_id": 1, "owner_id": "A", "players": ["q1", "r1", "r3", "w2", "r9", "z0", "k1"], "reserve": [], "taxi": ["r9"]},
        {"roster_id": 2, "owner_id": "B", "players": ["q2", "r2", "w1", "w3"], "reserve": ["w3"], "taxi": []},
    ]
    store.write_season("tiny", SeasonData(league=league, users=data.users, rosters=rosters, matchups=data.matchups))

    def proj(first, pos, team, **stats):
        return {"first_name": first, "last_name": "Test", "position": pos, "team": team, "stats": stats}

    week3 = {"w1": proj("W1", "WR", "DAL", rec_yd=140), "r9": proj("R9", "RB", "ATL", rush_yd=60), "z0": proj("Z0", "RB", "NYG"),
             "k1": proj("K1", "K", "BAL", fgm=2), "q1": proj("Q1", "QB", "BUF", pass_yd=250)}
    week4 = {"w1": proj("W1", "WR", "DAL"), "r9": proj("R9", "RB", "ATL", rush_yd=60), "z0": proj("Z0", "RB", "NYG")}
    store.write_projections("2025", 3, week3)
    store.write_projections("2025", 4, week4)
    store.write_injuries("2025", 2, {"w2": "Out", "q1": "Questionable"})
    return store


def players_of(payload):
    return {p["id"]: p for team in payload["teams"] for p in team["players"]}


def test_points_per_game_blends_actual_and_projected(tmp_path):
    payload = build_positions(in_progress_store(tmp_path), tiny_config(), "tiny", "2025")
    assert payload["weeks"] == [1, 2, 3, 4] and payload["final_through"] == 2 and payload["status"] == "in_progress"
    players = players_of(payload)
    # w1: 12 points in each final week, projected 14 in week 3 and 0 (bye) in week 4
    assert players["w1"]["ppg"] == pytest.approx(round((12 + 12 + 14) / 3, 2))
    assert (players["w1"]["games"], players["w1"]["projected"]) == (2, 1)
    # r9 has not played: two projected weeks of 6 points
    assert players["r9"]["ppg"] == 6.0 and (players["r9"]["games"], players["r9"]["projected"]) == (0, 2)
    # nothing scored and nothing projected: left out; the league has no K slot: left out
    assert "z0" not in players and "k1" not in players


def test_roster_flags_and_owners(tmp_path):
    payload = build_positions(in_progress_store(tmp_path), tiny_config(), "tiny", "2025")
    players = players_of(payload)
    assert players["r9"]["taxi"] and not players["w1"]["taxi"]
    assert players["w3"]["reserve"]
    assert players["w2"]["injured"] and not players["q1"]["injured"]  # Out yes, Questionable no
    team = payload["teams"][0]
    assert (team["roster_id"], team["owner_id"], team["display_name"]) == (1, "A", "Alice")
    assert list(payload["positions"]) == ["QB", "RB", "WR"]


def test_completed_season_uses_actual_points_and_no_injury_flags(tmp_path):
    store = synthetic_store(tmp_path)  # complete, regular season weeks 1-2, both final
    store.write_injuries("2025", 2, {"w2": "Out"})
    payload = build_positions(store, tiny_config(), "tiny", "2025")
    players = players_of(payload)
    assert payload["status"] == "complete"
    assert all(p["projected"] == 0 for p in players.values())
    assert players["w1"]["ppg"] == 12.0
    assert not any(p["injured"] for p in players.values())


def test_replacement_level_from_war_or_none(tmp_path):
    store = synthetic_store(tmp_path)
    assert build_positions(store, tiny_config(), "tiny", "2025")["positions"]["RB"]["replacement"] is None
    write_json(store.root / "war" / "tiny" / "2025.json", {"replacement": {"RB": {"level": 7.9412, "baseline_wins": 5.0}}})
    payload = build_positions(store, tiny_config(), "tiny", "2025")
    assert payload["positions"]["RB"]["replacement"] == 7.94 and payload["positions"]["QB"]["replacement"] is None


def test_axis_is_shared_across_seasons_and_ignores_outliers():
    def season(values, replacement):
        return {"positions": {"K": {"replacement": replacement}},
                "teams": [{"players": [{"position": "K", "ppg": v} for v in values]}]}

    typical = [6.0 + (i % 80) / 10 for i in range(400)]  # 6.0 to 13.9
    ranges = axis_ranges([season(typical, 8.6), season(typical[:200] + [31.0], 9.4)])
    assert ranges["K"] == [0.0, 15.0]  # the one-game 31 does not stretch it


def test_export_payload_has_axis_in_every_season_and_an_index(tmp_path):
    store = in_progress_store(tmp_path)
    out = positions_export(store, tiny_config(), "tiny")
    assert out["index"]["current"] == "2025" and out["index"]["seasons"][0]["final_through"] == 2
    assert all("axis" in info for info in out["files"]["2025"]["positions"].values())
