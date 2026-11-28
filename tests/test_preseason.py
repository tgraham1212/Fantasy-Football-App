"""The preseason Forecast (league-preseason): values, sources, matching, rosters, absences, Wins Saved,
grades, the record and the export."""
from __future__ import annotations

import json
import zlib

import numpy as np
import pytest

from ffapp.noise import GaussianNoise
from ffapp.preseason import (
    ABSENCE, Lineups, espn_lines, grade, line_value, match_lines, norm_name, pool_levels, preseason_rosters,
    preseason_values, read_record, record_path,
)
from ffapp.store import Store, write_json

HALF_PPR = {"pass_yd": 0.04, "pass_td": 4, "pass_int": -2, "rush_yd": 0.1, "rush_td": 6, "rec": 0.5, "rec_yd": 0.1, "rec_td": 6, "fum_lost": -2,
            "xpm": 1, "fgm": 3}


def espn_player(name, pos_id, team_id, stats, season=2024):
    return {"player": {"fullName": name, "defaultPositionId": pos_id, "proTeamId": team_id,
                       "stats": [{"seasonId": season, "statSourceId": 1, "statSplitTypeId": 0, "stats": stats, "appliedTotal": 0}]}}


# -- 1.5.1 values -------------------------------------------------------------------------------------


def test_preseason_value_from_stat_line():
    """1.5.1: the season line scored with the league's scoring / 17; 0 in the bye week."""
    line = espn_lines([espn_player("Christian McCaffrey", 2, 25, {"24": 1218, "25": 12, "53": 67, "42": 527, "43": 4})], "2024")[0]
    assert line_value(line, "RB", HALF_PPR) == pytest.approx(304.0 / 17, abs=0.001)
    # the bye week scores nothing: a lone RB is out in his bye and replacement level plays
    squad_values = {"rb": 17.88}
    players = {"rb": {"position": "RB", "team": "SF"}}
    lineups = Lineups([1], {1: ["rb"]}, players, squad_values, ["RB"], {"RB": 5.0}, {"SF": {9}}, GaussianNoise(sd=0.0), 2000)
    rng = np.random.default_rng(1)
    assert lineups(9, rng)[:, 0].max() == pytest.approx(5.0)
    assert lineups(8, rng)[:, 0].max() == pytest.approx(17.88)


class FakeClient:
    def __init__(self, season_rows=None):
        self.season_rows = season_rows or []

    def season_projections(self, season):
        return self.season_rows


def test_projection_sources(tmp_path):
    """1.5.1.1: 2023 uses Sleeper's season projections, else the week-1 Projection; kickers use week 1."""
    store = Store(tmp_path)
    write_json(store.projections_path("2023", 1), {"9": {"position": "WR", "stats": {"rec": 6, "rec_yd": 82}},
                                                   "50": {"position": "K", "stats": {"xpm": 3, "fgm": 2}}})
    rows = [{"player_id": "8", "player": {"position": "RB"}, "stats": {"rush_yd": 1020, "rush_td": 8}}]
    players = {"8": {"position": "RB"}, "9": {"position": "WR"}, "50": {"position": "K"}, "77": {"position": "TE"}}
    v = preseason_values(store, FakeClient(rows), {"scoring_settings": HALF_PPR}, "2023", players)
    assert v.per_game["8"] == pytest.approx((102 + 48) / 17, abs=0.001) and v.source["8"] == "sleeper"
    assert v.per_game["9"] == pytest.approx(11.2) and v.source["9"] == "week1"
    assert v.per_game["50"] == pytest.approx(9.0) and v.source["50"] == "week1"
    assert v.unmatched == ["77"]


