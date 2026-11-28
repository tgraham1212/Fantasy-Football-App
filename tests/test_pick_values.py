"""Rookie pick values (rookie-pick-values): history records and WAR, the rookie order, the model, unused
picks, the record and the export. Real-data tests read the committed records under data/."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from ffapp.config import load_config
from ffapp.espn import match
from ffapp.mizelle import dlf_order, display_name, mfl_to_sleeper, player_arr
from ffapp.pick_values import (
    GROUPS, HISTORY_SEASONS, HistoryStore, build_model, class_orders, forecast_thirds, group_key, group_of,
    history_war, keep_stat_keys, last_finished_season, league_order, model_path, non_increasing, pick_rows,
    pick_value, pick_values_export, read_model, read_rookie_order, rookie_order_path, slim_record, war_by_season,
)
from ffapp.stats import actual_points, played
from ffapp.store import Store, write_json

DATA = Store("data")
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def config():
    return load_config("config/leagues.yaml")


def history_copy(tmp_path: Path, season: str = "2023") -> Store:
    """A base store holding the dynasty settings, the crosswalk and one league season copied in as history."""
    (tmp_path / "leagues/dynasty/2026").mkdir(parents=True)
    shutil.copy("data/leagues/dynasty/2026/league.json", tmp_path / "leagues/dynasty/2026/league.json")
    (tmp_path / "espn").mkdir()
    shutil.copy("data/espn/crosswalk.json", tmp_path / "espn/crosswalk.json")
    for w in range(1, 15):
        dst = tmp_path / f"history/stats/{season}/week_{w:02d}.json"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(f"data/stats/{season}/week_{w:02d}.json", dst)
    (tmp_path / f"history/espn/{season}").mkdir(parents=True)
    shutil.copy(f"data/espn/{season}/season.json", tmp_path / f"history/espn/{season}/season.json")
    return Store(tmp_path)


# -- 4.12.2 history records and WAR --------------------------------------------------------------------


def test_history_records_apart():
    """History seasons live under data/history/ and never appear in the league store's season walks."""
    hs = HistoryStore(DATA)
    assert hs.root == DATA.root / "history"
    for season in HISTORY_SEASONS:
        assert len(hs.stats_weeks(season)) == 14, season
        assert hs.read_espn_season(season) is not None, season
    stats_seasons = {p.name for p in (DATA.root / "stats").iterdir()}
    assert not stats_seasons & {s for s in HISTORY_SEASONS if s < "2021"}
    assert DATA.stats_weeks("2015") == [] and DATA.read_espn_season("2015") is None


def test_slim_record_keeps_points_and_played():
    league = DATA.read_league("dynasty", "2023")
    keep = keep_stat_keys(league)
    scoring = {k: float(v) for k, v in league["scoring_settings"].items()}
    rows = DATA.read_stats("2023", 3)
    for pid, rec in rows.items():
        slim = slim_record(rec, keep)
        assert actual_points(slim, scoring) == pytest.approx(actual_points(rec, scoring)), pid
        assert played(slim) == played(rec)
        assert slim["position"] == rec["position"]


def test_history_matching_fallback(tmp_path):
    """A retired Player missing from the crosswalk is matched by name and position among the season's lines."""
    (tmp_path / "leagues/dynasty/2026").mkdir(parents=True)
    shutil.copy("data/leagues/dynasty/2026/league.json", tmp_path / "leagues/dynasty/2026/league.json")
    write_json(tmp_path / "espn/crosswalk.json", {"1": {"espn_id": "11", "name": "Current Player", "position": "WR", "team": "KC"}})
    write_json(tmp_path / "history/stats/2013/week_01.json",
               {"777": {"player_id": "777", "first_name": "Tony", "last_name": "Gonzalez", "position": "TE", "team": "ATL", "stats": {"pts_half_ppr": 9.0}}})
    hs = HistoryStore(Store(tmp_path))
    assert "777" not in (hs.read_crosswalk() or {})  # no active season: the base crosswalk only
    hs.active_season = "2013"
    mapping, unmatched = match({"9": {"name": "Tony Gonzalez", "position": "TE", "team": "ATL", "started": 89.2}}, hs.read_crosswalk(), {})
    assert mapping == {"9": "777"} and unmatched == []


def test_history_war_matches_stored_war(tmp_path, config):
    """4.12.2: the history path run on a 2023 copy gives the league's 2023 WAR to 0.0001."""
    from ffapp.war import build_war

    hist = history_war(history_copy(tmp_path), config, "2023")
    real = build_war(DATA, config, "dynasty", "2023")
    assert hist["cut"] == "yearly" and set(hist["players"]) == set(real["players"])
    assert max(abs(hist["players"][p]["war"] - real["players"][p]["war"]) for p in real["players"]) <= 1e-4