def test_espn_matching():
    """1.5.1.2: normalised names (suffixes dropped) and position; defences by team."""
    assert norm_name("Kenneth Walker III") == norm_name("Kenneth Walker") == "kenneth walker"
    assert norm_name("Amon-Ra St. Brown") == "amon ra st brown"
    lines = espn_lines([espn_player("Kenneth Walker III", 2, 26, {"24": 900}), espn_player("49ers D/ST", 16, 25, {"99": 40})], "2024")
    lines[1]["applied"] = 100.0
    matched = match_lines(lines, {"1": {"first": "Kenneth", "last": "Walker", "position": "RB", "team": "SEA"},
                                  "SF": {"first": "San Francisco", "last": "49ers", "position": "DEF", "team": "SF"}})
    assert matched["1"]["name"] == "Kenneth Walker III" and matched["SF"]["position"] == "DEF"


# -- 1.5.2 rosters ----------------------------------------------------------------------------------------


def test_preseason_rosters(seeded_store):
    """1.5.2: dynasty week-1 rosters without taxi Players."""
    data = seeded_store.read_season("dynasty", "2025")
    rosters, players = preseason_rosters(seeded_store, "dynasty", data)
    taxi = {str(p) for r in data.rosters for p in (r.get("taxi") or [])}
    week1 = {int(r["roster_id"]): [str(p) for p in r.get("players") or []] for r in data.matchups[1]}
    for rid, ids in rosters.items():
        assert set(ids) == set(week1.get(rid, [])) - taxi


def test_missing_kicker_scores_replacement_level():
    """1.5.2.1: no kicker on the roster: the kicker slot scores the preseason replacement level."""
    lineups = Lineups([1], {1: []}, {}, {}, ["K"], {"K": 9.5}, {}, GaussianNoise(sd=0.0), 500)
    assert lineups(1, np.random.default_rng(2))[:, 0] == pytest.approx(np.full(500, 9.5))
    assert pool_levels({"K": [10.0, 9.5, 9.0, 4.0]}) == {"K": 9.5}


# -- 1.5.3 absences --------------------------------------------------------------------------------------------


def test_absence_rates():
    """1.5.3: each position misses at its pooled rate."""
    assert ABSENCE == {"QB": 0.106, "RB": 0.119, "WR": 0.114, "TE": 0.102, "K": 0.044, "DEF": 0.0}
    players = {"rb": {"position": "RB", "team": "A"}}
    lineups = Lineups([1], {1: ["rb"]}, players, {"rb": 15.0}, ["RB"], {"RB": 0.0}, {}, GaussianNoise(sd=0.0), 100_000)
    out = lineups(1, np.random.default_rng(3))[:, 0]
    assert 0.116 <= (out == 0.0).mean() <= 0.122


def test_bench_fills_absent_starter():
    """1.5.3.1: the best healthy bench Player worth at least replacement level fills in."""
    players = {"rb1": {"position": "RB", "team": "A"}, "rb2": {"position": "RB", "team": "B"}, "rb3": {"position": "RB", "team": "C"}}
    values = {"rb1": 15.0, "rb2": 9.0, "rb3": 4.0}
    lineups = Lineups([1], {1: list(values)}, players, values, ["RB"], {"RB": 5.0}, {"A": {1}}, GaussianNoise(sd=0.0), 5000)
    out = lineups(1, np.random.default_rng(4))[:, 0]     # RB1 on bye: RB2 (9.0) plays, or replacement (5.0) when RB2 is hurt
    assert set(np.unique(out)) <= {9.0, 5.0} and (out == 9.0).mean() > 0.85
    assert not (out == 4.0).any(), "a bench Player worth less than replacement level never plays"


# -- 1.5.4 outcomes, Wins Saved; 1.5.5 grades --------------------------------------------------------------------


@pytest.fixture
def forecast(seeded_store, dynasty_config, monkeypatch):
    """A small preseason Forecast for the seeded dynasty 2025 season, values from a stub."""
    import ffapp.preseason as P

    def fake_values(store, client, league, season, players):
        vals = {pid: (12.0 + (zlib.crc32(pid.encode()) % 70) / 10 if p["position"] in ABSENCE else 0.0) for pid, p in players.items()}
        return P.Values(vals, {pid: "espn" for pid in vals}, [], {pos: 6.0 for pos in ABSENCE})

    monkeypatch.setattr(P, "preseason_values", fake_values)
    return P.make_forecast(seeded_store, None, dynasty_config, "dynasty", "2025", GaussianNoise(sd=8.0), runs=300)


def test_outcomes(forecast):
    """1.5.4: shares to 0.001 (title shares add to 1), record to 0.1, points per week to 0.1."""
    teams = forecast["teams"]
    assert abs(sum(t["title"] for t in teams) - 1.0) <= 0.01
    assert all(round(t["wins"], 1) == t["wins"] and round(t["ppg"], 1) == t["ppg"] for t in teams)
    assert [t["title"] for t in teams] == sorted((t["title"] for t in teams), reverse=True)


def test_wins_saved(forecast, seeded_store, dynasty_config, monkeypatch):
    """1.5.4.1: Wins Saved to 0.01; a team whose bench holds nobody worth a start saves nothing."""
    assert all(round(t["wins_saved"], 2) == t["wins_saved"] for t in forecast["teams"])
    import ffapp.preseason as P

    def flat(store, client, league, season, players):  # every bench Player below replacement level
        vals = {pid: 0.0 for pid in players}
        return P.Values(vals, {}, [], {pos: 6.0 for pos in ABSENCE})

    monkeypatch.setattr(P, "preseason_values", flat)
    rec = P.make_forecast(seeded_store, None, dynasty_config, "dynasty", "2025", GaussianNoise(sd=8.0), runs=200)
    assert all(t["wins_saved"] == 0.0 for t in rec["teams"])


def test_grade_letters():
    """1.5.5: A, then B, then F, then C, then D."""
    assert grade(0.297, 0.89, 0.004)[0] == "A"
    assert grade(0.12, 0.60, 0.05)[0] == "B" and grade(0.05, 0.70, 0.02)[0] == "B"
    assert grade(0.01, 0.20, 0.22) == "F"
    assert grade(0.05, 0.50, 0.08)[0] == "C" and grade(0.02, 0.20, 0.10)[0] == "D"


def test_plus_and_minus():
    """1.5.5.1: plus and minus near the edges of each band."""
    assert [grade(t, 0.9, 0) for t in (0.25, 0.20, 0.16)] == ["A+", "A", "A-"]
    assert grade(0.11, 0.5, 0.05) == "B+" and grade(0.05, 0.75, 0.02) == "B" and grade(0.05, 0.70, 0.02) == "B-"
    assert [grade(0.05, p, 0.05) for p in (0.60, 0.50, 0.40)] == ["C+", "C", "C-"]
    assert grade(0.02, 0.30, 0.155) == "D-" and grade(0.02, 0.30, 0.10) == "D+" and grade(0.02, 0.20, 0.10) == "D"


# -- 1.5, 1.5.6 to 1.5.8 record, timing and export --------------------------------------------------------------------


def test_preseason_forecast_made_once(seeded_store, dynasty_config, monkeypatch):
    """1.5: made once and kept byte for byte."""
    import ffapp.preseason as P

    calls = []
    monkeypatch.setattr(P, "make_forecast", lambda *a, **k: calls.append(a[4]) or {"teams": [], "season": a[4]})
    made, _ = P.make_due(seeded_store, None, dynasty_config, "dynasty", GaussianNoise())
    assert made and made == calls
    before = record_path(seeded_store, "dynasty", made[0]).read_bytes()
    again, _ = P.make_due(seeded_store, None, dynasty_config, "dynasty", GaussianNoise())
    assert again == [] and record_path(seeded_store, "dynasty", made[0]).read_bytes() == before