def test_commands_not_in_cold_runs():
    """4.12.1.2: the fetches and the model build are run by hand, never by a cold or hot run or the build."""
    from ffapp.cli import BUILD_STEPS, REFRESH_STEPS

    names = {n for n, _ in REFRESH_STEPS} | {n for n, _ in BUILD_STEPS}
    assert not names & {"history-fetch", "rookie-adp-fetch", "pick-values"}
    for wf in ("refresh.yml", "hot.yml"):
        text = (ROOT / ".github/workflows" / wf).read_text(encoding="utf-8")
        assert "history-fetch" not in text and "rookie-adp-fetch" not in text and "pick-values" not in text, wf


# -- 4.12.1 rookie order ----------------------------------------------------------------------------


PAGE = """<html><script>
const playerArr = [
 {"id": "100", "name": "Back, Early", "status": "R", "position": "RB",
  "stats": {"feb": {"picks": [1, 1]}, "may": {"picks": [30, 34]}, "jun": {"picks": [32]}}},
 {"id": "101", "name": "Wideout, Late", "status": "R", "position": "WR",
  "stats": {"feb": {"picks": [50]}, "jul": {"picks": [18, 19]}}},
 {"id": "102", "name": "Veteran, Old", "position": "WR", "stats": {"may": {"picks": [2]}}},
 {"id": "103", "name": "Kicker, Rookie", "status": "R", "position": "PK", "stats": {"may": {"picks": [5]}}},
 {"id": "104", "name": "Tight, \\"Quote\\" End", "status": "R", "position": "TE", "stats": {"aug": {"picks": [18.5]}}}
];
</script></html>"""


def test_player_arr_parser():
    players = player_arr(PAGE)
    assert [p["id"] for p in players] == ["100", "101", "102", "103", "104"]
    assert player_arr(PAGE.replace("const playerArr", "var playerArr"))[0]["id"] == "100"
    assert display_name("Elliott, Ezekiel") == "Ezekiel Elliott"


def test_dlf_rookie_order():
    """4.12.1.1: rookies only, QB/RB/WR/TE, ranked by mean May-August pick; February picks ignored."""
    order = dlf_order(player_arr(PAGE), {"100": "s100", "101": "s101"})
    assert [(s["slot"], s["mfl_id"]) for s in order] == [(1, "101"), (2, "104"), (3, "100")]
    assert order[0]["mean_pick"] == 18.5 and order[0]["sleeper_id"] == "s101"
    assert order[1]["sleeper_id"] is None  # unmapped rookie keeps his slot
    assert mfl_to_sleeper("mfl_id,sleeper_id\n1,10\nNA,11\n2,NA\n") == {"1": "10"}


def test_rookie_order_sources():
    """4.12.1: DLF for 2013-2021, this league's drafts from 2022 (2022: startup rookies in pick order)."""
    orders = class_orders(DATA)
    assert {s for s, o in orders.items() if o["source"] == "dlf"} == set(HISTORY_SEASONS)
    assert all(o["source"] == "league" for s, o in orders.items() if s >= "2022")
    first = league_order(DATA, "2022")[:2]
    assert [s["name"] for s in first] == ["Breece Hall", "Drake London"] and [s["slot"] for s in first] == [1, 2]


def test_rookie_order_record():
    """4.12.1.3: the record holds every 2013-2021 class, and the model rebuilds from committed records alone."""
    record = read_rookie_order(DATA)
    assert set(record["classes"]) == set(HISTORY_SEASONS)
    assert all(len(slots) == 36 for slots in record["classes"].values())
    assert {(f["class"], f["name"]) for f in record["flagged"]} == {("2013", "Johnathan Franklin"), ("2013", "Marcus Lattimore"), ("2014", "Colt Lyerla")}
    assert record["classes"]["2016"][0]["name"] == "Ezekiel Elliott"


def test_third_party_cache_not_committed():
    """4.12.1.2: the local cache is gitignored and nothing under it is tracked."""
    assert ".cache/" in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    tracked = subprocess.run(["git", "ls-files", ".cache"], cwd=ROOT, capture_output=True, text=True).stdout
    assert tracked.strip() == ""


# -- 4.12.3 model -------------------------------------------------------------------------------------


def test_pick_groups():
    """4.12.3.1: Early 1-4, Middle 5-8, Late 9-12 of each round."""
    assert group_of(1) == (1, "Early") and group_of(4) == (1, "Early") and group_of(5) == (1, "Middle")
    assert group_of(12) == (1, "Late") and group_of(18) == (2, "Middle") and group_of(36) == (3, "Late")
    assert len(GROUPS) == 9