def test_made_after_the_draft(seeded_store, dynasty_config):
    """1.5.8: due only once the season's draft is complete and no record exists."""
    from ffapp.preseason import due_seasons

    due = due_seasons(seeded_store, "dynasty")
    assert "2026" in due
    draft = seeded_store.read_draft("dynasty", "2026")
    seeded_store.write_draft("dynasty", "2026", {**draft, "draft": {**draft["draft"], "status": "drafting"}})
    assert "2026" not in due_seasons(seeded_store, "dynasty")


def test_actual_finish(forecast, seeded_store, dynasty_config):
    """1.5.6: a finished season gives each team's final place."""
    from ffapp.preseason import preseason_export

    write_json(record_path(seeded_store, "dynasty", "2025"), forecast)
    out = preseason_export(seeded_store, dynasty_config, "dynasty")["seasons"]["2025"]
    places = sorted(t["finish"] for t in out["teams"])
    assert out["final"] and places == list(range(1, len(places) + 1))


def test_export_writes_preseason_file(forecast, seeded_store, dynasty_config, tmp_path):
    """1.5.7: one preseason file per league with every stored Forecast."""
    from ffapp.export import export_site
    from tests.test_export import simulate_weeks

    write_json(record_path(seeded_store, "dynasty", "2025"), forecast)
    simulate_weeks(seeded_store, dynasty_config, [0, 1])
    out = tmp_path / "site-data"
    export_site(seeded_store, dynasty_config, out)
    data = json.loads((out / "dynasty" / "preseason.json").read_text(encoding="utf-8"))
    assert "2025" in data["seasons"] and data["latest"] == "2025"
    assert {t["user"] for t in data["seasons"]["2025"]["teams"]} <= set(data["managers"])
    index = json.loads((out / "index.json").read_text(encoding="utf-8"))
    assert index["leagues"][0]["preseason"] == {"file": "dynasty/preseason.json"}
    assert read_record(seeded_store, "dynasty", "2025")["teams"]


def test_draft_strength_rank(tmp_path):
    """1.5.6.1: redraft teams ranked by preseason points per week, 1 for the highest, ties shared."""
    from ffapp.preseason import preseason_export
    from tests.test_draft import write_season, pick, full_stats

    store = Store(tmp_path / "data")
    picks = [pick(n, f"p{n}", roster=(n - 1) % 12 + 1) for n in range(1, 13)]
    write_season(store, "red", "2025", "redraft", picks, {}, stats=full_stats([p["player_id"] for p in picks]))
    teams = [{"roster_id": r, "ppg": 100.0 + r if r != 12 else 111.0, "title": 0.08, "playoffs": 0.5, "last": 0.08,
              "wins": 7.0, "losses": 7.0, "wins_saved": 0.1, "grade": "C"} for r in range(1, 13)]
    write_json(record_path(store, "red", "2025"), {"teams": teams, "made_at": "x"})
    out = {t["roster_id"]: t["draft_strength"] for t in preseason_export(store, None, "red")["seasons"]["2025"]["teams"]}
    assert out[11] == 1 and out[12] == 1, "111.0 ties: both 1st"
    assert out[10] == 3 and out[1] == 12


def test_season_under_way_uses_week_one(tmp_path):
    """1.5.1.1.1: a season under way takes every value from its week-1 Projections."""
    store = Store(tmp_path)
    write_json(store.projections_path("2026", 1), {"5": {"position": "WR", "stats": {"rec": 6, "rec_yd": 82}}})
    league = {"scoring_settings": HALF_PPR, "status": "in_season", "season": "2026",
              "settings": {"start_week": 1, "playoff_week_start": 15, "leg": 12, "last_scored_leg": 12}}
    import ffapp.preseason as P
    v = P.preseason_values(store, None, league, "2026", {"5": {"position": "WR"}, "6": {"position": "RB"}}) if P.under_way(league) else None
    assert v is not None and v.per_game == {"5": pytest.approx(11.2)} and v.source == {"5": "week1"} and v.unmatched == ["6"]