def test_eight_season_value():
    """4.12.3: per-season means over the picks that reached the season; a season without games counts 0."""
    orders = {"2020": {"source": "dlf", "slots": [{"slot": 1, "sleeper_id": "a"}]},
              "2024": {"source": "league", "slots": [{"slot": 2, "sleeper_id": "b"}]}}
    war = {"2020": {"a": 1.0}, "2021": {}, "2022": {"a": 2.0}, "2024": {"b": 3.0}, "2025": {"b": -1.0}}
    rows = pick_rows(orders, war, "2025")
    assert rows[0]["war"] == [1.0, 0.0, 2.0, 0.0, 0.0, 0.0] and rows[1]["war"] == [3.0, -1.0]
    model = build_model(orders, war, "2025", draws=50)
    early = model["groups"][group_key(1, "Early")]
    # season 1: mean(1, 3) = 2; season 2: mean(0, -1) = -0.5; seasons 3-6: a alone
    assert early["measured"] == pytest.approx(2.0 - 0.5 + 2.0)
    assert [s["picks"] for s in early["seasons"]] == [2, 2, 1, 1, 1, 1]


def test_values_never_rise():
    """4.12.3.2: pool adjacent violators; the measured round 2 becomes -0.75 throughout."""
    out = non_increasing([3.38, 1.45, 0.11, -1.13, -0.46, -0.66, -1.03, -1.64, -0.47])
    assert out[:3] == [3.38, 1.45, 0.11]
    assert out[3:6] == pytest.approx([-0.75] * 3)
    assert all(a >= b - 1e-12 for a, b in zip(out, out[1:]))


def test_model_values(config):
    """4.12: the committed model gives 1st Early +3.38, and a rebuild from committed records reproduces it."""
    model = read_model(DATA)
    assert model is not None and round(model["groups"]["1-Early"]["value"], 2) == 3.38
    through = last_finished_season(DATA)
    assert model["through_season"] == through
    rebuilt = build_model(class_orders(DATA), war_by_season(DATA, config, through), through)
    for key, g in model["groups"].items():
        assert rebuilt["groups"][key]["value"] == pytest.approx(g["value"], abs=1e-4), key
    assert sum(c["picks"] for c in model["classes"].values()) == 465


def test_model_record_not_rewritten(tmp_path):
    """4.12.5: the export only reads the model; no build or refresh step writes it."""
    from ffapp.cli import BUILD_STEPS, REFRESH_STEPS

    before = model_path(DATA).read_bytes()
    pick_values_export(DATA)
    assert model_path(DATA).read_bytes() == before
    assert "pick-values" not in {n for n, _ in BUILD_STEPS + REFRESH_STEPS}


# -- 4.12.4 unused picks ---------------------------------------------------------------------------------


def test_unused_pick_value():
    """4.12.4: two drafts away a pick takes its round's average value; without a model the value is None."""
    model = read_model(DATA)
    far = pick_value(DATA, model, "2028", 1, 4)
    assert far["basis"] == "round_average" and far["value"] == pytest.approx(model["rounds"]["1"]["average_value"])
    assert round(far["value"], 2) == 1.65
    assert pick_value(DATA, None, "2028", 1, 4)["value"] is None
    used = pick_value(DATA, model, "2025", 1, 2)  # the 2025 order is set: roster 2 had slot 1
    assert used["basis"] == "slot" and used["group"] == "1-Early"


def test_next_draft_from_forecast():
    """4.12.4.1: the team with the best projected finish holds a Late pick in the next draft."""
    model = read_model(DATA)
    thirds = forecast_thirds(DATA)
    assert sorted(thirds.values()).count("Late") == 4 and len(thirds) == 12
    best = next(rid for rid, t in thirds.items() if t == "Late")
    value = pick_value(DATA, model, "2027", 1, best, thirds=thirds)
    assert value["basis"] == "forecast" and value["group"] == "1-Late" and round(value["value"], 2) == 0.11


# -- 4.12.6 export ------------------------------------------------------------------------------------


def test_export_writes_pick_values_file(tmp_path):
    """4.12.6: the export writes site/data/pick-values.json from the record; no record, no file."""
    payload = pick_values_export(DATA)
    assert set(payload["groups"]) == {group_key(r, t) for r, t in GROUPS}
    assert all({"value", "measured", "range", "picks", "seasons"} <= set(g) for g in payload["groups"].values())
    assert len(payload["slots"]) == 36 and payload["sources"]
    assert pick_values_export(Store(tmp_path)) is None
